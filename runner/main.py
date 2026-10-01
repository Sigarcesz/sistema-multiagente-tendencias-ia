"""Ejecuta el sistema multiagente con la API de OpenAI (Agents SDK).

Las skills (.claude/skills/*/SKILL.md), los prompts de los agentes (.claude/agents/*.md)
y los scripts de control son LOS MISMOS que usa la versión de Claude Code. Este archivo
solo cambia el motor: carga esos textos como instrucciones y da a cada agente las
herramientas de su rol.

Uso:
  python -m runner.main --run runs/v1-base_caso1
  python -m runner.main --prueba runs/v1-base_caso1_caso4
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

from agents import Agent, Runner, WebSearchTool, function_tool, set_tracing_disabled  # noqa: E402
from agents.exceptions import MaxTurnsExceeded  # noqa: E402

from runner.herramientas import (  # noqa: E402
    ejecutar_script_auditor, ejecutar_script_orquestador, escribir_archivo, leer_archivo, web_fetch,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SOLICITUD = ("Elabora el informe ejecutivo 'Tendencias emergentes de inteligencia artificial con potencial "
             "impacto empresarial durante los próximos tres años' para Horizonte Digital S.A.S. El informe será "
             "utilizado por la alta dirección para decidir qué tendencias deben observarse, evaluarse o "
             "incorporarse a futuros proyectos.")

MODELO_BASE = os.getenv("MODELO", "gpt-5-mini")
MODELOS = {
    "orquestador": os.getenv("MODELO_ORQUESTADOR", MODELO_BASE),
    "trend-scout": os.getenv("MODELO_SCOUT", MODELO_BASE),
    "report-writer": os.getenv("MODELO_ESCRITOR", MODELO_BASE),
    "quality-auditor": os.getenv("MODELO_AUDITOR", MODELO_BASE),
}
MAX_TURNOS = {"orquestador": 150, "trend-scout": 80, "report-writer": 25, "quality-auditor": 100}

if os.getenv("DESACTIVAR_TRACING") == "1":
    set_tracing_disabled(True)

# Estado global de la corrida (uso de tokens y delegaciones)
ESTADO = {"run": None, "uso": {}, "inicio": None}


def cuerpo_md(path: Path) -> str:
    """Quita el frontmatter YAML de un .md."""
    texto = path.read_text(encoding="utf-8")
    return re.sub(r"^---\n.*?\n---\n", "", texto, count=1, flags=re.S).strip()


ADAPTADOR_ESPECIALISTA = """
---
## Entorno de ejecución (API de OpenAI)

Las instrucciones de arriba nombran herramientas de Claude Code. Aquí equivalen a:
- WebSearch → `web_search` · WebFetch → `web_fetch`
- Read → `leer_archivo` · Write → `escribir_archivo` (solo dentro de runs/)
- Bash o `python3 <script> <args>` → `ejecutar_script_auditor(script="<script>", argumentos=[...])`
Rutas siempre relativas a la raíz del repositorio. Si una herramienta no está en tu lista, no la tienes.
Escribe los archivos con la herramienta; no pegues su contenido completo en tu respuesta final.
"""

ADAPTADOR_ORQUESTADOR = """
---
## Entorno de ejecución (API de OpenAI)

- Delegar en `trend-scout` → herramienta `trend_scout(mensaje)`; en `report-writer` → `report_writer(mensaje)`;
  en `quality-auditor` → `quality_auditor(mensaje)`. Cada llamada es una delegación independiente:
  el agente no recuerda llamadas anteriores, así que el mensaje debe incluir modo, carpeta del run y rutas.
- Read → `leer_archivo`.
- Bash o `python3 <script> <args>` → `ejecutar_script_orquestador(script="<script>", argumentos=[...])`.
  La elección entre python3 y python la resuelve la herramienta.
- La carpeta del run y el modo vienen indicados en el mensaje del usuario; úsalos tal cual.
- Trabaja de forma autónoma hasta el final: no hay un usuario disponible para responder preguntas
  durante la corrida.
