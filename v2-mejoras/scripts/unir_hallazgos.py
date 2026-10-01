#!/usr/bin/env python3
"""Une en un solo archivo las tendencias que investigaron varios Scouts en paralelo.

Cada Scout trabaja una tendencia y numera su evidencia localmente (E1, E2…). Este script
toma las candidatas en el orden de 01a_candidatas.json, lee 01b_tendencias/<id>.json,
descarta las que el Scout marcó como descartadas y renumera T# y E# de forma global.

Uso:
  python scripts/unir_hallazgos.py --run runs/<id>
  -> runs/<id>/01_hallazgos_scout.json y runs/<id>/01_union.json (resumen)
"""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    a = p.parse_args()
    run = Path(a.run)

    cand = json.load(open(run / "01a_candidatas.json", encoding="utf-8"))
    tendencias, descartadas, faltantes, ne = [], [], [], 0
    for c in cand["candidatas"]:
        f = run / "01b_tendencias" / f"{c['id']}.json"
        if not f.exists():
            faltantes.append(c["id"])
            continue
        try:
            t = json.load(open(f, encoding="utf-8"))
        except json.JSONDecodeError as ex:
            faltantes.append(f"{c['id']} (JSON inválido: {ex})")
            continue
        if t.get("descartada"):
            descartadas.append({"id": c["id"], "nombre": c.get("nombre"), "motivo": t.get("motivo", "")})
            continue
        t["id_candidata"] = c["id"]
        t["id"] = f"T{len(tendencias) + 1}"
        for e in t.get("evidencias", []):
            ne += 1
            e["id_local"] = e.get("id")
            e["id"] = f"E{ne}"
        tendencias.append(t)

    salida = {"tema": cand.get("tema", ""), "fecha_investigacion": cand.get("fecha_investigacion", ""),
              "tendencias": tendencias}
    json.dump(salida, open(run / "01_hallazgos_scout.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rep = {"candidatas": len(cand["candidatas"]), "tendencias": len(tendencias), "evidencias": ne,
           "descartadas": descartadas, "faltantes": faltantes}
    json.dump(rep, open(run / "01_union.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
