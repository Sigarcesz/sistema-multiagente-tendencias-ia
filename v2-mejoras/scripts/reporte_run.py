#!/usr/bin/env python3
"""Genera runs/<id>/reporte_run.html: un solo archivo, sin dependencias, para revisar un run.

Incluye:
  - tablero: estado final, score, duración, tokens y modelos;
  - línea de tiempo: cada delegación y script como barra (se ve qué corrió en paralelo);
  - visor de evidencia: cada E# con su afirmación, cifras, extracto, tipo y fecha de la
    fuente, chequeo mecánico y veredicto del auditor;
  - auditorías por versión;
  - informe final, con cada [E#] enlazado a su evidencia;
  - registro completo de eventos.

Uso:  python scripts/reporte_run.py --run runs/<id>
"""
import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


def cargar(p: Path):
    try:
        return json.load(open(p, encoding="utf-8")) if p.exists() else None
    except json.JSONDecodeError:
        return None


def jsonl(p: Path):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def ts(s):
    try:
        return datetime.fromisoformat(str(s)[:19])
    except ValueError:
        return None


def md_a_html(md: str) -> str:
    out, en_lista, en_tabla = [], False, False
    for l in md.splitlines():
        t = l.strip()
        linea = esc(t)
        linea = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", linea)
        linea = re.sub(r"\[(E\d+)\]", r'<a class="cita" href="#\1">[\1]</a>', linea)
        if t.startswith("|"):
            if re.fullmatch(r"\|?[\s:\-|]+\|?", t):
                continue
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if not en_tabla:
                out.append("<table class='md'>")
                en_tabla = True
            out.append("<tr>" + "".join(f"<td>{c}</td>" for c in celdas) + "</tr>")
            continue
        if en_tabla:
            out.append("</table>")
            en_tabla = False
        if re.match(r"^[-*]\s+", t):
            if not en_lista:
                out.append("<ul>")
                en_lista = True
            item = re.sub(r"^[-*]\s+", "", linea)
            out.append(f"<li>{item}</li>")
            continue
        if en_lista:
            out.append("</ul>")
            en_lista = False
        if t.startswith("### "):
            out.append(f"<h4>{linea[4:]}</h4>")
        elif t.startswith("## "):
            out.append(f"<h3>{linea[3:]}</h3>")
        elif t.startswith("# "):
            out.append(f"<h3>{linea[2:]}</h3>")
        elif t:
            out.append(f"<p>{linea}</p>")
    if en_lista:
        out.append("</ul>")
    if en_tabla:
        out.append("</table>")
    return "\n".join(out)


def en_curso(run: Path) -> dict:
    """Delegaciones que empezaron y aún no terminan (id -> registro de inicio)."""
    activos = {}
    for r in jsonl(run / "en_curso.jsonl"):
        if r.get("fin"):
            activos.pop(r["id"], None)
        else:
            activos[r["id"]] = r
    return activos


