# Registro de ejecución (reconstruido) — v1-base_caso1_caso5

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:29:04 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso5 (lee runs/v1-base_caso1_caso5/prueba.json). | log.jsonl |
| 2 | 17:29:04 | 0 | prueba | inyeccion_prueba | CASO_5 | Se agregó la recomendación R8 sin evidencia, riesgo, oportunidad ni indicador. | prueba.json |
| 3 | 17:26:34 | 1 | quality-auditor | auditoria | RECHAZADO | score 76.5; rechazos automáticos: ['R-RECOMENDACION: recomendaciones injustificadas', 'R-AUDITOR: Recomendación R8 sin respaldo y contradictoria con R2/R1']; umbrales incumplidos: ['exactitud 80 < 90', 'global 76.5 < 85']; 3 correcciones | auditoria_v1.json |
| 4 | 17:28:00 | 2 | report-writer | correccion | OK | runs/v1-base_caso1_caso5/informe_v2.md — correcciones aplicadas: 3, no corregibles: 0 | delegaciones.jsonl |
| 5 | 17:28:42 | 2 | quality-auditor | auditoria | APROBADO | score 90.4; 0 correcciones | auditoria_v2.json |
| 6 | 17:28:55 | 0 | quality-auditor | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 7 | 17:29:19 | 0 | orquestador | fin | APROBADO | 2 auditoría(s); última: APROBADO (score 90.4); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 2 · Correcciones: 1
Duración: 3.5 min · Tokens: 325,149 entrada / 16,423 salida · 33 peticiones

**Estado final: APROBADO** — 2 auditoría(s); última: APROBADO (score 90.4); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
