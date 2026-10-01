# Casos de prueba

Los campos **Evidencia observada** y **Resultado obtenido** se llenan después de cada
ejecución, citando archivos y eventos concretos del run (no impresiones).

## Cómo se ejecutan

```bash
# Caso 1 (flujo real completo). Esta carpeta será la BASE de los demás casos.
python -m runner.main --run runs/v1-base_caso1

# Casos 2-7: se inyecta un fallo sobre los artefactos reales del caso 1
python scripts/inyectar_fallo.py --base runs/v1-base_caso1 --caso 4
python -m runner.main --prueba runs/v1-base_caso1_caso4
```

Verificación previa sin red ni modelo: `python scripts/smoke_test.py`.
Con Claude Code, el equivalente es `claude --agent orquestador "<solicitud o modo prueba>"`.

---

## Caso 1 — Flujo correcto

| Campo | Contenido |
|---|---|
| Entrada | Solicitud de Horizonte Digital S.A.S. (modo real) |
| Componente evaluado | Sistema completo |
| Resultado esperado | APROBADO y DOCX generado |
| Criterio de aprobación | `auditoria_vN.json` → `estado: APROBADO`, exactitud ≥ 90, referencias ≥ 90, profundidad ≥ 70, global ≥ 85, sin rechazos automáticos; existe `final/*.docx`; `log.md` muestra la secuencia Scout → contrato → verificación → redacción → auditoría → publicación |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 2 — Fuente inexistente

| Campo | Contenido |
|---|---|
| Entrada | `01_hallazgos_scout.json` real + una evidencia con fuente inventada (dominio inexistente) |
| Componente evaluado | Auditor (modo verificación de evidencia) + `aplicar_verificacion.py` |
| Resultado esperado | La evidencia se rechaza antes de llegar al escritor |
| Criterio de aprobación | La evidencia inyectada (`prueba.json → evidencia_inyectada`) aparece en `03_filtrado.json → evidencias_rechazadas`, NO aparece en `03_hallazgos_validados.json` ni en ningún `informe_v*.md`; el log tiene un evento `evidencia_rechazada` |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 3 — Invasión de responsabilidades

| Campo | Contenido |
|---|---|
| Entrada | `01_hallazgos_scout.json` real + campo `recomendaciones` en T1 + frase prescriptiva en T2 |
| Componente evaluado | Orquestador (compuerta `validar_contrato.py`) |
| Resultado esperado | Se eliminan ambas partes y se registra la violación |
| Criterio de aprobación | `02_contrato.json → estado: SANEADO` con ≥ 2 violaciones; `02_hallazgos_contrato.json` no contiene esos textos; el log tiene un evento `violacion_responsabilidad` por violación; el flujo continúa |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 4 — Invención del escritor

| Campo | Contenido |
|---|---|
| Entrada | Informe aprobado del caso 1 + una cifra inventada en la sección 5 (`informe_v1.md`) |
| Componente evaluado | Auditor (`verificar_informe.py` + `decidir_estado.py`) |
| Resultado esperado | RECHAZADO por exactitud factual |
| Criterio de aprobación | `verificacion_informe_v1.json → cifras_no_trazables` incluye la cifra inyectada; `auditoria_v1.json → estado: RECHAZADO`, `rechazos_automaticos` contiene `R-EXACTITUD`, exactitud ≤ 60; existe una corrección que señala esa cifra |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 5 — Recomendación injustificada

| Campo | Contenido |
|---|---|
| Entrada | Informe aprobado del caso 1 + recomendación de inversión sin vínculos (`informe_v1.md`) |
| Componente evaluado | Auditor (`verificar_informe.py` + `decidir_estado.py`) |
| Resultado esperado | RECHAZADO |
| Criterio de aprobación | `verificacion_informe_v1.json → recomendaciones_invalidas` incluye la R# inyectada con sus cuatro problemas; `auditoria_v1.json → estado: RECHAZADO` con `R-RECOMENDACION` |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 6 — Límite de iteraciones

| Campo | Contenido |
|---|---|
| Entrada | Hallazgos validados reducidos a una tendencia con una evidencia, sin reinvestigación |
| Componente evaluado | Orquestador (ciclo de corrección) + guarda de `generar_docx.py` |
| Resultado esperado | NO_APROBADO; el documento no se publica |
| Criterio de aprobación | Existen `auditoria_v1.json` a `auditoria_v4.json`, todas RECHAZADO; hay exactamente 3 eventos `correccion`; el último evento `fin` tiene estado `NO_APROBADO`; no existe `final/` ni ningún `.docx`; no hay evento `publicacion` |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 7 — Cita a evidencia inexistente (adicional)

| Campo | Contenido |
|---|---|
| Entrada | Informe aprobado del caso 1 + afirmación que cita `[E99]` |
| Componente evaluado | Auditor (`verificar_informe.py`) |
| Resultado esperado | RECHAZADO por referencias |
| Criterio de aprobación | `citas_inexistentes` incluye E99; `auditoria_v1.json → estado: RECHAZADO` con `R-REFERENCIAS` |
| Evidencia observada | |
| Resultado obtenido | |

## Caso 8 — Corrección exitosa (adicional, se observa en el run del caso 4 o 5)

| Campo | Contenido |
|---|---|
| Entrada | Rechazo de `auditoria_v1.json` del caso 4 |
| Componente evaluado | Report Writer (modo corrección) + ciclo del orquestador |
| Resultado esperado | El escritor corrige solo lo observado y la v2 se APRUEBA |
| Criterio de aprobación | `respuesta_correcciones_v2.json` reporta la corrección; la cifra inventada no está en `informe_v2.md`; `auditoria_v2.json → APROBADO`; el resto del informe no cambió sustancialmente (comparar v1 y v2) |
| Evidencia observada | |
| Resultado obtenido | |
