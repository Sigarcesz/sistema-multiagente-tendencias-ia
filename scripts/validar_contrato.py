#!/usr/bin/env python3
"""Compuerta de contrato (orquestador) sobre la salida del Trend Scout.

No juzga la calidad ni la veracidad del contenido (eso es del auditor). Solo:
  1. Verifica que la salida cumpla el contrato estructural (campos, IDs, enums, fuentes).
  2. Detecta invasión de responsabilidades: claves o frases prescriptivas
     (recomendaciones, estrategias, hojas de ruta). Las ELIMINA y las registra.

Uso:
  python3 scripts/validar_contrato.py --entrada runs/<id>/01_hallazgos_scout.json \
      --salida runs/<id>/02_hallazgos_contrato.json --reporte runs/<id>/02_contrato.json

Código de salida: 0 = OK, 1 = SANEADO (hubo violaciones, se corrigieron), 2 = ERROR_ESTRUCTURA.
"""
import argparse
import copy
import json
import re
import sys
import unicodedata

CLAVES_PROHIBIDAS = {
    "recomendaciones", "recomendacion", "recomendación", "estrategia", "estrategias",
    "acciones_sugeridas", "acciones", "hoja_de_ruta", "roadmap", "conclusiones",
    "plan_de_accion", "sugerencias",
}

# Patrones sobre texto normalizado (minúsculas, sin tildes)
PATRONES_PRESCRIPTIVOS = [
    r"\brecomend\w*",
    r"\bse sugiere\b", r"\bsugerimos\b", r"\bsugiere[n]? (que|adoptar|invertir|implementar)\b",
    r"\b(la empresa|las empresas|horizonte digital|la organizacion|las organizaciones|"
    r"la alta direccion|la direccion|los directivos)\s+(deber\w*|tendr\w*|necesit\w*|conviene)",
    r"\bdeber(ia|ian|a|an)\s+(adoptar|invertir|implementar|priorizar|evaluar|incorporar|considerar|apostar)",
    r"\bes (recomendable|aconsejable|conveniente|prioritario)\b",
    r"\binvertir en\b", r"\bhoja de ruta\b", r"\bse aconseja\b",
]

NIVELES = {
    "impacto": {"alto", "medio", "bajo"},
    "madurez": {"emergente", "en_adopcion", "consolidada"},
    "confianza": {"alta", "media", "baja"},
}
CAMPOS_TEXTO = ["descripcion"]
RE_FECHA = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
RE_ORACIONES = re.compile(r"(?<=[.!?])\s+")


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def es_prescriptiva(oracion: str) -> bool:
    n = normalizar(oracion)
    return any(re.search(p, n) for p in PATRONES_PRESCRIPTIVOS)


def sanear_texto(texto: str, ubicacion: str, violaciones: list) -> str:
    if not isinstance(texto, str):
        return texto
    conservadas = []
    for o in RE_ORACIONES.split(texto):
        if es_prescriptiva(o):
            violaciones.append({
                "tipo": "invasion_responsabilidad", "subtipo": "frase_prescriptiva",
                "ubicacion": ubicacion, "contenido_eliminado": o.strip(),
            })
        else:
            conservadas.append(o)
    return " ".join(conservadas).strip()


def quitar_claves(obj, ruta: str, violaciones: list):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if normalizar(k) in {normalizar(c) for c in CLAVES_PROHIBIDAS}:
                violaciones.append({
                    "tipo": "invasion_responsabilidad", "subtipo": "campo_prohibido",
                    "ubicacion": f"{ruta}.{k}",
                    "contenido_eliminado": json.dumps(obj[k], ensure_ascii=False)[:500],
                })
                del obj[k]
            else:
                quitar_claves(obj[k], f"{ruta}.{k}", violaciones)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            quitar_claves(x, f"{ruta}[{i}]", violaciones)