"""


def construir_especialista(nombre: str, herramientas: list) -> Agent:
    instrucciones = (cuerpo_md(RAIZ / ".claude/skills" / nombre / "SKILL.md") + "\n\n---\n\n"
                     + cuerpo_md(RAIZ / ".claude/agents" / f"{nombre}.md") + ADAPTADOR_ESPECIALISTA)
    return Agent(name=nombre, instructions=instrucciones, model=MODELOS[nombre], tools=herramientas)


ESPECIALISTAS = {
    "trend-scout": construir_especialista("trend-scout", [WebSearchTool(), web_fetch, leer_archivo, escribir_archivo]),
    "report-writer": construir_especialista("report-writer", [leer_archivo, escribir_archivo]),
    "quality-auditor": construir_especialista("quality-auditor",
                                              [leer_archivo, escribir_archivo, ejecutar_script_auditor, web_fetch]),
}


def registrar(nombre: str, mensaje: str, salida: str, uso, segundos: float, error: str | None = None):
    u = ESTADO["uso"].setdefault(nombre, {"modelo": MODELOS[nombre], "delegaciones": 0, "requests": 0,
                                          "input_tokens": 0, "output_tokens": 0, "segundos": 0.0})
    u["delegaciones"] += 1
    if uso is not None:
        u["requests"] += uso.requests
        u["input_tokens"] += uso.input_tokens
        u["output_tokens"] += uso.output_tokens
    u["segundos"] = round(u["segundos"] + segundos, 1)
    if ESTADO["run"]:
        Path(ESTADO["run"]).mkdir(parents=True, exist_ok=True)
        with open(Path(ESTADO["run"]) / "delegaciones.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "agente": nombre,
                                "mensaje": mensaje, "respuesta": salida[:4000], "error": error,
                                "segundos": round(segundos, 1)}, ensure_ascii=False) + "\n")


async def delegar(nombre: str, mensaje: str) -> str:
    print(f"  → {nombre} ({MODELOS[nombre]})…", flush=True)
    t0 = time.time()
    try:
        r = await Runner.run(ESPECIALISTAS[nombre], mensaje, max_turns=MAX_TURNOS[nombre])
        salida = str(r.final_output)
        registrar(nombre, mensaje, salida, r.context_wrapper.usage, time.time() - t0)
        print(f"  ← {nombre} terminó en {time.time() - t0:.0f}s", flush=True)
        return salida
    except MaxTurnsExceeded:
        msg = f"ERROR: {nombre} superó el límite de {MAX_TURNOS[nombre]} turnos sin terminar."
        registrar(nombre, mensaje, msg, None, time.time() - t0, error="max_turns")
        print(f"  ✗ {msg}", flush=True)
        return msg
    except Exception as ex:
        msg = f"ERROR: {nombre} falló: {type(ex).__name__}: {str(ex)[:500]}"
        registrar(nombre, mensaje, msg, None, time.time() - t0, error=type(ex).__name__)
        print(f"  ✗ {msg}", flush=True)
        return msg


@function_tool
async def trend_scout(mensaje: str) -> str:
    """Delega en el Trend Scout (investigación). El mensaje debe incluir tema, cliente, carpeta del run y ruta de salida."""
    return await delegar("trend-scout", mensaje)


@function_tool
async def report_writer(mensaje: str) -> str:
    """Delega en el Report Writer (redacción o corrección). El mensaje debe incluir modo, rutas de entrada y salida."""
    return await delegar("report-writer", mensaje)


@function_tool
async def quality_auditor(mensaje: str) -> str:
    """Delega en el Quality Auditor (verificación de evidencia, auditoría o publicación). Incluye modo y rutas."""
    return await delegar("quality-auditor", mensaje)


ORQUESTADOR = Agent(
    name="orquestador",
    instructions=cuerpo_md(RAIZ / ".claude/agents/orquestador.md") + ADAPTADOR_ORQUESTADOR,
    model=MODELOS["orquestador"],
    tools=[trend_scout, report_writer, quality_auditor, leer_archivo, ejecutar_script_orquestador],
)


async def main_async(run: str, prueba: bool):
    ESTADO["run"] = run
    ESTADO["inicio"] = time.time()
    if prueba:
        entrada = f"Ejecuta en modo prueba sobre {run} (lee {run}/prueba.json)."
    else:
        entrada = f"{SOLICITUD}\n\nModo: real. Carpeta del run: {run}"
    print(f"Run: {run}\nModelos: {MODELOS}\n")
    t0 = time.time()
    try:
        r = await Runner.run(ORQUESTADOR, entrada, max_turns=MAX_TURNOS["orquestador"])
        salida, uso, error = str(r.final_output), r.context_wrapper.usage, None
    except MaxTurnsExceeded:
        salida, uso, error = "ERROR: el orquestador superó el límite de turnos.", None, "max_turns"
    duracion = time.time() - t0
    registrar("orquestador", entrada, salida, uso, duracion, error)

    total = {k: sum(v[k] for v in ESTADO["uso"].values()) for k in ("requests", "input_tokens", "output_tokens")}
    resumen = {"run": run, "modo": "prueba" if prueba else "real", "duracion_segundos": round(duracion, 1),
               "por_agente": ESTADO["uso"], "total": total}
    Path(run).mkdir(parents=True, exist_ok=True)
    (Path(run) / "uso.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    (Path(run) / "respuesta_final.md").write_text(salida, encoding="utf-8")
    print("\n" + "=" * 70 + f"\n{salida}\n" + "=" * 70)
    print(f"\nDuración: {duracion / 60:.1f} min · Tokens entrada: {total['input_tokens']:,} · "
          f"salida: {total['output_tokens']:,} · requests: {total['requests']}")
    print(f"Detalle de uso: {run}/uso.json")


def main():
    p = argparse.ArgumentParser(description="Sistema multiagente con OpenAI")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--run", help="Carpeta del run en modo real (p. ej. runs/v1-base_caso1)")
    g.add_argument("--prueba", help="Carpeta preparada con scripts/inyectar_fallo.py")
    a = p.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("Falta OPENAI_API_KEY. Copia .env.ejemplo a .env y pon tu key.")
    if a.prueba:
        run, prueba = a.prueba.rstrip("/\\"), True
        if not (RAIZ / run / "prueba.json").exists():
            sys.exit(f"No existe {run}/prueba.json. Prepáralo con scripts/inyectar_fallo.py")
    else:
        run, prueba = (a.run or f"runs/{datetime.now():%Y%m%d-%H%M%S}").rstrip("/\\"), False
        if (RAIZ / run / "log.jsonl").exists():
            sys.exit(f"{run} ya tiene una corrida. Usa otra carpeta.")
    os.chdir(RAIZ)
    asyncio.run(main_async(run, prueba))


if __name__ == "__main__":
    main()
