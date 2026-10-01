#!/usr/bin/env python3
"""Combina el juicio del auditor con la verificación mecánica y decide el estado.

El auditor (modelo) asigna puntajes 0-100 por criterio y lista correcciones.
Este script aplica de forma determinista:
  - topes por hallazgos mecánicos (una cifra inventada no puede tener exactitud 95);
  - el score global ponderado;
  - los umbrales;
  - los rechazos automáticos.
Así la decisión APROBADO/RECHAZADO no depende de que el modelo "se acuerde" de las reglas.

Uso:
  python3 decidir_estado.py --borrador runs/<id>/auditoria_borrador_v1.json \
      --verificacion runs/<id>/verificacion_informe_v1.json --version 1 \
      --salida runs/<id>/auditoria_v1.json
"""
import argparse
import json

PESOS = {
    "exactitud": 0.25,
    "calidad_evidencia": 0.15,
    "referencias": 0.15,
    "profundidad": 0.15,
    "claridad": 0.10,
    "utilidad": 0.20,
}
UMBRALES = {"exactitud": 90, "referencias": 90, "profundidad": 70, "global": 85}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--borrador", required=True)
    p.add_argument("--verificacion", required=True)
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--salida", required=True)
    a = p.parse_args()

    b = json.load(open(a.borrador, encoding="utf-8"))
    v = json.load(open(a.verificacion, encoding="utf-8"))

    faltan = [c for c in PESOS if c not in b.get("puntajes", {})]
    if faltan:
        raise SystemExit(f"ERROR: el borrador no trae puntajes para {faltan}")
    puntajes = {c: max(0, min(100, int(b["puntajes"][c]))) for c in PESOS}
    topes, rechazos, correcciones_mec = [], [], []

    def tope(criterio, maximo, motivo):
        if puntajes[criterio] > maximo:
            topes.append({"criterio": criterio, "de": puntajes[criterio], "a": maximo, "motivo": motivo})
            puntajes[criterio] = maximo

    if v["cifras_no_trazables"]:
        tope("exactitud", 60, f"{len(v['cifras_no_trazables'])} cifra(s) no trazables a los hallazgos")
        rechazos.append("R-EXACTITUD: cifras que no aparecen en los hallazgos")
        for c in v["cifras_no_trazables"]:
            correcciones_mec.append({"criterio": "exactitud", "ubicacion": f"Sección {c['seccion']}",
                                     "problema": f"La cifra '{c['cifra']}' no aparece en los hallazgos: «{c['texto']}»",
                                     "accion_requerida": "Eliminar la cifra o reemplazarla por la cifra exacta de una evidencia citada."})
    if v["citas_inexistentes"]:
        tope("referencias", 50, "citas a evidencias inexistentes o rechazadas")
        rechazos.append("R-REFERENCIAS: citas a evidencias que no existen en los hallazgos validados")
        for c in v["citas_inexistentes"]:
            correcciones_mec.append({"criterio": "referencias", "ubicacion": f"Sección {c['seccion']}",
                                     "problema": f"Se cita {c['id']}, que no existe en los hallazgos validados.",
                                     "accion_requerida": "Eliminar la afirmación o citar una evidencia existente que la respalde."})
    if v["tendencias_inventadas"]:
        tope("exactitud", 50, "tendencias que no están en los hallazgos")
        rechazos.append("R-EXACTITUD: tendencias inventadas")
    if v["recomendaciones_invalidas"]:
        tope("utilidad", 60, "recomendaciones sin evidencia, riesgo, oportunidad o indicador")
        rechazos.append("R-RECOMENDACION: recomendaciones injustificadas")
        for rr in v["recomendaciones_invalidas"]:
            correcciones_mec.append({"criterio": "utilidad", "ubicacion": f"Sección 8, {rr.get('id') or 'sin ID'}",
                                     "problema": "; ".join(rr["problemas"]),
                                     "accion_requerida": "Vincular la recomendación a evidencia [E#], riesgo RG#, oportunidad OP# e indicador, o eliminarla."})
    if not v["estructura"]["orden_correcto"]:
        tope("claridad", 60, "estructura obligatoria incompleta o desordenada")
        rechazos.append("R-ESTRUCTURA: faltan secciones obligatorias o el orden es incorrecto")
        correcciones_mec.append({"criterio": "claridad", "ubicacion": "Documento",
                                 "problema": f"Secciones faltantes: {v['estructura']['faltantes']}",
                                 "accion_requerida": "Respetar las 11 secciones obligatorias en orden."})
    if v["referencias_faltantes"]:
        tope("referencias", 80, "evidencias citadas sin entrada en Referencias")
        for c in v["referencias_faltantes"]:
            correcciones_mec.append({"criterio": "referencias", "ubicacion": "Sección 11",
                                     "problema": f"{c['id']} se cita pero su URL no aparece en Referencias.",
                                     "accion_requerida": f"Agregar la referencia de {c['id']} ({c['url']})."})
    if v["cifras_sin_cita_correcta"]:
        tope("referencias", 85, "cifras atribuidas a una evidencia que no las contiene")
        for c in v["cifras_sin_cita_correcta"]:
            correcciones_mec.append({"criterio": "referencias", "ubicacion": f"Sección {c['seccion']}",
                                     "problema": f"La cifra '{c['cifra']}' no corresponde a las evidencias citadas {c['citas_en_oracion']}.",
                                     "accion_requerida": "Citar la evidencia que contiene esa cifra."})

    if v.get("n_tendencias_hallazgos", 99) < 3:
        tope("profundidad", 50, f"solo {v['n_tendencias_hallazgos']} tendencia(s) respaldadas; el mínimo es 3")
        correcciones_mec.append({"criterio": "profundidad", "ubicacion": "Documento",
                                 "problema": "El informe cubre menos de 3 tendencias respaldadas por evidencia.",
                                 "accion_requerida": "No corregible por el escritor: requiere nueva investigación del Trend Scout.",
                                 "corregible_por_escritor": False})

    for bl in b.get("bloqueantes_auditor", []):
        rechazos.append(f"R-AUDITOR: {bl}")

    score_global = round(sum(puntajes[c] * w for c, w in PESOS.items()), 1)
    incumplidos = [f"{c} {puntajes[c]} < {u}" for c, u in UMBRALES.items() if c != "global" and puntajes[c] < u]
    if score_global < UMBRALES["global"]:
        incumplidos.append(f"global {score_global} < {UMBRALES['global']}")
    estado = "APROBADO" if not rechazos and not incumplidos else "RECHAZADO"

    correcciones = []
    for c in correcciones_mec + b.get("correcciones", []):
        correcciones.append(c)
    # prioridad: rechazos automáticos primero, luego por criterio con peso
    orden = {"exactitud": 0, "referencias": 1, "utilidad": 2, "calidad_evidencia": 3, "profundidad": 4, "claridad": 5}
    correcciones.sort(key=lambda c: (orden.get(c.get("criterio"), 9), c.get("prioridad", 9)))
    for i, c in enumerate(correcciones, 1):
        c["id"] = f"C{i}"
        c["prioridad"] = i

    salida = {
        "version": a.version,
        "estado": estado,
        "score_global": score_global,
        "puntajes": puntajes,
        "pesos": PESOS,
        "umbrales": UMBRALES,
        "umbrales_incumplidos": incumplidos,
        "rechazos_automaticos": rechazos,
        "topes_aplicados": topes,
        "hallazgos_auditor": b.get("hallazgos", []),
        "correcciones": correcciones if estado == "RECHAZADO" else [],
        "observaciones_menores": correcciones if estado == "APROBADO" else [],
    }
    json.dump(salida, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"estado": estado, "score_global": score_global, "puntajes": puntajes,
                      "rechazos_automaticos": rechazos, "umbrales_incumplidos": incumplidos,
                      "n_correcciones": len(salida["correcciones"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