def validar(data: dict, errores: list, violaciones: list) -> dict:
    data = copy.deepcopy(data)
    quitar_claves(data, "$", violaciones)

    for campo in ("tema", "fecha_investigacion", "tendencias"):
        if campo not in data:
            errores.append(f"Falta el campo raíz '{campo}'")
    tendencias = data.get("tendencias", [])
    if not isinstance(tendencias, list) or not tendencias:
        errores.append("'tendencias' debe ser una lista no vacía")
        return data

    ids_t, ids_e = set(), set()
    for i, t in enumerate(tendencias):
        ub = f"tendencias[{i}]"
        tid = t.get("id")
        if not tid or not re.fullmatch(r"T\d+", str(tid)):
            errores.append(f"{ub}: id inválido '{tid}' (formato T1, T2…)")
        elif tid in ids_t:
            errores.append(f"{ub}: id duplicado {tid}")
        ids_t.add(tid)
        for campo in ("nombre", "descripcion"):
            if not str(t.get(campo, "")).strip():
                errores.append(f"{ub} ({tid}): falta '{campo}'")
        for dim, valores in NIVELES.items():
            d = t.get(dim)
            if not isinstance(d, dict) or d.get("nivel") not in valores:
                errores.append(f"{ub} ({tid}): '{dim}.nivel' debe ser uno de {sorted(valores)}")
            elif not str(d.get("justificacion", "")).strip():
                errores.append(f"{ub} ({tid}): falta '{dim}.justificacion'")
            else:
                d["justificacion"] = sanear_texto(d["justificacion"], f"{tid}.{dim}.justificacion", violaciones)
        for campo in CAMPOS_TEXTO:
            if campo in t:
                t[campo] = sanear_texto(t[campo], f"{tid}.{campo}", violaciones)

        evs = t.get("evidencias", [])
        if not isinstance(evs, list) or not evs:
            errores.append(f"{ub} ({tid}): necesita al menos una evidencia")
            continue
        for j, e in enumerate(evs):
            ue = f"{tid}.evidencias[{j}]"
            eid = e.get("id")
            if not eid or not re.fullmatch(r"E\d+", str(eid)):
                errores.append(f"{ue}: id inválido '{eid}' (formato E1, E2…)")
            elif eid in ids_e:
                errores.append(f"{ue}: id de evidencia duplicado {eid} (deben ser únicos en todo el documento)")
            ids_e.add(eid)
            if not str(e.get("afirmacion", "")).strip():
                errores.append(f"{ue} ({eid}): falta 'afirmacion'")
            else:
                e["afirmacion"] = sanear_texto(e["afirmacion"], f"{eid}.afirmacion", violaciones)
            if "cifras" in e and not isinstance(e["cifras"], list):
                errores.append(f"{ue} ({eid}): 'cifras' debe ser una lista")
            f = e.get("fuente")
            if not isinstance(f, dict):
                errores.append(f"{ue} ({eid}): falta 'fuente'")
                continue
            for campo in ("titulo", "organizacion", "fecha", "url"):
                if not str(f.get(campo, "")).strip():
                    errores.append(f"{ue} ({eid}): falta 'fuente.{campo}'")
            if f.get("url") and not str(f["url"]).startswith(("http://", "https://")):
                errores.append(f"{ue} ({eid}): 'fuente.url' no es una URL http(s)")
            if f.get("fecha") and not RE_FECHA.match(str(f["fecha"])):
                errores.append(f"{ue} ({eid}): 'fuente.fecha' debe ser AAAA, AAAA-MM o AAAA-MM-DD")
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--entrada", required=True)
    p.add_argument("--salida", required=True)
    p.add_argument("--reporte", required=True)
    a = p.parse_args()

    try:
        data = json.load(open(a.entrada, encoding="utf-8"))
    except json.JSONDecodeError as ex:
        rep = {"estado": "ERROR_ESTRUCTURA", "errores": [f"JSON inválido: {ex}"], "violaciones": []}
        json.dump(rep, open(a.reporte, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(json.dumps(rep, ensure_ascii=False))
        sys.exit(2)

    errores, violaciones = [], []
    limpio = validar(data, errores, violaciones)
    estado = "ERROR_ESTRUCTURA" if errores else ("SANEADO" if violaciones else "OK")
    rep = {
        "estado": estado,
        "errores": errores,
        "violaciones": violaciones,
        "tendencias": len(limpio.get("tendencias", [])),
        "evidencias": sum(len(t.get("evidencias", [])) for t in limpio.get("tendencias", [])),
    }
    json.dump(limpio, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(rep, open(a.reporte, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: rep[k] for k in ("estado", "tendencias", "evidencias")} |
                     {"n_errores": len(errores), "n_violaciones": len(violaciones)}, ensure_ascii=False))
    sys.exit({"OK": 0, "SANEADO": 1, "ERROR_ESTRUCTURA": 2}[estado])


if __name__ == "__main__":
    main()
