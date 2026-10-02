#!/usr/bin/env python3
"""Compara runs lado a lado (p. ej. v1 contra v2 del mismo caso).

Métricas: duración total y por etapa, tokens, peticiones, auditorías, score y puntajes,
evidencias válidas y rechazadas (y por qué origen), ajustes de confianza, tipos de fuente
y estado final.

Uso:
  python scripts/comparar_runs.py runs/v1-base_caso1 runs/v2-mejoras_caso1
  python scripts/comparar_runs.py runs/v1-base_caso1 runs/v2-mejoras_caso1 --salida docs/comparacion_caso1.md
"""
import argparse
import json
import re
import sys
from pathlib import Path


def cargar(p: Path):
    try:
        return json.load(open(p, encoding="utf-8")) if p.exists() else None
    except json.JSONDecodeError:
        return None


def jsonl(p: Path):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def etapa(d: dict) -> str:
    m = (d.get("etiqueta", "") + " " + d.get("mensaje", "")).lower()
    if d["agente"] == "trend-scout":
        return "investigación"
    if d["agente"] == "report-writer":
        return "redacción y correcciones"
    if d["agente"] == "quality-auditor":
        if "verific" in m and "evidencia" in m:
            return "verificación de evidencia"
        if "public" in m:
            return "publicación"
        return "auditorías"
    return "otro"


def tiempos_etapa(run: Path) -> dict:
    """Tiempo de pared por etapa: desde el primer inicio hasta el último fin de sus delegaciones
    (las que corren en paralelo no se suman). Para runs sin ts_inicio usa la suma de duraciones."""
    from datetime import datetime, timedelta
    grupos = {}
    for d in jsonl(run / "delegaciones.jsonl"):
        if d["agente"] == "orquestador":
            continue
        fin = datetime.fromisoformat(d["ts"][:19])
        ini = datetime.fromisoformat(d["ts_inicio"][:19]) if d.get("ts_inicio") else fin - timedelta(seconds=d["segundos"])
        grupos.setdefault(etapa(d), []).append((ini, fin))
    for s in jsonl(run / "scripts.jsonl"):
        if s["script"].endswith(("preparar_verificacion.py", "unir_verificacion.py")):
            grupos.setdefault("verificación de evidencia", []).append(
                (datetime.fromisoformat(s["ts_inicio"][:19]), datetime.fromisoformat(s["ts_fin"][:19])))
    out = {}
    for k, v in grupos.items():
        if k in ("auditorías", "redacción y correcciones"):
            out[k] = round(sum((b - a).total_seconds() for a, b in v))
        else:
            out[k] = round((max(b for _, b in v) - min(a for a, _ in v)).total_seconds())
    return out


def metricas(run: Path) -> dict:
    uso = cargar(run / "uso.json") or {}
    auds = sorted(run.glob("auditoria_v*.json"), key=lambda x: int(re.search(r"(\d+)", x.stem).group(1)))
    primera, ult = (cargar(auds[0]), cargar(auds[-1])) if auds else (None, None)
    f = cargar(run / "03_filtrado.json") or {}
    ev = jsonl(run / "log_completo.jsonl")
    fin = [e for e in ev if e["evento"] == "fin"]
    rech = f.get("evidencias_rechazadas", [])
    m = {
        "Versión": uso.get("version", "v1"),
        "Estado final": fin[-1]["estado"] if fin else (ult["estado"] if ult else "—"),
        "Duración total (min)": round(uso.get("duracion_segundos", 0) / 60, 1),
        "Tokens de entrada": f"{uso.get('total', {}).get('input_tokens', 0):,}",
        "Tokens de salida": f"{uso.get('total', {}).get('output_tokens', 0):,}",
        "Peticiones al modelo": uso.get("total", {}).get("requests", "—"),
        "Auditorías": len(auds),
        "Score primera auditoría": primera["score_global"] if primera else "—",
        "Score final": ult["score_global"] if ult else "—",
    }
    if ult:
        for c, v in ult["puntajes"].items():
            m[f"  {c}"] = v
    m.update({
        "Tendencias válidas": f"{f.get('tendencias_validas', '—')}/{f.get('tendencias_entrada', '—')}",
        "Evidencias válidas": f"{f.get('evidencias_validas', '—')}/{f.get('evidencias_entrada', '—')}",
        "Rechazadas por chequeo mecánico": sum(1 for r in rech if r.get("origen") == "mecanico") if rech and "origen" in rech[0] else "n/d",
        "Rechazadas por el auditor": sum(1 for r in rech if r.get("origen") == "auditor") if rech and "origen" in rech[0] else len(rech),
        "Ajustes de confianza": len(f.get("ajustes_confianza", [])) if "ajustes_confianza" in f else "n/d",
        "Tipos de fuente válidas": f.get("tipos_fuente_validas", "n/d"),
    })
    for k, v in tiempos_etapa(run).items():
        m[f"Tiempo: {k} (s)"] = v
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--salida")
    a = p.parse_args()
    runs = [Path(r) for r in a.runs]
    # Una ruta mal escrita producía una tabla de ceros con exit 0, indistinguible de un run vacío.
    invalidos = [str(r) for r in runs if not r.is_dir()]
    if invalidos:
        sys.exit(f"ERROR: no existe la carpeta de run: {', '.join(invalidos)}\n"
                 f"Directorio actual: {Path.cwd()}")
    ms = [metricas(r) for r in runs]
    claves = list(dict.fromkeys(k for m in ms for k in m))
    lineas = ["| Métrica | " + " | ".join(r.name for r in runs) + " |", "|---|" + "---|" * len(runs)]
    for k in claves:
        lineas.append(f"| {k} | " + " | ".join(str(m.get(k, "—")) for m in ms) + " |")
    texto = "\n".join(lineas)
    print(texto)
    if a.salida:
        Path(a.salida).write_text(f"# Comparación de runs\n\n{texto}\n", encoding="utf-8")
        print(f"\nGuardado en {a.salida}")


if __name__ == "__main__":
    main()
