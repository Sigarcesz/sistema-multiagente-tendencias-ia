#!/usr/bin/env python3
"""Primer filtro mecánico de rastreabilidad: ¿la URL de cada fuente existe?

Clasifica cada URL en:
  - accesible      : respondió 2xx/3xx.
  - inaccesible    : el dominio no resuelve, la conexión falla o responde 404/410.
  - indeterminado  : responde 401/403/429/5xx u otro código (muchos sitios bloquean bots).
                     El auditor debe confirmarla manualmente con WebFetch.

Esto NO prueba que la fuente respalde la afirmación; solo que existe.
Esa segunda verificación la hace el auditor leyendo la página.

Uso:
  python3 verificar_fuentes.py --hallazgos runs/<id>/02_hallazgos_contrato.json \
      --salida runs/<id>/03_verificacion_fuentes.json
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; verificador-fuentes/1.0; proyecto academico)",
    "Accept": "text/html,application/pdf,*/*",
}


def revisar(url: str) -> dict:
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=15)
        if r.status_code in (405, 403, 400) or r.status_code >= 500:
            r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=20, stream=True)
        code = r.status_code
        if 200 <= code < 400:
            estado = "accesible"
        elif code in (404, 410):
            estado = "inaccesible"
        else:
            estado = "indeterminado"
        return {"url": url, "estado": estado, "http": code, "url_final": r.url}
    except requests.exceptions.ConnectionError as ex:
        return {"url": url, "estado": "inaccesible", "http": None, "error": f"conexion: {str(ex)[:160]}"}
    except requests.exceptions.Timeout:
        return {"url": url, "estado": "indeterminado", "http": None, "error": "timeout"}
    except requests.exceptions.RequestException as ex:
        return {"url": url, "estado": "indeterminado", "http": None, "error": str(ex)[:160]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hallazgos", required=True)
    p.add_argument("--salida", required=True)
    a = p.parse_args()

    data = json.load(open(a.hallazgos, encoding="utf-8"))
    evidencias = [(e["id"], e["fuente"]["url"]) for t in data["tendencias"] for e in t["evidencias"]]
    urls = sorted({u for _, u in evidencias})
    with ThreadPoolExecutor(max_workers=8) as ex:
        resultados = {r["url"]: r for r in ex.map(revisar, urls)}

    salida = {"evidencias": [{"id": eid, **resultados[u]} for eid, u in evidencias]}
    resumen = {}
    for e in salida["evidencias"]:
        resumen[e["estado"]] = resumen.get(e["estado"], 0) + 1
    salida["resumen"] = resumen
    json.dump(salida, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
