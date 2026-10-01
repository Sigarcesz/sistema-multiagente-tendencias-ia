#!/usr/bin/env python3
"""Verificación mecánica del borrador contra los hallazgos validados.

Detecta, sin depender del juicio del modelo:
  - estructura: las 11 secciones obligatorias, en orden;
  - cifras no trazables: números del informe que no aparecen en los hallazgos (caso 4);
  - citas inexistentes: [E#] que no existe en los hallazgos validados;
  - tendencias inventadas: [T#] / '### T#' fuera de los hallazgos;
  - recomendaciones sin sus cuatro vínculos: evidencia, riesgo, oportunidad, indicador (caso 5);
  - referencias faltantes: evidencia citada cuya URL no aparece en la sección 11.

Uso:
  python3 verificar_informe.py --informe runs/<id>/informe_v1.md \
      --hallazgos runs/<id>/03_hallazgos_validados.json \
      --salida runs/<id>/verificacion_informe_v1.json
"""
import argparse
import json
import re
import unicodedata

SECCIONES = [
    "resumen ejecutivo", "objetivo", "metodologia", "tendencias analizadas",
    "impacto empresarial", "riesgos", "oportunidades", "recomendaciones",
    "hoja de ruta", "conclusiones", "referencias",
]
RE_ID = r"(?:RG|OP|E|T|R|C)\d+"
RE_HEADING = re.compile(r"^##\s+(\d+)\.\s*(.+?)\s*$")
RE_NUM = re.compile(r"(?<![\w])(\d+(?:[.,]\d+)*)(\s*(?:%|por ciento|puntos porcentuales|pp\b))?")
RE_UNIDAD_TIEMPO = re.compile(r"^\s*(?:-|–|a)?\s*\d*\s*(meses|mes|años|año|semanas|semana|trimestres|trimestre|días|dias)\b", re.I)
RE_ORACION = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡\[(])")


def norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def valor(tok: str) -> float:
    """'1.200' -> 1200 ; '2,5' -> 2.5 ; '1,200' -> 1200 ; '35' -> 35"""
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", tok):
        return float(re.sub(r"[.,]", "", tok))
    return float(tok.replace(",", "."))


def numeros(texto: str):
    """Devuelve [(valor, es_porcentaje, token, posicion_final)]"""
    out = []
    for m in RE_NUM.finditer(texto):
        tok = m.group(1)
        try:
            v = valor(tok)
        except ValueError:
            continue
        out.append((v, bool(m.group(2)), m.group(0).strip(), m.end()))
    return out


def es_excluido(v: float, pct: bool, texto: str, fin: int, tok: str) -> str | None:
    if not pct and float(v).is_integer() and 1990 <= v <= 2100 and re.fullmatch(r"\d{4}", tok):
        return "año"
    if not pct and v <= 60 and RE_UNIDAD_TIEMPO.match(texto[fin:fin + 25]):
        return "horizonte_temporal"
    return None


def limpiar_ids(linea: str) -> str:
    linea = re.sub(rf"\b{RE_ID}\b", " ", linea)
    linea = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", " ", linea)
    linea = re.sub(r"\b(fase|etapa|horizonte|ola|nivel|seccion|sección)\s+\d+\b", " ", linea, flags=re.I)
    linea = re.sub(r"https?://\S+", " ", linea)
    return linea


def secciones(md: str):
    lineas = md.splitlines()
    idx = []
    for i, l in enumerate(lineas):
        m = RE_HEADING.match(l)
        if m:
            idx.append((i, int(m.group(1)), norm(m.group(2))))
    out = {}
    for k, (i, n, titulo) in enumerate(idx):
        fin = idx[k + 1][0] if k + 1 < len(idx) else len(lineas)
        out[n] = {"titulo": titulo, "inicio": i, "lineas": lineas[i + 1:fin]}
    return out, idx


def numeros_permitidos(h: dict) -> set:
    textos = [h.get("tema", "")]
    for t in h["tendencias"]:
        textos += [t.get("descripcion", "")]
        for dim in ("impacto", "madurez", "confianza"):
            textos.append(t.get(dim, {}).get("justificacion", ""))
        for e in t["evidencias"]:
            textos.append(e.get("afirmacion", ""))
            textos += [str(c) for c in e.get("cifras", [])]
    permitidos = set()
    for tx in textos:
        for v, pct, _, _ in numeros(limpiar_ids(tx)):
            permitidos.add((round(v, 4), pct))
            permitidos.add((round(v, 4), None))
    return permitidos


