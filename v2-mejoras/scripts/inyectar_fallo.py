#!/usr/bin/env python3
"""Prepara un run de prueba inyectando un fallo controlado sobre un run real ya aprobado.

Los casos 2-7 no ocurren espontáneamente: hay que provocarlos. Este script toma los
artefactos REALES de un run base (caso 1) y crea una carpeta nueva con UN fallo inyectado
más un manifiesto prueba.json que le dice al orquestador qué etapa reemplazar.

Uso:
  python3 scripts/inyectar_fallo.py --base runs/<run_caso1> --caso 4
  -> crea runs/<run_caso1>_caso4/ con los artefactos y prueba.json

Casos:
  2  fuente inexistente en la salida del Scout          -> se inyecta en 01_hallazgos_scout.json
  3  el Scout agrega recomendaciones estratégicas        -> se inyecta en 01_hallazgos_scout.json
  4  el escritor agrega una cifra que no está en hallazgos -> se inyecta en informe_v1.md
  5  recomendación de inversión sin justificación       -> se inyecta en informe_v1.md
  6  hallazgos insuficientes: no puede alcanzar umbrales -> se inyecta en 03_hallazgos_validados.json
  7  el escritor cita una evidencia que no existe        -> se inyecta en informe_v1.md
"""
import argparse
import copy
import json
import re
import shutil
from pathlib import Path


def cargar(p):
    return json.load(open(p, encoding="utf-8"))


