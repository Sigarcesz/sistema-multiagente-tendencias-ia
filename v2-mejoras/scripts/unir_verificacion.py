#!/usr/bin/env python3
"""Une la verificación de evidencia hecha en paralelo y produce los hallazgos validados.

Reglas por evidencia (fail-closed; se aplican en este orden):
  1. URL inaccesible (dominio inexistente, 404/410)             -> RECHAZADA
  2. Página legible pero alguna cifra declarada no aparece en ella -> RECHAZADA (mecánico)
  3. Sin veredicto del auditor                                    -> RECHAZADA
  4. Veredicto del auditor distinto de VERIFICADA                 -> RECHAZADA
  5. Página no legible y el auditor no la confirmó por otra vía   -> RECHAZADA

Después, por tendencia:
  - sin evidencias válidas                         -> se elimina;
  - confianza 'alta' con menos de 2 evidencias     -> baja a 'media';
  - todas sus evidencias son de proveedores        -> confianza máxima 'media';
  - todas sus evidencias tienen más de 24 meses    -> confianza máxima 'media'.
Cada ajuste queda registrado: la confianza que ve el escritor ya es coherente con lo
que sobrevivió a la verificación.

Uso:
  python scripts/unir_verificacion.py --run runs/<id>
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validar_contrato import MESES_RECENCIA, meses_entre  # noqa: E402



def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--hallazgos", default="02_hallazgos_contrato.json")
    a = p.parse_args()
    run = Path(a.run)
    h = json.load(open(run / a.hallazgos, encoding="utf-8"))
    mec = {m["id"]: m for m in json.load(open(run / "03_verificacion" / "mecanica.json", encoding="utf-8"))["evidencias"]}

    veredictos, archivos_faltantes = {}, []
    for t in h["tendencias"]:
        f = run / "03_verificacion" / f"veredictos_{t['id']}.json"
        if not f.exists():
            archivos_faltantes.append(t["id"])
            continue
        try:
            for v in json.load(open(f, encoding="utf-8")).get("evidencias", []):
                veredictos[v["id"]] = v
        except (json.JSONDecodeError, KeyError):
            archivos_faltantes.append(f"{t['id']} (archivo inválido)")

    salida = copy.deepcopy(h)
    rechazadas, eliminadas, ajustes, nuevas = [], [], [], []
    for t in salida["tendencias"]:
        validas = []
        for e in t["evidencias"]:
            m, v = mec.get(e["id"], {}), veredictos.get(e["id"])
            motivo = None
            if m.get("estado_fuente") == "inaccesible":
                motivo = f"URL inaccesible ({m.get('http') or m.get('error')})"
            elif m.get("cifras_no_encontradas"):
                motivo = f"cifras que no aparecen en la página: {m['cifras_no_encontradas']} (chequeo mecánico)"
            elif not v:
                motivo = "sin veredicto del auditor (fail-closed)"
            elif v.get("veredicto") != "VERIFICADA":
                motivo = v.get("motivo", "rechazada por el auditor")
            elif m.get("estado_fuente") != "legible" and not v.get("confirmada_por_otra_via"):
                motivo = "la página no se pudo leer y no se confirmó por otra vía"
            if motivo:
                rechazadas.append({"id": e["id"], "tendencia": t["id"], "motivo": motivo, "url": e["fuente"]["url"],
                                   "origen": "mecanico" if "mecánico" in motivo or "URL" in motivo else "auditor"})
            else:
                validas.append(e)
        if not validas:
            eliminadas.append({"id": t["id"], "nombre": t["nombre"]})
            continue
        t["evidencias"] = validas

        razones = []
        fi = h.get("fecha_investigacion", "")
        antiguedad = [meses_entre(e["fuente"].get("fecha", ""), fi) for e in validas]
        if len(validas) < 2:
            razones.append("menos de 2 evidencias válidas")
        if all(e["fuente"].get("tipo") == "proveedor" for e in validas):
            razones.append("solo fuentes de proveedores")
        if fi and all(x is not None and x > MESES_RECENCIA for x in antiguedad):
            razones.append(f"todas las fuentes tienen más de {MESES_RECENCIA} meses")
        nivel = "media" if razones and t["confianza"]["nivel"] == "alta" else t["confianza"]["nivel"]
        if nivel != t["confianza"]["nivel"]:
            ajustes.append({"tendencia": t["id"], "de": t["confianza"]["nivel"], "a": nivel, "razones": razones})
            t["confianza"] = {"nivel": nivel, "justificacion": t["confianza"]["justificacion"]
                              + f" [Ajustada en verificación a '{nivel}': {'; '.join(razones)}.]"}
        nuevas.append(t)

    salida["tendencias"] = nuevas
    salida["verificacion"] = {"evidencias_rechazadas": [r["id"] for r in rechazadas], "ajustes_confianza": ajustes}
    rep = {
        "evidencias_entrada": sum(len(t["evidencias"]) for t in h["tendencias"]),
        "evidencias_validas": sum(len(t["evidencias"]) for t in nuevas),
        "evidencias_rechazadas": rechazadas,
        "tendencias_entrada": len(h["tendencias"]),
        "tendencias_validas": len(nuevas),
        "tendencias_eliminadas": eliminadas,
        "ajustes_confianza": ajustes,
        "veredictos_faltantes": archivos_faltantes,
        "tipos_fuente_validas": {},
    }
    for t in nuevas:
        for e in t["evidencias"]:
            tp = e["fuente"].get("tipo", "sin_tipo")
            rep["tipos_fuente_validas"][tp] = rep["tipos_fuente_validas"].get(tp, 0) + 1
    json.dump(salida, open(run / "03_hallazgos_validados.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(rep, open(run / "03_filtrado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump({"evidencias": list(veredictos.values())}, open(run / "03_verificacion_evidencia.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
