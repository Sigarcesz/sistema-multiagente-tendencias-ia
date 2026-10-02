#!/usr/bin/env python3
"""Une en un solo archivo las tendencias que investigaron varios Scouts en paralelo.

Cada Scout trabaja una tendencia y numera su evidencia localmente (E1, E2…). Este script
toma las candidatas en el orden de 01a_candidatas.json, lee 01b_tendencias/<id>.json,
descarta las que el Scout marcó como descartadas y normaliza el resultado.

La normalización (renumerar T# y E# de forma global y llevar fechas reconocibles a
AAAA-MM-DD) vive solo aquí: el modelo no numera ni formatea fechas de forma fiable, y una
corrección del Scout puede deshacer ambas cosas. Por eso el archivo corregido vuelve a
pasar por este mismo script (modo --desde) antes de la compuerta de contrato.

Uso:
  python scripts/unir_hallazgos.py --run runs/<id>
  -> runs/<id>/01_hallazgos_scout.json y runs/<id>/01_union.json (resumen)
  python scripts/unir_hallazgos.py --desde runs/<id>/01_hallazgos_scout_corregido.json \
      --salida runs/<id>/01_hallazgos_scout_v2.json
"""
import argparse
import json
import re
from pathlib import Path

MESES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12, "ene": 1, "abr": 4, "dic": 12,
    # "ago" (agosto) queda fuera a propósito: en inglés "3 years ago, 2023" se leería como agosto.
}
RE_ISO = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
# Más largos primero, y "\.?" admite "Jan." sin que "jan" se coma a "january".
_M = "|".join(sorted(MESES, key=len, reverse=True))
PATRONES_FECHA = [  # (regex, orden de los grupos)
    (re.compile(rf"\b(\d{{1,2}})(?:\s+de)?\s+({_M})\.?(?:\s+de)?,?\s+(\d{{4}})\b"), "dmy"),  # 31 July 2026 / 31 de julio de 2026
    (re.compile(rf"\b({_M})\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b"), "mdy"),                      # July 31, 2026
    (re.compile(rf"\b({_M})\.?(?:\s+de)?,?\s+(\d{{4}})\b"), "my"),                           # July 2026 / julio de 2026
    (re.compile(r"\b(\d{4})[/.](\d{1,2})[/.](\d{1,2})\b"), "ymd"),                        # 2026/07/31
]


def normalizar_fecha(texto: str) -> str | None:
    """Devuelve la fecha en AAAA-MM-DD / AAAA-MM si el texto contiene exactamente una fecha
    reconocible; None si no hay ninguna o hay varias (no se adivina cuál es la de publicación).
    Formatos numéricos día/mes ambiguos (07/08/2026) no se intentan."""
    t = str(texto).strip().lower()
    if RE_ISO.match(t):
        return t
    halladas, ocupado = set(), []
    for rx, orden in PATRONES_FECHA:
        for m in rx.finditer(t):
            if any(a < m.end() and m.start() < b for a, b in ocupado):
                continue  # "July 2026" dentro de "31 July 2026" ya contado
            ocupado.append(m.span())
            g = dict(zip(orden, m.groups()))
            mes = MESES.get(g["m"]) if not g["m"].isdigit() else int(g["m"])
            if not mes or not 1 <= mes <= 12:
                continue
            if "d" in g:
                if not 1 <= int(g["d"]) <= 31:
                    continue
                halladas.add(f"{g['y']}-{mes:02d}-{int(g['d']):02d}")
            else:
                halladas.add(f"{g['y']}-{mes:02d}")
    return halladas.pop() if len(halladas) == 1 else None


def normalizar(tendencias: list) -> tuple[list, list]:
    """Renumera T# y E# en orden y normaliza las fechas de las fuentes.
    Devuelve las tendencias y la lista de fechas cambiadas (para dejar rastro)."""
    cambios, ne = [], 0
    for i, t in enumerate(tendencias, 1):
        t["id"] = f"T{i}"
        evs = t.get("evidencias")
        for e in evs if isinstance(evs, list) else []:
            ne += 1
            e.setdefault("id_local", e.get("id"))
            e["id"] = f"E{ne}"
            f = e.get("fuente")
            if isinstance(f, dict) and f.get("fecha") and not RE_ISO.match(str(f["fecha"])):
                nueva = normalizar_fecha(f["fecha"])
                if nueva:  # si no se reconoce, queda igual y la compuerta lo rechaza con su motivo
                    cambios.append({"evidencia": e["id"], "original": f["fecha"], "normalizada": nueva})
                    f["fecha"] = nueva
    return tendencias, cambios


def unir(run: Path):
    cand = json.load(open(run / "01a_candidatas.json", encoding="utf-8"))
    tendencias, descartadas, faltantes = [], [], []
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
        tendencias.append(t)
    tendencias, cambios = normalizar(tendencias)

    salida = {"tema": cand.get("tema", ""), "fecha_investigacion": cand.get("fecha_investigacion", ""),
              "tendencias": tendencias}
    json.dump(salida, open(run / "01_hallazgos_scout.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rep = {"candidatas": len(cand["candidatas"]), "tendencias": len(tendencias),
           "evidencias": sum(len(t.get("evidencias") or []) for t in tendencias),
           "descartadas": descartadas, "faltantes": faltantes, "fechas_normalizadas": cambios}
    json.dump(rep, open(run / "01_union.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}, ensure_ascii=False))


def renormalizar(entrada: Path, salida: Path):
    data = json.load(open(entrada, encoding="utf-8"))
    data["tendencias"], cambios = normalizar(data.get("tendencias") or [])
    json.dump(data, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"salida": str(salida), "tendencias": len(data["tendencias"]),
                      "fechas_normalizadas": cambios}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", help="Une 01b_tendencias/ de este run")
    g.add_argument("--desde", help="Renormaliza un archivo de hallazgos ya unido (p. ej. tras una corrección)")
    p.add_argument("--salida", help="Con --desde: archivo de salida (distinto de la entrada)")
    a = p.parse_args()
    if a.run:
        unir(Path(a.run))
    else:
        if not a.salida or Path(a.salida).resolve() == Path(a.desde).resolve():
            p.error("--desde requiere --salida distinta de la entrada")
        renormalizar(Path(a.desde), Path(a.salida))


if __name__ == "__main__":
    main()