def linea_tiempo(run: Path) -> str:
    ahora = datetime.now()
    filas = [(ts(r["ts_inicio"]), ahora, r["etiqueta"] + " (en curso)", r["agente"] + "_activo")
             for k, r in en_curso(run).items() if r["agente"] != "orquestador"]
    for d in jsonl(run / "delegaciones.jsonl"):
        if d["agente"] == "orquestador":
            continue
        a, b = ts(d.get("ts_inicio")), ts(d["ts"])
        if a is None and b is not None:
            from datetime import timedelta
            a = b - timedelta(seconds=d.get("segundos", 0))
        filas.append((a, b, d.get("etiqueta", d["agente"]), d["agente"]))
    for s in jsonl(run / "scripts.jsonl"):
        if s["script"].endswith("log.py"):
            continue
        filas.append((ts(s["ts_inicio"]), ts(s["ts_fin"]), s["script"].split("/")[-1], "script"))
    filas = [f for f in filas if f[0] and f[1]]
    if not filas:
        return "<p class='nota'>Sin datos de tiempos de inicio (run anterior a v2).</p>"
    t0 = min(f[0] for f in filas)
    t1 = max(f[1] for f in filas)
    total = max((t1 - t0).total_seconds(), 1)
    colores = {"trend-scout": "#3b82f6", "quality-auditor": "#ef4444", "report-writer": "#22c55e", "script": "#a3a3a3",
               "trend-scout_activo": "#93c5fd", "quality-auditor_activo": "#fca5a5", "report-writer_activo": "#86efac"}
    alto, ancho, izq = 22, 900, 230
    svg = [f"<svg viewBox='0 0 {izq + ancho + 60} {len(filas) * alto + 30}' class='gantt'>"]
    for i, (a, b, et, ag) in enumerate(sorted(filas, key=lambda f: f[0])):
        x = izq + (a - t0).total_seconds() / total * ancho
        w = max((b - a).total_seconds() / total * ancho, 2)
        y = i * alto + 5
        svg.append(f"<text x='{izq - 8}' y='{y + 14}' text-anchor='end'>{esc(et)}</text>")
        svg.append(f"<rect x='{x:.1f}' y='{y}' width='{w:.1f}' height='{alto - 6}' rx='3' fill='{colores.get(ag, '#888')}'>"
                   f"<title>{esc(et)}: {(b - a).total_seconds():.0f} s</title></rect>")
        svg.append(f"<text x='{x + w + 4:.1f}' y='{y + 14}' class='seg'>{(b - a).total_seconds():.0f}s</text>")
    svg.append(f"<text x='{izq}' y='{len(filas) * alto + 25}' class='seg'>0 s</text>"
               f"<text x='{izq + ancho}' y='{len(filas) * alto + 25}' class='seg' text-anchor='end'>{total:.0f} s</text></svg>")
    return "\n".join(svg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    a = p.parse_args()
    run = Path(a.run)

    uso = cargar(run / "uso.json") or {}
    eventos = jsonl(run / "log_completo.jsonl")
    fin = [e for e in eventos if e["evento"] == "fin"]
    auds = sorted(run.glob("auditoria_v*.json"), key=lambda x: int(re.search(r"(\d+)", x.stem).group(1)))
    ult = cargar(auds[-1]) if auds else None
    informes = sorted(run.glob("informe_v*.md"), key=lambda x: int(re.search(r"(\d+)", x.stem).group(1)))
    hall = cargar(run / "02_hallazgos_contrato.json") or cargar(run / "03_hallazgos_validados.json") or {"tendencias": []}
    validados = cargar(run / "03_hallazgos_validados.json") or {"tendencias": []}
    filtrado = cargar(run / "03_filtrado.json") or {}
    rech = {r["id"]: r for r in filtrado.get("evidencias_rechazadas", [])}
    mec = {m["id"]: m for m in (cargar(run / "03_verificacion" / "mecanica.json") or {}).get("evidencias", [])}
    ver = {v["id"]: v for v in (cargar(run / "03_verificacion_evidencia.json") or {}).get("evidencias", [])}
    conf_final = {t["id"]: t["confianza"]["nivel"] for t in validados["tendencias"]}

    activos = en_curso(run)
    vivo = "orquestador" in activos
    estado = fin[-1]["estado"] if fin else ("EN CURSO" if vivo else (ult["estado"] if ult else "—"))
    if vivo:
        inicio = ts(activos["orquestador"]["ts_inicio"])
        uso = dict(uso, duracion_segundos=(datetime.now() - inicio).total_seconds() if inicio else 0)
    tot = uso.get("total", {})
    tarjetas = [("Estado", estado), ("Score", ult["score_global"] if ult else "—"),
                ("Auditorías", len(auds)), ("Duración", f"{uso.get('duracion_segundos', 0) / 60:.1f} min"),
                ("Tokens entrada", f"{tot.get('input_tokens', 0):,}"), ("Peticiones", tot.get("requests", "—")),
                ("Evidencias válidas", f"{filtrado.get('evidencias_validas', '—')}/{filtrado.get('evidencias_entrada', '—')}"),
                ("Ajustes de confianza", len(filtrado.get("ajustes_confianza", [])))]

    filas_ev = []
    for t in hall["tendencias"]:
        for e in t["evidencias"]:
            m, v, r = mec.get(e["id"], {}), ver.get(e["id"], {}), rech.get(e["id"])
            cif = ", ".join(("✓ " if c["encontrada"] else "✗ ") + esc(c["cifra"]) for c in m.get("cifras", [])) or esc(", ".join(e.get("cifras", [])))
            ext = {True: "✓", False: "✗", None: "—"}[m.get("extracto_encontrado")] if m else "—"
            f = e["fuente"]
            filas_ev.append(
                f"<tr id='{e['id']}' class='{'rech' if r else 'ok'}'><td><b>{e['id']}</b><br>{t['id']}</td>"
                f"<td>{esc(e['afirmacion'])}" + (f"<div class='ext'>«{esc(e['extracto'])}»</div>" if e.get("extracto") else "") + "</td>"
                f"<td>{cif}</td><td>{ext}</td><td>{esc(f.get('tipo', '—'))}</td><td>{esc(f.get('fecha'))}</td>"
                f"<td><a href='{esc(f['url'])}' target='_blank'>{esc(f.get('organizacion'))}</a></td>"
                f"<td>{'<b>RECHAZADA</b><br>' + esc(r['motivo']) if r else '<b>VÁLIDA</b><br>' + esc(v.get('motivo', ''))}</td></tr>")

    filas_t = "".join(
        f"<tr><td>{t['id']}</td><td>{esc(t['nombre'])}</td><td>{esc(t['madurez']['nivel'])}</td><td>{esc(t['impacto']['nivel'])}</td>"
        f"<td>{esc(t['confianza']['nivel'])} → <b>{esc(conf_final.get(t['id'], 'eliminada'))}</b></td></tr>" for t in hall["tendencias"])
    filas_a = "".join(
        f"<tr><td>v{x['version']}</td><td><b>{x['estado']}</b></td><td>{x['score_global']}</td>"
        + "".join(f"<td>{x['puntajes'][c]}</td>" for c in ("exactitud", "calidad_evidencia", "referencias", "profundidad", "claridad", "utilidad"))
        + f"<td>{esc('; '.join(x['rechazos_automaticos'] + x['umbrales_incumplidos']) or '—')}</td></tr>"
        for x in (cargar(f) for f in auds))
    filas_log = "".join(f"<tr><td>{esc(e['ts'][11:19])}</td><td>{esc(e['componente'])}</td><td>{esc(e['evento'])}</td>"
                        f"<td>{esc(e['estado'])}</td><td>{esc(e['detalle'])}</td></tr>" for e in eventos)
    agentes = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v.get('modelo'))}</td><td>{v.get('delegaciones')}</td><td>{v.get('requests')}</td>"
                      f"<td>{v.get('input_tokens', 0):,}</td><td>{v.get('output_tokens', 0):,}</td><td>{v.get('segundos')}</td></tr>"
                      for k, v in uso.get("por_agente", {}).items())

    actividad = ""
    if vivo:
        ult_h = jsonl(run / "herramientas.jsonl")[-15:]
        trabajando = "".join(f"<li><b>{esc(r['etiqueta'])}</b> desde {esc(r['ts_inicio'][11:19])}</li>"
                             for r in activos.values() if r["agente"] != "orquestador") or "<li>Orquestador decidiendo el siguiente paso</li>"
        recientes = "".join(f"<tr><td>{esc(h['ts'][11:19])}</td><td>{esc(h['agente'])}</td><td>{esc(h['herramienta'])}</td>"
                            f"<td>{h['segundos']}</td></tr>" for h in reversed(ult_h))
        actividad = (f"<div class='vivo'>En curso · se actualiza cada 10 s · {datetime.now():%H:%M:%S}</div>"
                     f"<h2>Trabajando ahora</h2><ul>{trabajando}</ul>"
                     f"<h2>Actividad reciente</h2><div class='wrap'><table><tr><th>Hora</th><th>Agente</th><th>Herramienta</th>"
                     f"<th>Segundos</th></tr>{recientes}</table></div>")
    refresco = '<meta http-equiv="refresh" content="10">' if vivo else ""

    doc = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">{refresco}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run {esc(run.name)}</title>
