#!/usr/bin/env python3
"""Registro de ejecución del orquestador.

Uso:
  python3 scripts/log.py init --run runs/<id> --solicitud "texto de la solicitud" [--modo real|prueba]
  python3 scripts/log.py evento --run runs/<id> --paso 3 --componente quality-auditor \
      --evento verificacion_evidencia --estado OK --detalle "2 evidencias rechazadas" \
      [--iteracion 1] [--artefactos a.json b.json]
  python3 scripts/log.py resumen --run runs/<id>      # genera runs/<id>/log.md

Cada evento se guarda como una línea JSON en runs/<id>/log.jsonl. Nada se borra:
el log es la evidencia de la ejecución (entregable 2).
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def ahora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def escribir(run: Path, registro: dict) -> None:
    run.mkdir(parents=True, exist_ok=True)
    with open(run / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def cmd_init(a):
    run = Path(a.run)
    if (run / "log.jsonl").exists():
        print(f"ERROR: {run}/log.jsonl ya existe; usa otro --run", file=sys.stderr)
        sys.exit(2)
    escribir(run, {
        "ts": ahora(), "run": run.name, "paso": 0, "iteracion": 0,
        "componente": "orquestador", "evento": "inicio", "estado": "OK",
        "detalle": a.solicitud, "modo": a.modo, "artefactos": [],
    })
    print(f"Run iniciado en {run}")


def cmd_evento(a):
    run = Path(a.run)
    if not (run / "log.jsonl").exists():
        print("ERROR: run no inicializado (usa 'init' primero)", file=sys.stderr)
        sys.exit(2)
    escribir(run, {
        "ts": ahora(), "run": run.name, "paso": a.paso, "iteracion": a.iteracion,
        "componente": a.componente, "evento": a.evento, "estado": a.estado,
        "detalle": a.detalle, "artefactos": a.artefactos or [],
    })
    print("ok")


def cmd_resumen(a):
    run = Path(a.run)
    eventos = [json.loads(l) for l in open(run / "log.jsonl", encoding="utf-8") if l.strip()]
    lineas = [
        f"# Registro de ejecución — {run.name}", "",
        f"Inicio: {eventos[0]['ts']}  ",
        f"Fin: {eventos[-1]['ts']}  ",
        f"Modo: {eventos[0].get('modo', 'real')}  ",
        f"Solicitud: {eventos[0]['detalle']}", "",
        "| # | Hora | Paso | Iter. | Componente | Evento | Estado | Detalle | Artefactos |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(eventos, 1):
        det = str(e.get("detalle", "")).replace("|", "\\|").replace("\n", " ")
        art = ", ".join(e.get("artefactos", []))
        hora = e["ts"][11:19]
        lineas.append(
            f"| {i} | {hora} | {e['paso']} | {e.get('iteracion', 0)} | {e['componente']} | "
            f"{e['evento']} | {e['estado']} | {det} | {art} |"
        )
    violaciones = [e for e in eventos if e["evento"].startswith("violacion")]
    lineas += ["", f"Violaciones registradas: {len(violaciones)}", ""]
    final = [e for e in eventos if e["evento"] == "fin"]
    if final:
        lineas.append(f"**Estado final: {final[-1]['estado']}** — {final[-1]['detalle']}")
    (run / "log.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Resumen escrito en {run / 'log.md'}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init")
    i.add_argument("--run", required=True)
    i.add_argument("--solicitud", required=True)
    i.add_argument("--modo", default="real")
    i.set_defaults(fn=cmd_init)

    e = sub.add_parser("evento")
    e.add_argument("--run", required=True)
    e.add_argument("--paso", type=int, required=True)
    e.add_argument("--iteracion", type=int, default=0)
    e.add_argument("--componente", required=True)
    e.add_argument("--evento", required=True)
    e.add_argument("--estado", required=True)
    e.add_argument("--detalle", default="")
    e.add_argument("--artefactos", nargs="*")
    e.set_defaults(fn=cmd_evento)

    r = sub.add_parser("resumen")
    r.add_argument("--run", required=True)
    r.set_defaults(fn=cmd_resumen)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
