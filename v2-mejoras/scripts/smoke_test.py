#!/usr/bin/env python3
"""Prueba rápida de los scripts deterministas con datos FICTICIOS (sin red ni modelo).

Comprueba que cada compuerta reacciona como se espera antes de gastar tokens en una
ejecución real. No reemplaza los casos de prueba del proyecto (esos usan el sistema completo).

Uso:  python scripts/smoke_test.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from texto_fuentes import ruta_cache  # noqa: E402

FIX = RAIZ / "tests" / "fixtures" / "sintetico"
AUD = RAIZ / ".claude" / "skills" / "quality-auditor" / "scripts"
S = RAIZ / "scripts"
PY = sys.executable
ok = True


def run(*args, cwd=None):
    r = subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def check(nombre, cond, detalle=""):
    global ok
    print(f"[{'OK ' if cond else 'FALLA'}] {nombre}" + (f" — {detalle}" if detalle and not cond else ""))
    ok &= bool(cond)


def cargar(p):
    return json.load(open(p, encoding="utf-8"))


def guardar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    rel = Path("runs") / "base"
    base = tmp / rel
    h = cargar(FIX / "hallazgos_scout.json")

    # --- Fase 1: candidatas + una tendencia por Scout + unión ------------------------------
    guardar(base / "01a_candidatas.json", {"tema": h["tema"], "fecha_investigacion": h["fecha_investigacion"],
                                           "candidatas": [{"id": t["id"], "nombre": t["nombre"], "descripcion_breve": "",
                                                           "consultas_sugeridas": []} for t in h["tendencias"]]
                                           + [{"id": "T9", "nombre": "Descartada", "descripcion_breve": "", "consultas_sugeridas": []}]})
    for t in h["tendencias"]:
        t2 = json.loads(json.dumps(t))
        for i, e in enumerate(t2["evidencias"], 1):
            e["id"] = f"E{i}"            # IDs locales, como los deja cada Scout
        guardar(base / "01b_tendencias" / f"{t['id']}.json", t2)
    guardar(base / "01b_tendencias" / "T9.json", {"descartada": True, "motivo": "sin evidencia verificable"})
    c, out, err = run(S / "unir_hallazgos.py", "--run", rel, cwd=tmp)
    u = cargar(base / "01_hallazgos_scout.json")
    ids = [e["id"] for t in u["tendencias"] for e in t["evidencias"]]
    check("unión: renumera E# globalmente y descarta T9", ids == ["E1", "E2", "E3", "E4"] and len(u["tendencias"]) == 3, out + err)

    # --- Compuerta de contrato -----------------------------------------------------------
    c, out, _ = run(S / "validar_contrato.py", "--entrada", rel / "01_hallazgos_scout.json",
                    "--salida", rel / "02_hallazgos_contrato.json", "--reporte", rel / "02_contrato.json", cwd=tmp)
    rep = cargar(base / "02_contrato.json")
    check("contrato limpio -> OK", c == 0, out)
    check("contrato: advierte fuente de más de 24 meses (E4)", [a["evidencia"] for a in rep["advertencias"]] == ["E4"], rep["advertencias"])

    # --- Verificación: caché simulada (sin red) -------------------------------------------
    textos = {e["fuente"]["url"]: f"TÍTULO: {e['fuente']['titulo']}\n" + ("Relleno del documento. " * 20) + "\n" + e["extracto"]
              for t in u["tendencias"] for e in t["evidencias"]}
    for url, tx in textos.items():
        p = ruta_cache(base, url)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(tx, encoding="utf-8")
    c, out, err = run(S / "preparar_verificacion.py", "--run", rel, cwd=tmp)
    mec = cargar(base / "03_verificacion" / "mecanica.json")
    check("verificación mecánica: cifras y extractos encontrados en la página",
          c == 0 and not mec["resumen"]["evidencias_con_cifras_no_encontradas"]
          and not mec["resumen"]["evidencias_con_extracto_no_encontrado"]
          and mec["resumen"]["reutilizadas_de_cache"] == 4, out + err)
    check("verificación mecánica: un pendiente por tendencia",
          sorted(x.name for x in (base / "03_verificacion").glob("pendiente_*.json")) == ["pendiente_T1.json", "pendiente_T2.json", "pendiente_T3.json"])
    for t in u["tendencias"]:
        guardar(base / "03_verificacion" / f"veredictos_{t['id']}.json",
                {"tendencia": t["id"], "evidencias": [{"id": e["id"], "veredicto": "VERIFICADA", "motivo": "ficticio"} for e in t["evidencias"]]})
    c, out, err = run(S / "unir_verificacion.py", "--run", rel, cwd=tmp)
    f = cargar(base / "03_filtrado.json")
    aj = {a["tendencia"]: a for a in f["ajustes_confianza"]}
    check("unión de veredictos: 4/4 evidencias válidas", f["evidencias_validas"] == 4, out + err)
    check("confianza recalculada: T2 y T3 (una sola evidencia) bajan de alta a media",
          set(aj) == {"T2", "T3"} and all(a["a"] == "media" for a in aj.values()), f["ajustes_confianza"])

    # Cifra que no aparece en la página -> rechazo mecánico
    alt = tmp / "runs" / "alt"
    shutil.copytree(base, alt)
    url_e1 = u["tendencias"][0]["evidencias"][0]["fuente"]["url"]
    ruta_cache(alt, url_e1).write_text("TÍTULO: x\n" + "Texto sin la cifra. " * 30, encoding="utf-8")
    run(S / "preparar_verificacion.py", "--run", Path("runs") / "alt", cwd=tmp)
    run(S / "unir_verificacion.py", "--run", Path("runs") / "alt", cwd=tmp)
    fa = cargar(alt / "03_filtrado.json")
    r = {x["id"]: x for x in fa["evidencias_rechazadas"]}
    check("cifra ausente en la página -> rechazo mecánico aunque el auditor diga VERIFICADA",
          "E1" in r and r["E1"]["origen"] == "mecanico", fa["evidencias_rechazadas"])

    # Fuente inaccesible -> rechazo (caso 2, parte mecánica)
    mec_alt = cargar(alt / "03_verificacion" / "mecanica.json")
    mec_alt["evidencias"][2]["estado_fuente"] = "inaccesible"
    guardar(alt / "03_verificacion" / "mecanica.json", mec_alt)
    run(S / "unir_verificacion.py", "--run", Path("runs") / "alt", cwd=tmp)
    r = {x["id"]: x for x in cargar(alt / "03_filtrado.json")["evidencias_rechazadas"]}
    check("caso 2: URL inaccesible se rechaza (fail-closed)", "E3" in r and "inaccesible" in r["E3"]["motivo"], r)

    # --- Informe válido -----------------------------------------------------------------
    shutil.copy(FIX / "informe.md", base / "informe_v1.md")
    run(AUD / "verificar_informe.py", "--informe", base / "informe_v1.md",
        "--hallazgos", base / "03_hallazgos_validados.json", "--salida", base / "verificacion_informe_v1.json")
    v = cargar(base / "verificacion_informe_v1.json")
    check("informe válido sin bloqueantes", not v["bloqueantes"], v["bloqueantes"] or v)
    c, out, _ = run(AUD / "decidir_estado.py", "--borrador", FIX / "auditoria_borrador.json",
                    "--verificacion", base / "verificacion_informe_v1.json", "--version", 1,
                    "--salida", base / "auditoria_v1.json")
    check("informe válido -> APROBADO", cargar(base / "auditoria_v1.json")["estado"] == "APROBADO", out)
    c, out, err = run(AUD / "generar_docx.py", "--informe", base / "informe_v1.md", "--auditoria", base / "auditoria_v1.json",
                      "--hallazgos", base / "03_hallazgos_validados.json", "--cliente", "Horizonte Digital S.A.S.",
                      "--titulo", "Informe de prueba", "--salida-dir", base / "final")
    check("DOCX generado cuando está APROBADO", c == 0 and list((base / "final").glob("*.docx")), err)

    # --- Casos inyectados -----------------------------------------------------------------
    for caso in (3, 4, 5, 6, 7):
        c, out, err = run(S / "inyectar_fallo.py", "--base", base, "--caso", caso)
        if c != 0:
            check(f"inyección caso {caso}", False, err)
            continue
        d = Path(f"{base}_caso{caso}")
        if caso == 3:
            c, out, _ = run(S / "validar_contrato.py", "--entrada", d / "01_hallazgos_scout.json",
                            "--salida", d / "02_hallazgos_contrato.json", "--reporte", d / "02_contrato.json")
            rep = cargar(d / "02_contrato.json")
            limpio = json.dumps(cargar(d / "02_hallazgos_contrato.json"), ensure_ascii=False).lower()
            check("caso 3: invasión detectada y eliminada",
                  c == 1 and len(rep["violaciones"]) >= 2 and "recomendaciones" not in limpio and "debería priorizar" not in limpio,
                  rep["violaciones"])
            continue
        if caso == 6:
            shutil.copy(FIX / "informe.md", d / "informe_v1.md")
        informe = d / "informe_v1.md"
        run(AUD / "verificar_informe.py", "--informe", informe, "--hallazgos", d / "03_hallazgos_validados.json", "--salida", d / "ver.json")
        run(AUD / "decidir_estado.py", "--borrador", FIX / "auditoria_borrador.json", "--verificacion", d / "ver.json",
            "--version", 1, "--salida", d / "aud.json")
        v, aud = cargar(d / "ver.json"), cargar(d / "aud.json")
        esperado = {4: "CIFRAS_NO_TRAZABLES", 5: "RECOMENDACIONES_INJUSTIFICADAS", 7: "CITAS_INEXISTENTES"}.get(caso)
        if esperado:
            check(f"caso {caso}: {esperado} -> RECHAZADO", esperado in v["bloqueantes"] and aud["estado"] == "RECHAZADO",
                  {"bloqueantes": v["bloqueantes"], "estado": aud["estado"]})
        else:
            check("caso 6: <3 tendencias -> profundidad topada y RECHAZADO",
                  aud["puntajes"]["profundidad"] <= 50 and aud["estado"] == "RECHAZADO", aud["umbrales_incumplidos"])
        if aud["estado"] != "APROBADO":
            c, _, _ = run(AUD / "generar_docx.py", "--informe", informe, "--auditoria", d / "aud.json",
                          "--hallazgos", d / "03_hallazgos_validados.json", "--cliente", "X", "--titulo", "X",
                          "--salida-dir", d / "final")
            check(f"caso {caso}: generar_docx se niega a publicar", c == 3)

    # --- Registro, reporte y comparación ------------------------------------------------------
    run(S / "log.py", "init", "--run", base, "--solicitud", "prueba")
    with open(base / "delegaciones.jsonl", "w", encoding="utf-8") as fh:
        for ag, m, t0, t1 in [("trend-scout", "modo: candidatas", "2026-10-01T10:00:00", "2026-10-01T10:01:00"),
                              ("trend-scout", "modo: tendencia T1", "2026-10-01T10:01:00", "2026-10-01T10:03:00"),
                              ("trend-scout", "modo: tendencia T2", "2026-10-01T10:01:00", "2026-10-01T10:02:30"),
                              ("orquestador", "solicitud", "2026-10-01T10:00:00", "2026-10-01T10:10:00")]:
            fh.write(json.dumps({"ts": t1, "ts_inicio": t0, "agente": ag, "etiqueta": ag, "mensaje": m,
                                 "respuesta": "ok", "error": None, "segundos": 60}) + "\n")
    with open(base / "scripts.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts_inicio": "2026-10-01T10:03:00", "ts_fin": "2026-10-01T10:03:01", "script": "scripts/unir_verificacion.py",
                             "argumentos": [], "codigo_salida": 0, "salida": "", "segundos": 1}) + "\n")
    guardar(base / "uso.json", {"version": "v2", "duracion_segundos": 600, "total": {"requests": 10, "input_tokens": 1000, "output_tokens": 100},
                                "por_agente": {}})
    c, out, err = run(S / "reconstruir_log.py", "--run", base)
    check("registro reconstruido (v2)", c == 0 and (base / "log_completo.md").exists() and "ajuste_confianza" in
          (base / "log_completo.md").read_text(encoding="utf-8"), out + err)
    c, out, err = run(S / "reporte_run.py", "--run", base)
    check("reporte HTML generado", c == 0 and (base / "reporte_run.html").exists(), err)
    c, out, err = run(S / "comparar_runs.py", base, alt)
    check("comparación de runs", c == 0 and "| Métrica |" in out, err)

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