<style>
:root{{--bg:#fff;--fg:#1f2937;--mut:#6b7280;--card:#f3f4f6;--line:#e5e7eb;--ok:#dcfce7;--bad:#fee2e2;--acc:#1f3a5f}}
@media (prefers-color-scheme: dark){{:root{{--bg:#111827;--fg:#e5e7eb;--mut:#9ca3af;--card:#1f2937;--line:#374151;--ok:#14532d;--bad:#7f1d1d;--acc:#93c5fd}}}}
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:24px;max-width:1200px;margin:auto}}
h1{{color:var(--acc);margin-bottom:4px}} h2{{color:var(--acc);border-bottom:2px solid var(--line);padding-bottom:4px;margin-top:36px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}}
.card{{background:var(--card);border-radius:10px;padding:12px}} .card b{{display:block;font-size:1.3em}} .card span{{color:var(--mut);font-size:.85em}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.88em}} td,th{{border:1px solid var(--line);padding:6px;vertical-align:top;text-align:left}}
th{{background:var(--acc);color:#fff}} tr.rech{{background:var(--bad)}} tr.ok td:last-child{{background:var(--ok)}}
.ext{{color:var(--mut);font-style:italic;margin-top:4px}} .nota{{color:var(--mut)}} a.cita{{text-decoration:none;font-weight:600}}
:target{{outline:3px solid #f59e0b}} .gantt{{width:100%;height:auto;font-size:11px}} .gantt text{{fill:var(--fg)}} .seg{{fill:var(--mut)!important}}
.informe{{background:var(--card);border-radius:10px;padding:8px 20px}} table.md td{{background:var(--bg)}}
.vivo{{background:#f59e0b;color:#111;padding:8px 12px;border-radius:8px;font-weight:600;margin:12px 0}}
</style></head><body>
<h1>Run {esc(run.name)}</h1><p class="nota">Modelos: {esc(uso.get('modelos', '—'))} · versión {esc(uso.get('version', 'v1'))}</p>
<div class="cards">{''.join(f"<div class='card'><span>{esc(k)}</span><b>{esc(v)}</b></div>" for k, v in tarjetas)}</div>
{actividad}
<h2>Línea de tiempo</h2><p class="nota">Azul: Scout · rojo: auditor · verde: escritor · gris: scripts. Las barras superpuestas corrieron en paralelo; las claras siguen en curso.</p>
<div class="wrap">{linea_tiempo(run)}</div>
<h2>Consumo por agente</h2><div class="wrap"><table><tr><th>Agente</th><th>Modelo</th><th>Llamadas</th><th>Peticiones</th><th>Tokens entrada</th><th>Tokens salida</th><th>Segundos</th></tr>{agentes}</table></div>
<h2>Tendencias y confianza</h2><div class="wrap"><table><tr><th>ID</th><th>Tendencia</th><th>Madurez</th><th>Impacto</th><th>Confianza (Scout → final)</th></tr>{filas_t}</table></div>
<h2>Visor de evidencia</h2><p class="nota">✓/✗ en cifras y extracto: chequeo mecánico contra el texto descargado de la fuente.</p>
<div class="wrap"><table><tr><th>ID</th><th>Afirmación y extracto</th><th>Cifras</th><th>Extracto</th><th>Tipo</th><th>Fecha</th><th>Fuente</th><th>Veredicto</th></tr>{''.join(filas_ev)}</table></div>
<h2>Auditorías</h2><div class="wrap"><table><tr><th>Versión</th><th>Estado</th><th>Global</th><th>Exact.</th><th>Evid.</th><th>Ref.</th><th>Prof.</th><th>Clar.</th><th>Util.</th><th>Rechazos / umbrales</th></tr>{filas_a}</table></div>
<h2>Informe final ({esc(informes[-1].name) if informes else '—'})</h2><p class="nota">Cada [E#] lleva a su evidencia.</p>
<div class="informe">{md_a_html(informes[-1].read_text(encoding='utf-8')) if informes else '<p>Sin informe.</p>'}</div>
<h2>Registro de eventos</h2><div class="wrap"><table><tr><th>Hora</th><th>Componente</th><th>Evento</th><th>Estado</th><th>Detalle</th></tr>{filas_log}</table></div>
</body></html>"""
    (run / "reporte_run.html").write_text(doc, encoding="utf-8")
    print(f"Reporte: {run / 'reporte_run.html'}")


if __name__ == "__main__":
    main()
