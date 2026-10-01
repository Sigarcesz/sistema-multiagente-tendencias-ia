#!/usr/bin/env python3
"""Prueba rápida de las compuertas deterministas con datos FICTICIOS (sin red ni modelo).

Comprueba que cada compuerta reacciona como se espera antes de gastar tokens en una
ejecución real. No reemplaza los casos de prueba del proyecto (esos usan el sistema completo).

Uso:  python3 scripts/smoke_test.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FIX = RAIZ / "tests" / "fixtures" / "sintetico"
AUD = RAIZ / ".claude" / "skills" / "quality-auditor" / "scripts"
PY = sys.executable
ok = True


def run(*args):
    r = subprocess.run([PY, *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def check(nombre, cond, detalle=""):
    global ok
    print(f"[{'OK ' if cond else 'FALLA'}] {nombre}" + (f" — {detalle}" if detalle and not cond else ""))
    ok &= bool(cond)


with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp) / "runs" / "base"
    base.mkdir(parents=True)
    shutil.copy(FIX / "hallazgos_scout.json", base / "01_hallazgos_scout.json")

    # Compuerta de contrato: caso limpio
    c, out, _ = run(RAIZ / "scripts/validar_contrato.py", "--entrada", base / "01_hallazgos_scout.json",
                    "--salida", base / "02_hallazgos_contrato.json", "--reporte", base / "02_contrato.json")
    check("contrato limpio -> OK", c == 0, out)

    # Filtrado de evidencia (todo verificado)
    run(AUD / "aplicar_verificacion.py", "--hallazgos", base / "02_hallazgos_contrato.json",
        "--fuentes", FIX / "verificacion_fuentes.json", "--veredictos", FIX / "verificacion_evidencia.json",
        "--salida", base / "03_hallazgos_validados.json", "--reporte", base / "03_filtrado.json")
    rep = json.load(open(base / "03_filtrado.json"))
    check("verificación completa conserva 3 tendencias", rep["tendencias_validas"] == 3, rep)

    # Informe válido
    shutil.copy(FIX / "informe.md", base / "informe_v1.md")
    run(AUD / "verificar_informe.py", "--informe", base / "informe_v1.md",
        "--hallazgos", base / "03_hallazgos_validados.json", "--salida", base / "verificacion_informe_v1.json")
    v = json.load(open(base / "verificacion_informe_v1.json"))
    check("informe válido sin bloqueantes", not v["bloqueantes"], v["bloqueantes"] or v)
    c, out, _ = run(AUD / "decidir_estado.py", "--borrador", FIX / "auditoria_borrador.json",
                    "--verificacion", base / "verificacion_informe_v1.json", "--version", 1,
                    "--salida", base / "auditoria_v1.json")
    check("informe válido -> APROBADO", json.load(open(base / "auditoria_v1.json"))["estado"] == "APROBADO", out)
    c, out, err = run(AUD / "generar_docx.py", "--informe", base / "informe_v1.md", "--auditoria", base / "auditoria_v1.json",
                      "--hallazgos", base / "03_hallazgos_validados.json", "--cliente", "Horizonte Digital S.A.S.",
                      "--titulo", "Informe de prueba", "--salida-dir", base / "final")
    check("DOCX generado cuando está APROBADO", c == 0 and list((base / "final").glob("*.docx")), err)

    # Caso 2 (parte mecánica): URL inexistente se descarta aunque el auditor la apruebe
    fuentes = json.load(open(FIX / "verificacion_fuentes.json"))
    fuentes["evidencias"][2]["estado"] = "inaccesible"
    json.dump(fuentes, open(Path(tmp) / "f2.json", "w"))
    run(AUD / "aplicar_verificacion.py", "--hallazgos", base / "02_hallazgos_contrato.json",
        "--fuentes", Path(tmp) / "f2.json", "--veredictos", FIX / "verificacion_evidencia.json",
        "--salida", Path(tmp) / "v2.json", "--reporte", Path(tmp) / "r2.json")
    r2 = json.load(open(Path(tmp) / "r2.json"))
    check("caso 2: URL inaccesible se rechaza (fail-closed)", [e["id"] for e in r2["evidencias_rechazadas"]] == ["E3"], r2)

    # Casos inyectados
    for caso in (3, 4, 5, 6, 7):
        c, out, err = run(RAIZ / "scripts/inyectar_fallo.py", "--base", base, "--caso", caso)
        if c != 0:
            check(f"inyección caso {caso}", False, err)
            continue
        d = Path(f"{base}_caso{caso}")
        if caso == 3:
            c, out, _ = run(RAIZ / "scripts/validar_contrato.py", "--entrada", d / "01_hallazgos_scout.json",
                            "--salida", d / "02_hallazgos_contrato.json", "--reporte", d / "02_contrato.json")
            rep = json.load(open(d / "02_contrato.json"))
            limpio = json.dumps(json.load(open(d / "02_hallazgos_contrato.json")), ensure_ascii=False).lower()
            check("caso 3: invasión detectada y eliminada",
                  c == 1 and len(rep["violaciones"]) >= 2 and "recomendaciones" not in limpio and "debería priorizar" not in limpio,
                  rep["violaciones"])
            continue
        informe = d / ("informe_v1.md" if caso != 6 else "x")
        if caso == 6:
            shutil.copy(FIX / "informe.md", d / "informe_v1.md")
            informe = d / "informe_v1.md"
        run(AUD / "verificar_informe.py", "--informe", informe, "--hallazgos", d / "03_hallazgos_validados.json",
            "--salida", d / "ver.json")
        run(AUD / "decidir_estado.py", "--borrador", FIX / "auditoria_borrador.json", "--verificacion", d / "ver.json",
            "--version", 1, "--salida", d / "aud.json")
        v, aud = json.load(open(d / "ver.json")), json.load(open(d / "aud.json"))
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

    # Log
    run(RAIZ / "scripts/log.py", "init", "--run", base, "--solicitud", "prueba")
    run(RAIZ / "scripts/log.py", "evento", "--run", base, "--paso", 9, "--componente", "orquestador",
        "--evento", "fin", "--estado", "APROBADO", "--detalle", "ok")
    c, _, _ = run(RAIZ / "scripts/log.py", "resumen", "--run", base)
    check("log.md generado", c == 0 and (base / "log.md").exists())

print("\nTODO OK" if ok else "\nHAY FALLAS")
sys.exit(0 if ok else 1)
