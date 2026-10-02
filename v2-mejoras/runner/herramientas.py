"""Herramientas que reemplazan las de Claude Code (Read, Write, Bash, WebFetch).

Cada agente recibe solo las que su rol necesita (ver main.py). Las restricciones viven
aquí, en código: aunque un agente lo intente, no puede escribir fuera de runs/, leer el
.env ni ejecutar scripts que no estén en la lista blanca de su rol.

Todo lo que pasa por estas herramientas queda registrado por código (scripts.jsonl), así
el registro de la ejecución no depende de que el modelo se acuerde de escribirlo.
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from agents import function_tool

RAIZ = Path(__file__).resolve().parent.parent
RUNS = RAIZ / "runs"
sys.path.insert(0, str(RAIZ / "scripts"))
from texto_fuentes import descargar, extracto_relevante, ruta_cache  # noqa: E402

AUD = ".claude/skills/quality-auditor/scripts/"
SCRIPTS_ORQUESTADOR = {
    "scripts/log.py", "scripts/validar_contrato.py", "scripts/unir_hallazgos.py",
    "scripts/preparar_verificacion.py", "scripts/unir_verificacion.py",
}
SCRIPTS_AUDITOR = {AUD + "verificar_informe.py", AUD + "decidir_estado.py", AUD + "generar_docx.py"}

# La carpeta del run en curso la fija main.py al arrancar (para la caché y los registros).
CONTEXTO = {"run": None}


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _registrar(archivo: str, registro: dict):
    if CONTEXTO["run"]:
        p = RAIZ / CONTEXTO["run"]
        p.mkdir(parents=True, exist_ok=True)
        with open(p / archivo, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def _ruta_segura(path: str, solo_runs: bool) -> Path:
    p = (RAIZ / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if RAIZ not in p.parents and p != RAIZ:
        raise ValueError("Ruta fuera del proyecto")
    if p.name.startswith(".env"):
        raise ValueError("Acceso denegado al archivo de credenciales")
    if solo_runs and RUNS not in p.parents:
        raise ValueError("Solo se permite escribir dentro de runs/")
    return p


@function_tool
def leer_archivo(path: str) -> str:
    """Lee un archivo de texto del proyecto (ruta relativa a la raíz del repo, p. ej. runs/x/informe_v1.md)."""
    try:
        p = _ruta_segura(path, solo_runs=False)
        texto = p.read_text(encoding="utf-8")
        return texto if len(texto) < 120_000 else texto[:120_000] + "\n[...truncado...]"
    except Exception as ex:  # el error vuelve al modelo, no rompe la corrida
        return f"ERROR: {ex}"


@function_tool
def escribir_archivo(path: str, contenido: str) -> str:
    """Escribe (o sobrescribe) un archivo de texto dentro de runs/. Devuelve la ruta escrita.
    Para JSON, el contenido debe ser JSON válido."""
    try:
        p = _ruta_segura(path, solo_runs=True)
        if p.suffix == ".json":
            json.loads(contenido)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        return f"OK: escrito {p.relative_to(RAIZ).as_posix()} ({len(contenido)} caracteres)"
    except json.JSONDecodeError as ex:
        return f"ERROR: el contenido no es JSON válido ({ex}). Corrígelo y vuelve a escribir."
    except Exception as ex:
        return f"ERROR: {ex}"


def _ejecutar(script: str, argumentos: list[str], permitidos: set[str], rol: str) -> str:
    script = script.strip().replace("\\", "/")
    for prefijo in ("python3 ", "python "):
        if script.startswith(prefijo):
            script = script[len(prefijo):].strip()
    if script.startswith("./"):
        script = script[2:]
    if script not in permitidos:
        return f"ERROR: script no permitido para este rol. Permitidos: {sorted(permitidos)}"
    t0, ts0 = time.time(), _ahora()
    r = subprocess.run([sys.executable, str(RAIZ / script), *argumentos], cwd=RAIZ,
                       capture_output=True, text=True, timeout=900, encoding="utf-8", errors="replace")
    salida = (r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr.strip() else "")).strip()
    _registrar("scripts.jsonl", {"ts_inicio": ts0, "ts_fin": _ahora(), "segundos": round(time.time() - t0, 1),
                                 "rol": rol, "script": script, "argumentos": argumentos,
                                 "codigo_salida": r.returncode, "salida": salida[:3000]})
    return f"codigo_salida={r.returncode}\n{salida[:20_000]}"


@function_tool
def ejecutar_script_orquestador(script: str, argumentos: list[str]) -> str:
    """Ejecuta un script de control del orquestador (scripts/log.py, validar_contrato.py, unir_hallazgos.py,
    preparar_verificacion.py o unir_verificacion.py). 'argumentos' es la lista de argumentos de línea de
    comandos. Devuelve el código de salida y la salida estándar."""
    return _ejecutar(script, argumentos, SCRIPTS_ORQUESTADOR, "orquestador")


@function_tool
def ejecutar_script_auditor(script: str, argumentos: list[str]) -> str:
    """Ejecuta un script del auditor (.claude/skills/quality-auditor/scripts/*.py).
    'argumentos' es la lista de argumentos de línea de comandos. Devuelve el código de salida y la salida."""
    return _ejecutar(script, argumentos, SCRIPTS_AUDITOR, "quality-auditor")


@function_tool
def web_fetch(url: str, consulta: str, max_caracteres: int) -> str:
    """Descarga una página web o PDF y devuelve un EXTRACTO: el inicio de la página más las líneas con
    cifras o con palabras de 'consulta' (lo que buscas en esa fuente). Usa max_caracteres entre 2000 y
    8000 (recomendado 5000). El texto completo queda guardado en disco; la respuesta indica la ruta por si
    necesitas leerlo entero con leer_archivo."""
    return descargar_texto(url, consulta, max_caracteres)


def descargar_texto(url: str, consulta: str = "", max_caracteres: int = 5000) -> str:
    max_caracteres = max(2000, min(int(max_caracteres or 5000), 8000))
    run = RAIZ / CONTEXTO["run"] if CONTEXTO["run"] else None
    t0 = time.time()
    r = descargar(url, run)
    _registrar("descargas.jsonl", {"ts": _ahora(), "url": url, "estado": r["estado"], "http": r.get("http"),
                                   "desde_cache": r.get("desde_cache"), "segundos": round(time.time() - t0, 1),
                                   "caracteres": len(r.get("texto", ""))})
    if r["estado"] == "inaccesible":
        return f"ERROR_FETCH: no se pudo conectar o la página no existe ({r.get('http') or r.get('error')})"
    if r["estado"] == "error_http":
        return f"ERROR_FETCH: HTTP {r.get('http')} ({r.get('error', '')})"
    if r["estado"] == "ilegible":
        return "ERROR_FETCH: la página no tiene texto legible (posible bloqueo o contenido dinámico). Busca otra fuente o versión."
    texto = r["texto"]
    ref = ""
    if run is not None:
        ref = f"\nTEXTO_COMPLETO: {ruta_cache(run, url).relative_to(RAIZ).as_posix()} ({len(texto)} caracteres)"
    return (f"URL_FINAL: {r['url_final']}{ref}\n\n" + extracto_relevante(texto, consulta, max_caracteres))
