#!/usr/bin/env python3
"""Prepara la verificación de evidencia (antes del escritor).

1. Descarga en paralelo todas las URLs de los hallazgos (o las reutiliza de la caché del
   run, si el Scout ya las había leído). Cada fuente se descarga una sola vez.
2. Comprueba de forma mecánica, contra el texto descargado:
   - que cada cifra declarada aparezca en la página (por valor numérico);
   - que el extracto textual declarado aparezca en la página.
3. Reparte el trabajo: un archivo pendiente_<T#>.json por tendencia, para que varios
   auditores verifiquen en paralelo leyendo el texto local en vez de la web.

Uso:
  python scripts/preparar_verificacion.py --run runs/<id>
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texto_fuentes import descargar, extracto_presente, numeros, ruta_cache  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--hallazgos", default="02_hallazgos_contrato.json")
    a = p.parse_args()
    run = Path(a.run)
    h = json.load(open(run / a.hallazgos, encoding="utf-8"))
    dest = run / "03_verificacion"
    dest.mkdir(exist_ok=True)

    urls = sorted({e["fuente"]["url"] for t in h["tendencias"] for e in t["evidencias"]})
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = dict(zip(urls, ex.map(lambda u: descargar(u, run), urls)))

    mecanica, compat = [], []
    for t in h["tendencias"]:
        pendientes = []
        for e in t["evidencias"]:
            r = res[e["fuente"]["url"]]
            nums_texto = numeros(r["texto"]) if r["texto"] else set()
            cifras = []
            for c in e.get("cifras", []):
                valores = sorted(numeros(str(c)))
                cifras.append({"cifra": c, "encontrada": bool(valores) and all(v in nums_texto for v in valores)})
            ext = e.get("extracto")
            item = {
                "id": e["id"], "tendencia": t["id"], "url": e["fuente"]["url"],
                "estado_fuente": r["estado"], "http": r.get("http"), "desde_cache": r.get("desde_cache"),
                "texto_local": ruta_cache(run, e["fuente"]["url"]).as_posix() if r["estado"] == "legible" else None,
                "cifras": cifras,
                "cifras_no_encontradas": [c["cifra"] for c in cifras if not c["encontrada"]] if r["estado"] == "legible" else [],
                "extracto_encontrado": (extracto_presente(ext, r["texto"]) if ext and r["texto"] else None),
                "error": r.get("error"),
            }
            mecanica.append(item)
            compat.append({"id": e["id"], "url": e["fuente"]["url"],
                           "estado": "inaccesible" if r["estado"] == "inaccesible" else
                                     ("accesible" if r["estado"] == "legible" else "indeterminado"),
                           "http": r.get("http")})
            pendientes.append({"evidencia": e, "chequeo_mecanico": item})
        json.dump({"tendencia": {k: v for k, v in t.items() if k != "evidencias"}, "evidencias": pendientes},
                  open(dest / f"pendiente_{t['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    resumen = {
        "fuentes": len(urls),
        "descargadas_ahora": sum(1 for r in res.values() if not r.get("desde_cache") and r["estado"] == "legible"),
        "reutilizadas_de_cache": sum(1 for r in res.values() if r.get("desde_cache")),
        "legibles": sum(1 for r in res.values() if r["estado"] == "legible"),
        "inaccesibles": sum(1 for r in res.values() if r["estado"] == "inaccesible"),
        "ilegibles_o_bloqueadas": sum(1 for r in res.values() if r["estado"] in ("ilegible", "error_http")),
        "evidencias_con_cifras_no_encontradas": [m["id"] for m in mecanica if m["cifras_no_encontradas"]],
        "evidencias_con_extracto_no_encontrado": [m["id"] for m in mecanica if m["extracto_encontrado"] is False],
        "tendencias": [t["id"] for t in h["tendencias"]],
    }
    json.dump({"evidencias": mecanica, "resumen": resumen}, open(dest / "mecanica.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump({"evidencias": compat, "resumen": resumen}, open(run / "03_verificacion_fuentes.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
