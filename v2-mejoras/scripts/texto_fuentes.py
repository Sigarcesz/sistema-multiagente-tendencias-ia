"""Utilidades compartidas para descargar fuentes y compararlas con la evidencia.

Lo usan el runner (herramienta web_fetch) y los scripts de verificación. Así una página
se descarga una sola vez por run: el texto crudo queda en runs/<id>/fuentes_cache/ y
cualquier etapa posterior lo reutiliza. Lo que se comparte es el texto descargado por
código, nunca la interpretación de un agente, así que la verificación sigue siendo
independiente del Scout.
"""
import hashlib
import io
import re
import unicodedata
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "es,en;q=0.8",
}
MIN_TEXTO_LEGIBLE = 300
RE_NUM = re.compile(r"(?<![\w])(\d+(?:[.,]\d+)*)")


def ruta_cache(run: Path, url: str) -> Path:
    return Path(run) / "fuentes_cache" / (hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".txt")


def extraer_texto(contenido: bytes, tipo: str, url: str) -> str:
    if "pdf" in tipo or url.lower().split("?")[0].endswith(".pdf"):
        from pypdf import PdfReader
        lector = PdfReader(io.BytesIO(contenido))
        return "\n".join((pg.extract_text() or "") for pg in lector.pages[:60])
    from bs4 import BeautifulSoup
    sopa = BeautifulSoup(contenido, "html.parser")
    for tag in sopa(["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]):
        tag.decompose()
    titulo = sopa.title.get_text(strip=True) if sopa.title else ""
    lineas = (x.strip() for x in sopa.get_text("\n").splitlines())
    return f"TÍTULO: {titulo}\n" + "\n".join(l for l in lineas if l)


def descargar(url: str, run: Path | None = None, timeout: int = 30) -> dict:
    """Devuelve {estado, http, url_final, texto, desde_cache}.
    estado: legible | ilegible | inaccesible | error_http"""
    if run is not None:
        c = ruta_cache(run, url)
        if c.exists():
            texto = c.read_text(encoding="utf-8")
            return {"estado": "legible" if len(texto) >= MIN_TEXTO_LEGIBLE else "ilegible",
                    "http": 200, "url_final": url, "texto": texto, "desde_cache": True}
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.exceptions.ConnectionError as ex:
        return {"estado": "inaccesible", "http": None, "url_final": url, "texto": "",
                "error": f"conexion: {str(ex)[:160]}", "desde_cache": False}
    except requests.exceptions.RequestException as ex:
        return {"estado": "error_http", "http": None, "url_final": url, "texto": "",
                "error": str(ex)[:160], "desde_cache": False}
    if r.status_code in (404, 410):
        return {"estado": "inaccesible", "http": r.status_code, "url_final": r.url, "texto": "", "desde_cache": False}
    if r.status_code >= 400:
        return {"estado": "error_http", "http": r.status_code, "url_final": r.url, "texto": "", "desde_cache": False}
    try:
        texto = extraer_texto(r.content, r.headers.get("content-type", ""), r.url)
    except Exception as ex:
        return {"estado": "ilegible", "http": r.status_code, "url_final": r.url, "texto": "",
                "error": f"extraccion: {ex}", "desde_cache": False}
    if run is not None and len(texto) >= MIN_TEXTO_LEGIBLE:
        c = ruta_cache(run, url)
        c.parent.mkdir(parents=True, exist_ok=True)
        c.write_text(texto, encoding="utf-8")
    return {"estado": "legible" if len(texto) >= MIN_TEXTO_LEGIBLE else "ilegible", "http": r.status_code,
            "url_final": r.url, "texto": texto, "desde_cache": False}


def valor(tok: str) -> float:
    """'1.200' -> 1200 ; '2,5' -> 2.5 ; '1,200' -> 1200 ; '4.7' -> 4.7"""
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", tok):
        return float(re.sub(r"[.,]", "", tok))
    return float(tok.replace(",", "."))


def numeros(texto: str) -> set[float]:
    out = set()
    for m in RE_NUM.finditer(texto):
        try:
            out.add(round(valor(m.group(1)), 4))
        except ValueError:
            pass
    return out


def norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w%]+", " ", t).strip()


def extracto_presente(extracto: str, texto: str) -> bool:
    """Coincidencia textual tolerante a mayúsculas, tildes, puntuación y saltos de línea."""
    e, t = norm(extracto), norm(texto)
    if not e:
        return False
    if e in t:
        return True
    palabras = e.split()
    if len(palabras) < 6:
        return False
    # tolerancia: alguna ventana de 6 palabras consecutivas del extracto aparece en el texto
    return any(" ".join(palabras[i:i + 6]) in t for i in range(0, len(palabras) - 5))


def extracto_relevante(texto: str, consulta: str = "", max_caracteres: int = 5000) -> str:
    """Devuelve el inicio de la página y las líneas con cifras o con palabras de la consulta,
    en su orden original, hasta max_caracteres. Reduce el contexto que recibe el modelo."""
    lineas = texto.splitlines()
    claves = {w for w in norm(consulta).split() if len(w) > 3}
    puntaje = []
    for i, l in enumerate(lineas):
        nl = norm(l)
        s = 0
        if re.search(r"\d", l):
            s += 2
        if "%" in l or re.search(r"\b(million|billion|millones|billones|percent|por ciento)\b", nl):
            s += 2
        s += sum(1 for w in claves if w in nl)
        puntaje.append((s, i))
    elegidas, total = set(), 0
    cabecera = []
    for l in lineas:
        if total > 700:
            break
        cabecera.append(l)
        total += len(l) + 1
    for s, i in sorted(puntaje, key=lambda x: (-x[0], x[1])):
        if s == 0 or total >= max_caracteres:
            break
        if i < len(cabecera):
            continue
        elegidas.add(i)
        total += len(lineas[i]) + 1
    cuerpo = [lineas[i] for i in sorted(elegidas)]
    return "\n".join(cabecera) + ("\n[…]\n" + "\n".join(cuerpo) if cuerpo else "")
