#!/usr/bin/env python3
"""Filtra los hallazgos con los veredictos de verificación de evidencia.

Reglas (fail-closed):
  - Una evidencia pasa solo si el auditor la marcó VERIFICADA.
  - Si verificar_fuentes.py la marcó 'inaccesible', se rechaza aunque el auditor diga lo contrario.
  - Una evidencia sin veredicto se rechaza.
  - Una tendencia que se queda sin evidencias se elimina.

Uso:
  python3 aplicar_verificacion.py --hallazgos runs/<id>/02_hallazgos_contrato.json \
      --fuentes runs/<id>/03_verificacion_fuentes.json \
      --veredictos runs/<id>/03_verificacion_evidencia.json \
      --salida runs/<id>/03_hallazgos_validados.json --reporte runs/<id>/03_filtrado.json
"""
import argparse
import copy
import json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hallazgos", required=True)
    p.add_argument("--fuentes", required=True)
    p.add_argument("--veredictos", required=True)
    p.add_argument("--salida", required=True)
    p.add_argument("--reporte", required=True)
    a = p.parse_args()

    data = json.load(open(a.hallazgos, encoding="utf-8"))
    fuentes = {e["id"]: e for e in json.load(open(a.fuentes, encoding="utf-8"))["evidencias"]}
    veredictos = {v["id"]: v for v in json.load(open(a.veredictos, encoding="utf-8"))["evidencias"]}

    salida = copy.deepcopy(data)
    rechazadas, tendencias_eliminadas = [], []
    nuevas = []
    for t in salida["tendencias"]:
        conservadas = []
        for e in t["evidencias"]:
            eid = e["id"]
            v = veredictos.get(eid)
            f = fuentes.get(eid, {})
            if f.get("estado") == "inaccesible":
                rechazadas.append({"id": eid, "tendencia": t["id"], "motivo": f"URL inaccesible ({f.get('http') or f.get('error')})",
                                   "url": e["fuente"]["url"]})
            elif not v:
                rechazadas.append({"id": eid, "tendencia": t["id"], "motivo": "sin veredicto del auditor (fail-closed)",
                                   "url": e["fuente"]["url"]})
            elif v.get("veredicto") != "VERIFICADA":
                rechazadas.append({"id": eid, "tendencia": t["id"], "motivo": v.get("motivo", "rechazada por el auditor"),
                                   "url": e["fuente"]["url"]})
            else:
                conservadas.append(e)
        if conservadas:
            t["evidencias"] = conservadas
            nuevas.append(t)
        else:
            tendencias_eliminadas.append({"id": t["id"], "nombre": t["nombre"]})
    salida["tendencias"] = nuevas
    salida["verificacion"] = {"evidencias_rechazadas": [r["id"] for r in rechazadas]}

    rep = {
        "evidencias_entrada": sum(len(t["evidencias"]) for t in data["tendencias"]),
        "evidencias_validas": sum(len(t["evidencias"]) for t in nuevas),
        "evidencias_rechazadas": rechazadas,
        "tendencias_entrada": len(data["tendencias"]),
        "tendencias_validas": len(nuevas),
        "tendencias_eliminadas": tendencias_eliminadas,
    }
    json.dump(salida, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(rep, open(a.reporte, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