def guardar(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def informe_aprobado(base: Path) -> Path:
    candidatos = []
    for aud in base.glob("auditoria_v*.json"):
        m = re.search(r"_v(\d+)\.json$", aud.name)
        if m and cargar(aud).get("estado") == "APROBADO":
            candidatos.append(int(m.group(1)))
    if not candidatos:
        raise SystemExit(f"El run base {base} no tiene un informe APROBADO. Ejecuta primero el caso 1.")
    return base / f"informe_v{max(candidatos)}.md"


def siguiente_id(h, prefijo):
    ids = [int(e["id"][1:]) for t in h["tendencias"] for e in t["evidencias"]] if prefijo == "E" else \
          [int(t["id"][1:]) for t in h["tendencias"]]
    return f"{prefijo}{max(ids) + 1}"


def insertar_en_seccion(md: str, numero: int, texto: str, al_final=False) -> str:
    lineas = md.splitlines()
    ini = next(i for i, l in enumerate(lineas) if re.match(rf"^##\s+{numero}\.", l))
    fin = next((i for i in range(ini + 1, len(lineas)) if re.match(r"^##\s+\d+\.", lineas[i])), len(lineas))
    if al_final:
        pos = fin
    else:
        pos = next((i for i in range(ini + 1, fin) if lineas[i].strip() == "" and i > ini + 1), fin)
    return "\n".join(lineas[:pos] + ["", texto, ""] + lineas[pos:]) + "\n"


def numero_libre(h: dict) -> str:
    texto = json.dumps(h, ensure_ascii=False)
    for cand in ("73,4", "68,2", "81,7", "57,9"):
        if cand not in texto and cand.replace(",", ".") not in texto:
            return cand
    return "91,3"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--caso", type=int, required=True, choices=[2, 3, 4, 5, 6, 7])
    a = p.parse_args()

    base = Path(a.base)
    dest = Path(f"{base}_caso{a.caso}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    scout = cargar(base / "01_hallazgos_scout.json")
    validados = cargar(base / "03_hallazgos_validados.json")
    manifiesto = {"caso": a.caso, "run_base": base.name, "sin_reinvestigacion": True}
    if a.caso in (2, 3) and (base / "fuentes_cache").exists():
        # v2: reutiliza las páginas ya descargadas en el run base (no se rehace trabajo)
        shutil.copytree(base / "fuentes_cache", dest / "fuentes_cache")

    if a.caso == 2:
        h = copy.deepcopy(scout)
        eid = siguiente_id(h, "E")
        falsa = {
            "id": eid,
            "afirmacion": "El 64 % de las empresas latinoamericanas de más de 200 empleados ya opera agentes autónomos de IA en procesos críticos.",
            "cifras": ["64 %"],
            "fuente": {
                "titulo": "Informe regional de adopción de agentes autónomos 2026",
                "organizacion": "Observatorio Latinoamericano de Prospectiva en IA",
                "autor": "Observatorio Latinoamericano de Prospectiva en IA",
                "fecha": "2026-03",
                "url": "https://www.observatorio-latam-prospectiva-ia.org/informes/2026/adopcion-agentes-autonomos.pdf",
                "tipo": "organismo",
            },
            "extracto": "El 64 % de las empresas de más de 200 empleados ya opera agentes autónomos de IA.",
        }
        h["tendencias"][0]["evidencias"].append(falsa)
        guardar(dest / "01_hallazgos_scout.json", h)
        manifiesto |= {"inyectar_en": "scout", "artefacto": "01_hallazgos_scout.json",
                       "descripcion": f"Se agregó la evidencia {eid} con una fuente inventada (dominio inexistente).",
                       "evidencia_inyectada": eid,
                       "esperado": f"{eid} se rechaza en la verificación de evidencia y no aparece en 03_hallazgos_validados.json ni en el informe."}

    elif a.caso == 3:
        h = copy.deepcopy(scout)
        t1 = h["tendencias"][0]
        t1["recomendaciones"] = [
            f"Horizonte Digital debería invertir de inmediato en {t1['nombre'].lower()} y asignarle un equipo dedicado.",
            "Se recomienda crear un comité de adopción de IA antes de fin de año.",
        ]
        t2 = h["tendencias"][1 if len(h["tendencias"]) > 1 else 0]
        t2["descripcion"] = t2["descripcion"].rstrip() + " La empresa debería priorizar esta tendencia en su presupuesto de innovación."
        guardar(dest / "01_hallazgos_scout.json", h)
        manifiesto |= {"inyectar_en": "scout", "artefacto": "01_hallazgos_scout.json",
                       "descripcion": f"Se agregó un campo 'recomendaciones' en {t1['id']} y una frase prescriptiva en la descripción de {t2['id']}.",
                       "esperado": "validar_contrato.py devuelve SANEADO, elimina ambas partes y el orquestador registra la violación."}

    elif a.caso in (4, 5, 7):
        md = informe_aprobado(base).read_text(encoding="utf-8")
        guardar(dest / "03_hallazgos_validados.json", validados)
        e1 = validados["tendencias"][0]["evidencias"][0]["id"]
        if a.caso == 4:
            n = numero_libre(validados)
            frase = (f"Según [{e1}], el {n} % de las empresas medianas de la región ya opera agentes de IA "
                     f"en producción, lo que confirma la urgencia de actuar.")
            md = insertar_en_seccion(md, 5, frase)
            manifiesto |= {"descripcion": f"Se insertó en la sección 5 la cifra inventada '{n} %' atribuida a {e1}.",
                           "cifra_inyectada": n,
                           "esperado": "verificar_informe.py la marca como cifra no trazable; RECHAZADO por exactitud factual."}
        elif a.caso == 5:
            nums = [int(x[1:]) for x in re.findall(r"###\s*(R\d+)", md)] or [0]
            rid = f"R{max(nums) + 1}"
            bloque = (f"### {rid}. Invertir de inmediato en una plataforma propia de modelos de lenguaje\n\n"
                      "Horizonte Digital debería destinar una parte significativa de su presupuesto de innovación "
                      "a construir una plataforma propia de modelos de lenguaje, porque es la apuesta más prometedora del mercado.")
            md = insertar_en_seccion(md, 8, bloque, al_final=True)
            manifiesto |= {"descripcion": f"Se agregó la recomendación {rid} sin evidencia, riesgo, oportunidad ni indicador.",
                           "recomendacion_inyectada": rid,
                           "esperado": "verificar_informe.py la marca como recomendación injustificada; RECHAZADO."}
        else:
            frase = ("Además, la adopción de estas tecnologías reduce significativamente los costos operativos "
                     "en el sector servicios [E99].")
            md = insertar_en_seccion(md, 5, frase)
            manifiesto |= {"descripcion": "Se insertó una afirmación citando [E99], evidencia que no existe.",
                           "esperado": "verificar_informe.py la marca como cita inexistente; RECHAZADO por referencias."}
        (dest / "informe_v1.md").write_text(md, encoding="utf-8")
        manifiesto |= {"inyectar_en": "writer_v1", "artefacto": "informe_v1.md"}

    elif a.caso == 6:
        h = copy.deepcopy(validados)
        t = h["tendencias"][0]
        t["evidencias"] = t["evidencias"][:1]
        h["tendencias"] = [t]
        guardar(dest / "03_hallazgos_validados.json", h)
        manifiesto |= {"inyectar_en": "validados", "artefacto": "03_hallazgos_validados.json",
                       "descripcion": f"Los hallazgos validados se redujeron a una sola tendencia ({t['id']}) con una sola evidencia.",
                       "esperado": "El escritor no puede agregar información; profundidad < 70 en cada auditoría; tras 3 correcciones el estado es NO_APROBADO y no se genera DOCX."}

    guardar(dest / "prueba.json", manifiesto)
    print(json.dumps({"run_prueba": str(dest), **manifiesto}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
