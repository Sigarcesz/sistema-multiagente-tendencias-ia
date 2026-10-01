"""Herramientas que reemplazan las de Claude Code (Read, Write, Bash, WebFetch).

Cada agente recibe solo las que su rol necesita (ver agentes.py). Las restricciones
viven aquí, en código: aunque un agente lo intente, no puede escribir fuera de runs/,
leer el .env ni ejecutar scripts que no estén en la lista blanca.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import requests
from agents import function_tool
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
RUNS = RAIZ / "runs"

SCRIPTS_PERMITIDOS = {
    "scripts/log.py",
    "scripts/validar_contrato.py",
    ".claude/skills/quality-auditor/scripts/verificar_fuentes.py",
    ".claude/skills/quality-auditor/scripts/aplicar_verificacion.py",
    ".claude/skills/quality-auditor/scripts/verificar_informe.py",
    ".claude/skills/quality-auditor/scripts/decidir_estado.py",
    ".claude/skills/quality-auditor/scripts/generar_docx.py",
}
# Qué scripts puede ejecutar cada rol
SCRIPTS_ORQUESTADOR = {"scripts/log.py", "scripts/validar_contrato.py"}
SCRIPTS_AUDITOR = SCRIPTS_PERMITIDOS - SCRIPTS_ORQUESTADOR

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; trend-research-bot/1.0; proyecto academico)"}


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
        return f"OK: escrito {p.relative_to(RAIZ)} ({len(contenido)} caracteres)"
    except json.JSONDecodeError as ex:
        return f"ERROR: el contenido no es JSON válido ({ex}). Corrígelo y vuelve a escribir."
    except Exception as ex:
        return f"ERROR: {ex}"


def _ejecutar(script: str, argumentos: list[str], permitidos: set[str]) -> str:
    script = script.strip().replace("\\", "/")
    for prefijo in ("python3 ", "python "):
        if script.startswith(prefijo):
            script = script[len(prefijo):].strip()
    if script.startswith("./"):
        script = script[2:]
    if script not in permitidos:
        return f"ERROR: script no permitido para este rol. Permitidos: {sorted(permitidos)}"
    r = subprocess.run([sys.executable, str(RAIZ / script), *argumentos], cwd=RAIZ,
                       capture_output=True, text=True, timeout=600)
    salida = (r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr.strip() else "")).strip()
    return f"codigo_salida={r.returncode}\n{salida[:20_000]}"


@function_tool
def ejecutar_script_orquestador(script: str, argumentos: list[str]) -> str:
    """Ejecuta un script de control del orquestador (scripts/log.py o scripts/validar_contrato.py).
    'argumentos' es la lista de argumentos tal como irían en la línea de comandos.
    Devuelve el código de salida y la salida estándar."""
    return _ejecutar(script, argumentos, SCRIPTS_ORQUESTADOR)


@function_tool
def ejecutar_script_auditor(script: str, argumentos: list[str]) -> str:
    """Ejecuta un script del auditor (.claude/skills/quality-auditor/scripts/*.py).
    'argumentos' es la lista de argumentos tal como irían en la línea de comandos.
    Devuelve el código de salida y la salida estándar."""
    return _ejecutar(script, argumentos, SCRIPTS_AUDITOR)


@function_tool
def web_fetch(url: str, max_caracteres: int = 12000) -> str:
    """Descarga una página web o PDF y devuelve su texto legible (truncado a max_caracteres).
    Úsalo para leer una fuente antes de citarla o para verificar que respalda una afirmación."""
    return descargar_texto(url, max_caracteres)


def descargar_texto(url: str, max_caracteres: int = 12000) -> str:
    max_caracteres = max(2000, min(max_caracteres, 30000))
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException as ex:
        return f"ERROR_FETCH: no se pudo conectar ({str(ex)[:200]})"
    if r.status_code >= 400:
        return f"ERROR_FETCH: HTTP {r.status_code} en {r.url}"
    tipo = r.headers.get("content-type", "")
    try:
        if "pdf" in tipo or url.lower().endswith(".pdf"):
            from pypdf import PdfReader
            lector = PdfReader(io.BytesIO(r.content))
            texto = "\n".join((pg.extract_text() or "") for pg in lector.pages[:40])
        else:
            sopa = BeautifulSoup(r.text, "html.parser")
            for tag in sopa(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            titulo = sopa.title.get_text(strip=True) if sopa.title else ""
            texto = f"TÍTULO: {titulo}\n\n" + "\n".join(
                l for l in (x.strip() for x in sopa.get_text("\n").splitlines()) if l)
    except Exception as ex:
        return f"ERROR_FETCH: no se pudo extraer el texto ({ex})"
    if len(texto.strip()) < 200:
        return f"ERROR_FETCH: la página no tiene texto legible (posible bloqueo o contenido dinámico). URL final: {r.url}"
    return f"URL_FINAL: {r.url}\n\n{texto[:max_caracteres]}" + ("\n[...truncado...]" if len(texto) > max_caracteres else "")
