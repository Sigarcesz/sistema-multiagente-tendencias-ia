# Registro de ejecución (reconstruido) — v1-base_caso1_caso6

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:26:31 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso6 (lee runs/v1-base_caso1_caso6/prueba.json). | log.jsonl |
| 2 | 17:26:31 | 0 | prueba | inyeccion_prueba | CASO_6 | Los hallazgos validados se redujeron a una sola tendencia (T1) con una sola evidencia. | prueba.json |
| 3 | 17:27:07 | 1 | report-writer | redaccion | OK | runs/v1-base_caso1_caso6/informe_v1.md | delegaciones.jsonl |
| 4 | 17:28:50 | 1 | quality-auditor | auditoria | RECHAZADO | score 79.8; umbrales incumplidos: ['exactitud 85 < 90', 'profundidad 50 < 70', 'global 79.8 < 85']; 5 correcciones | auditoria_v1.json |
| 5 | 17:29:53 | 2 | report-writer | correccion | OK | runs/v1-base_caso1_caso6/informe_v2.md — correcciones aplicadas: 4; no_corregibles: 1 | delegaciones.jsonl |
| 6 | 17:30:39 | 2 | quality-auditor | auditoria | RECHAZADO | score 77.0; rechazos automáticos: ["R-AUDITOR: Inconsistencia significativa en el nivel de confianza: el archivo de hallazgos validado (03_hallazgos_validados.json) indica 'confianza' = 'alta' para T1, mientras que el informe dice 'nivel de confianza: medio' y afirma que la evidencia está limitada a una sola fuente. Esta contradicción afecta la exactitud general del documento."]; umbrales incumplidos: ['exactitud 75 < 90', 'profundidad 50 < 70', 'global 77.0 < 85']; 5 correcciones | auditoria_v2.json |
| 7 | 17:31:31 | 3 | report-writer | correccion | OK | runs/v1-base_caso1_caso6/informe_v3.md Correcciones aplicadas: 4 corregidas, 1 no_corregible (C4). | delegaciones.jsonl |
| 8 | 17:32:13 | 3 | quality-auditor | auditoria | RECHAZADO | score 81.8; umbrales incumplidos: ['profundidad 50 < 70', 'global 81.8 < 85']; 4 correcciones | auditoria_v3.json |
| 9 | 17:33:15 | 4 | report-writer | correccion | OK | runs/v1-base_caso1_caso6/informe_v4.md He corregido 2 y marqué 2 como no corregibles. | delegaciones.jsonl |
| 10 | 17:34:01 | 4 | quality-auditor | auditoria | RECHAZADO | score 76.0; umbrales incumplidos: ['exactitud 80 < 90', 'profundidad 50 < 70', 'global 76.0 < 85']; 5 correcciones | auditoria_v4.json |
| 11 | 17:34:22 | 0 | orquestador | fin | NO_APROBADO | 4 auditoría(s); última: RECHAZADO (score 76.0); documento: no generado | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 4 · Correcciones: 3
Duración: 8.1 min · Tokens: 506,072 entrada / 39,241 salida · 72 peticiones

**Estado final: NO_APROBADO** — 4 auditoría(s); última: RECHAZADO (score 76.0); documento: no generado
