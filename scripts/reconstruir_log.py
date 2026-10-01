#!/usr/bin/env python3
"""Reconstruye el registro completo de un run a partir de evidencia objetiva.

Motivo: en la corrida base, el orquestador (modelo) inicializó el log pero no registró los
eventos intermedios. El runner sí guarda en código cada delegación (delegaciones.jsonl) y
cada etapa deja artefactos. Este script arma el registro desde esas dos fuentes, sin
depender de que el modelo haya cumplido la instrucción de registrar.

No modifica log.jsonl / log.md (quedan como evidencia de lo que hizo el orquestador).
Escribe log_completo.jsonl y log_completo.md.

Uso:  python scripts/reconstruir_log.py --run runs/v1-base_caso1
      python scripts/reconstruir_log.py --todos      # todas las carpetas de runs/
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cargar(p: Path):
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def reconstruir(run: Path) -> list[dict]:
    ev = []

    def add(ts, componente, evento, estado, detalle, fuente, iteracion=0, artefactos=None):
        ev.append({"ts": ts, "componente": componente, "evento": evento, "estado": estado,
                   "iteracion": iteracion, "detalle": detalle, "fuente": fuente,
                   "artefactos": artefactos or []})

    log0 = [json.loads(l) for l in open(run / "log.jsonl", encoding="utf-8") if l.strip()] if (run / "log.jsonl").exists() else []
    delegs = [json.loads(l) for l in open(run / "delegaciones.jsonl", encoding="utf-8") if l.strip()] if (run / "delegaciones.jsonl").exists() else []
    t_inicio = log0[0]["ts"] if log0 else (delegs[0]["ts"] if delegs else "")
    add(t_inicio, "orquestador", "inicio", "OK", log0[0]["detalle"][:300] if log0 else "", "log.jsonl")

    prueba = cargar(run / "prueba.json")
    if prueba:
        add(t_inicio, "prueba", "inyeccion_prueba", f"CASO_{prueba['caso']}", prueba.get("descripcion", ""),
            "prueba.json", artefactos=[prueba.get("artefacto", "")])

    contrato_emitido = False

    def emitir_contrato(ts):
        nonlocal contrato_emitido
        c = cargar(run / "02_contrato.json")
        if c is None or contrato_emitido:
            return
        contrato_emitido = True
        add(ts, "orquestador", "compuerta_contrato", c["estado"],
            f"{c.get('tendencias')} tendencias, {c.get('evidencias')} evidencias, "
            f"{len(c.get('violaciones', []))} violaciones, {len(c.get('errores', []))} errores",
            "02_contrato.json", artefactos=["02_hallazgos_contrato.json", "02_contrato.json"])
        for v in c.get("violaciones", []):
            add(ts, "orquestador", "violacion_responsabilidad", "ELIMINADO",
                f"{v['ubicacion']}: «{v['contenido_eliminado'][:200]}»", "02_contrato.json")

    n_correccion = 0
    for d in delegs:
        ag, msg, ts = d["agente"], norm(d["mensaje"]), d["ts"]
        if d.get("error"):
            add(ts, ag, "error_delegacion", "ERROR", d["respuesta"][:300], "delegaciones.jsonl")
            continue
        if ag == "trend-scout":
            add(ts, ag, "investigacion", "OK", d["respuesta"][:300], "delegaciones.jsonl",
                artefactos=["01_hallazgos_scout.json"])
        elif ag == "quality-auditor" and "verific" in msg and "evidencia" in msg:
            emitir_contrato(ts)
            f = cargar(run / "03_filtrado.json") or {}
            add(ts, ag, "verificacion_evidencia", "OK",
                f"{f.get('evidencias_validas')}/{f.get('evidencias_entrada')} evidencias válidas; "
                f"{f.get('tendencias_validas')}/{f.get('tendencias_entrada')} tendencias con respaldo",
                "03_filtrado.json", artefactos=["03_verificacion_fuentes.json", "03_verificacion_evidencia.json",
                                                "03_hallazgos_validados.json"])
            for r in f.get("evidencias_rechazadas", []):
                add(ts, ag, "evidencia_rechazada", "RECHAZADA", f"{r['id']} ({r['tendencia']}): {r['motivo'][:250]}",
                    "03_filtrado.json")
            for t in f.get("tendencias_eliminadas", []):
                add(ts, ag, "tendencia_eliminada", "ELIMINADA", f"{t['id']} {t['nombre']}", "03_filtrado.json")
        elif ag == "report-writer":
            m = re.search(r"informe_v(\d+)\.md", d["respuesta"]) or re.findall(r"informe_v(\d+)\.md", d["mensaje"])
            if "correcc" in msg:
                n_correccion += 1
                rc = sorted(run.glob("respuesta_correcciones_v*.json"))
                add(ts, ag, "correccion", "OK", d["respuesta"][:300], "delegaciones.jsonl",
                    iteracion=n_correccion + 1, artefactos=[x.name for x in rc[-1:]])
            else:
                add(ts, ag, "redaccion", "OK", d["respuesta"][:300], "delegaciones.jsonl", iteracion=1,
                    artefactos=["informe_v1.md"])
        elif ag == "quality-auditor" and "public" in msg:
            docs = list((run / "final").glob("*.docx")) if (run / "final").exists() else []
            add(ts, ag, "publicacion", "OK" if docs else "SIN_DOCUMENTO",
                docs[0].name if docs else d["respuesta"][:200], "final/", artefactos=[f"final/{x.name}" for x in docs])
        elif ag == "quality-auditor":
            versiones = [int(x) for x in re.findall(r"informe_v(\d+)\.md", d["mensaje"])]
            n = max(versiones) if versiones else 1
            a = cargar(run / f"auditoria_v{n}.json")
            if a:
                det = f"score {a['score_global']}; " + (
                    f"rechazos automáticos: {a['rechazos_automaticos']}; " if a["rechazos_automaticos"] else "") + (
                    f"umbrales incumplidos: {a['umbrales_incumplidos']}; " if a["umbrales_incumplidos"] else "") + \
                    f"{len(a['correcciones'])} correcciones"
                add(ts, ag, "auditoria", a["estado"], det, f"auditoria_v{n}.json", iteracion=n,
                    artefactos=[f"verificacion_informe_v{n}.json", f"auditoria_v{n}.json"])
            else:
                add(ts, ag, "auditoria", "SIN_ARCHIVO", d["respuesta"][:200], "delegaciones.jsonl", iteracion=n)
        elif ag == "orquestador":
            emitir_contrato(ts)
            auds = sorted(run.glob("auditoria_v*.json"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
            docs = list((run / "final").glob("*.docx")) if (run / "final").exists() else []
            if auds:
                ult = cargar(auds[-1])
                if ult["estado"] == "APROBADO" and docs:
                    estado = "APROBADO"
                elif ult["estado"] == "RECHAZADO" and len(auds) >= 4:
                    estado = "NO_APROBADO"
                else:
                    estado = ult["estado"] if not docs else "APROBADO"
                det = f"{len(auds)} auditoría(s); última: {ult['estado']} (score {ult['score_global']}); documento: {docs[0].name if docs else 'no generado'}"
            else:
                estado, det = "FALLIDO", "no se llegó a auditar ningún informe"
            add(ts, "orquestador", "fin", estado, det, "artefactos del run")
    if not contrato_emitido:
        emitir_contrato(t_inicio)
    return ev


def escribir(run: Path, ev: list[dict]):
    with open(run / "log_completo.jsonl", "w", encoding="utf-8") as f:
        for e in ev:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    lin = [f"# Registro de ejecución (reconstruido) — {run.name}", "",
           "Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner "
           "escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de "
           "dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.", "",
           "| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |",
           "|---|---|---|---|---|---|---|---|"]
    for i, e in enumerate(ev, 1):
        det = str(e["detalle"]).replace("|", "\\|").replace("\n", " ")
        lin.append(f"| {i} | {e['ts'][11:19]} | {e['iteracion']} | {e['componente']} | {e['evento']} | "
                   f"{e['estado']} | {det} | {e['fuente']} |")
    fin = [e for e in ev if e["evento"] == "fin"]
    lin += ["", f"Violaciones registradas: {sum(e['evento'] == 'violacion_responsabilidad' for e in ev)}  ",
            f"Evidencias rechazadas: {sum(e['evento'] == 'evidencia_rechazada' for e in ev)}  ",
            f"Auditorías: {sum(e['evento'] == 'auditoria' for e in ev)} · Correcciones: {sum(e['evento'] == 'correccion' for e in ev)}"]
    uso = cargar(run / "uso.json")
    if uso:
        t = uso["total"]
        lin.append(f"Duración: {uso['duracion_segundos'] / 60:.1f} min · Tokens: {t['input_tokens']:,} entrada / "
                   f"{t['output_tokens']:,} salida · {t['requests']} peticiones")
    lin += ["", f"**Estado final: {fin[-1]['estado']}** — {fin[-1]['detalle']}" if fin else "**Run sin cierre registrado**"]
    (run / "log_completo.md").write_text("\n".join(lin) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--run")
    g.add_argument("--todos", action="store_true")
    a = p.parse_args()
    runs = [Path(a.run)] if a.run else sorted(x for x in Path("runs").iterdir() if x.is_dir())
    for run in runs:
        if not (run / "delegaciones.jsonl").exists():
            print(f"{run}: sin delegaciones.jsonl, se omite")
            continue
        ev = reconstruir(run)
        escribir(run, ev)
        fin = [e for e in ev if e["evento"] == "fin"]
        print(f"{run}: {len(ev)} eventos · estado final: {fin[-1]['estado'] if fin else 'sin cierre (¿sigue corriendo?)'}")


if __name__ == "__main__":
    main()
