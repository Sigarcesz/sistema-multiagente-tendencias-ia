# Registro de ejecución (reconstruido) — v1-base_caso1_caso7

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:26:52 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso7 (lee runs/v1-base_caso1_caso7/prueba.json) | log.jsonl |
| 2 | 17:26:52 | 0 | prueba | inyeccion_prueba | CASO_7 | Se insertó una afirmación citando [E99], evidencia que no existe. | prueba.json |
| 3 | 17:27:50 | 1 | quality-auditor | auditoria | RECHAZADO | score 80.2; rechazos automáticos: ['R-REFERENCIAS: citas a evidencias que no existen en los hallazgos validados', 'R-AUDITOR: CITAS_INEXISTENTES']; umbrales incumplidos: ['exactitud 88 < 90', 'referencias 50 < 90', 'global 80.2 < 85']; 3 correcciones | auditoria_v1.json |
| 4 | 17:29:09 | 2 | report-writer | correccion | OK | runs/v1-base_caso1_caso7/informe_v2.md, aplicadas 2, no_corregibles 1 | delegaciones.jsonl |
| 5 | 17:30:02 | 2 | quality-auditor | auditoria | RECHAZADO | score 84.8; umbrales incumplidos: ['exactitud 85 < 90', 'global 84.8 < 85']; 3 correcciones | auditoria_v2.json |
| 6 | 17:31:09 | 3 | report-writer | correccion | OK | runs/v1-base_caso1_caso7/informe_v3.md — correcciones aplicadas: 3, no corregibles: 0 | delegaciones.jsonl |
| 7 | 17:32:01 | 3 | quality-auditor | auditoria | APROBADO | score 89.4; 0 correcciones | auditoria_v3.json |
| 8 | 17:32:20 | 0 | quality-auditor | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 9 | 17:32:49 | 0 | orquestador | fin | APROBADO | 3 auditoría(s); última: APROBADO (score 89.4); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 3 · Correcciones: 2
Duración: 6.1 min · Tokens: 808,368 entrada / 29,934 salida · 60 peticiones

**Estado final: APROBADO** — 3 auditoría(s); última: APROBADO (score 89.4); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