def numeros_de_evidencia(e: dict) -> set:
    s = set()
    for tx in [e.get("afirmacion", "")] + [str(c) for c in e.get("cifras", [])]:
        for v, _, _, _ in numeros(limpiar_ids(tx)):
            s.add(round(v, 4))
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--informe", required=True)
    p.add_argument("--hallazgos", required=True)
    p.add_argument("--salida", required=True)
    a = p.parse_args()

    md = open(a.informe, encoding="utf-8").read()
    h = json.load(open(a.hallazgos, encoding="utf-8"))
    evid = {e["id"]: e for t in h["tendencias"] for e in t["evidencias"]}
    ids_t = {t["id"] for t in h["tendencias"]}
    permitidos = numeros_permitidos(h)
    nums_ev = {eid: numeros_de_evidencia(e) for eid, e in evid.items()}

    secs, idx = secciones(md)
    r = {"estructura": {}, "cifras_no_trazables": [], "cifras_sin_cita_correcta": [],
         "conteos_numericos": [], "citas_inexistentes": [], "tendencias_inventadas": [],
         "tendencias_omitidas": [], "recomendaciones_invalidas": [], "referencias_faltantes": [],
         "recomendaciones_validas": []}

    # 1. Estructura
    encontradas = [t for _, _, t in idx]
    faltan = [s for s in SECCIONES if not any(s in e for e in encontradas)]
    orden_ok = [n for _, n, _ in idx] == list(range(1, len(idx) + 1))
    r["estructura"] = {"secciones_encontradas": len(idx), "faltantes": faltan,
                       "orden_correcto": orden_ok and not faltan and len(idx) == 11}

    n_ref = next((n for n, s in secs.items() if "referencias" in s["titulo"]), None)

    # 2. Cifras y citas (todo el cuerpo salvo encabezados y Referencias)
    citadas = set()
    for n, s in secs.items():
        if n == n_ref:
            continue
        for k, linea in enumerate(s["lineas"]):
            if linea.lstrip().startswith("#"):
                if "tendencias" in s["titulo"]:
                    for tid in re.findall(r"\bT\d+\b", linea):
                        if tid not in ids_t:
                            r["tendencias_inventadas"].append({"id": tid, "linea": linea.strip()})
                continue
            for eid in re.findall(r"\bE\d+\b", linea):
                citadas.add(eid)
                if eid not in evid:
                    r["citas_inexistentes"].append({"id": eid, "seccion": n, "texto": linea.strip()[:200]})
            for tid in re.findall(r"\[T\d+\]|\bT\d+\b", linea):
                tid = tid.strip("[]")
                if tid not in ids_t:
                    r["tendencias_inventadas"].append({"id": tid, "linea": linea.strip()[:200]})
            for oracion in RE_ORACION.split(linea):
                cit = set(re.findall(r"\bE\d+\b", oracion)) or set(re.findall(r"\bE\d+\b", linea))
                limpio = limpiar_ids(oracion)
                for v, pct, tok, fin in numeros(limpio):
                    motivo = es_excluido(v, pct, limpio, fin, tok.split()[0] if tok else tok)
                    if motivo:
                        continue
                    item = {"cifra": tok, "seccion": n, "texto": oracion.strip()[:240]}
                    trazable = (round(v, 4), pct) in permitidos or (round(v, 4), None) in permitidos and not pct
                    if not trazable:
                        if not pct and float(v).is_integer() and v <= 12:
                            r["conteos_numericos"].append(item)   # advertencia, no bloqueante
                        else:
                            r["cifras_no_trazables"].append(item)
                    elif not any(round(v, 4) in nums_ev.get(e, set()) for e in cit):
                        if not (not pct and float(v).is_integer() and v <= 12):
                            r["cifras_sin_cita_correcta"].append(item | {"citas_en_oracion": sorted(cit)})

    sec_t = next((s for s in secs.values() if "tendencias analizadas" in s["titulo"]), None)
    if sec_t:
        texto_t = "\n".join(sec_t["lineas"])
        r["tendencias_omitidas"] = sorted(t for t in ids_t if not re.search(rf"\b{t}\b", texto_t))

    # 3. Recomendaciones
    def ids_en(sec_nombre, patron):
        s = next((s for s in secs.values() if sec_nombre in s["titulo"]), None)
        return set(re.findall(patron, "\n".join(s["lineas"]))) if s else set()
    rg_ids = ids_en("riesgos", r"\bRG\d+\b")
    op_ids = ids_en("oportunidades", r"\bOP\d+\b")
    sec_r = next((s for s in secs.values() if "recomendaciones" in s["titulo"]), None)
    if not sec_r:
        r["recomendaciones_invalidas"].append({"id": None, "problemas": ["no existe la sección Recomendaciones"]})
    else:
        bloques, actual = [], None
        for l in sec_r["lineas"]:
            m = re.match(r"^###\s*(R\d+)?\.?\s*(.*)$", l)
            if m:
                actual = {"id": m.group(1), "titulo": m.group(2).strip(), "lineas": []}
                bloques.append(actual)
            elif actual:
                actual["lineas"].append(l)
        if not bloques:
            r["recomendaciones_invalidas"].append({"id": None, "problemas": ["no hay recomendaciones con formato '### R#.'"]})
        for b in bloques:
            campos = {}
            for l in b["lineas"]:
                ln = norm(l.replace("*", ""))
                for c in ("evidencia", "riesgo", "oportunidad", "indicador"):
                    if re.match(rf"^\s*[-]?\s*{c}s?\s*:", ln):
                        campos[c] = l.split(":", 1)[1] if ":" in l else ""
            prob = []
            if not b["id"]:
                prob.append("encabezado sin ID R#")
            ev = re.findall(r"\bE\d+\b", campos.get("evidencia", ""))
            if not ev:
                prob.append("sin evidencia vinculada")
            elif any(e not in evid for e in ev):
                prob.append(f"evidencia inexistente: {[e for e in ev if e not in evid]}")
            rg = re.findall(r"\bRG\d+\b", campos.get("riesgo", ""))
            if not rg:
                prob.append("sin riesgo vinculado (RG#)")
            elif any(x not in rg_ids for x in rg):
                prob.append(f"riesgo no definido en sección Riesgos: {[x for x in rg if x not in rg_ids]}")
            op = re.findall(r"\bOP\d+\b", campos.get("oportunidad", ""))
            if not op:
                prob.append("sin oportunidad vinculada (OP#)")
            elif any(x not in op_ids for x in op):
                prob.append(f"oportunidad no definida en sección Oportunidades: {[x for x in op if x not in op_ids]}")
            if len(campos.get("indicador", "").split()) < 4:
                prob.append("sin indicador de seguimiento (mín. 4 palabras)")
            if prob:
                r["recomendaciones_invalidas"].append({"id": b["id"], "titulo": b["titulo"], "problemas": prob})
            else:
                r["recomendaciones_validas"].append(b["id"])

    # 4. Referencias
    ref_txt = "\n".join(secs[n_ref]["lineas"]) if n_ref else ""
    for eid in sorted(citadas & set(evid)):
        if evid[eid]["fuente"]["url"] not in ref_txt:
            r["referencias_faltantes"].append({"id": eid, "url": evid[eid]["fuente"]["url"]})

    bloqueantes = []
    if not r["estructura"]["orden_correcto"]:
        bloqueantes.append("ESTRUCTURA")
    if r["cifras_no_trazables"]:
        bloqueantes.append("CIFRAS_NO_TRAZABLES")
    if r["citas_inexistentes"]:
        bloqueantes.append("CITAS_INEXISTENTES")
    if r["tendencias_inventadas"]:
        bloqueantes.append("TENDENCIAS_INVENTADAS")
    if r["recomendaciones_invalidas"]:
        bloqueantes.append("RECOMENDACIONES_INJUSTIFICADAS")
    r["bloqueantes"] = bloqueantes
    r["n_tendencias_hallazgos"] = len(ids_t)
    r["resumen"] = {k: len(v) for k, v in r.items() if isinstance(v, list) and k != "bloqueantes"}

    json.dump(r, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"bloqueantes": bloqueantes, **r["resumen"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
