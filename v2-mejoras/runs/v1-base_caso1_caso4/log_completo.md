# Registro de ejecución (reconstruido) — v1-base_caso1_caso4

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:25:11 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso4 (lee runs/v1-base_caso1_caso4/prueba.json). | log.jsonl |
| 2 | 17:25:11 | 0 | prueba | inyeccion_prueba | CASO_4 | Se insertó en la sección 5 la cifra inventada '73,4 %' atribuida a E2. | prueba.json |
| 3 | 17:25:50 | 1 | quality-auditor | auditoria | RECHAZADO | score 79.5; rechazos automáticos: ['R-EXACTITUD: cifras que no aparecen en los hallazgos', 'R-AUDITOR: CIFRAS_NO_TRAZABLES']; umbrales incumplidos: ['exactitud 60 < 90', 'referencias 88 < 90', 'global 79.5 < 85']; 3 correcciones | auditoria_v1.json |
| 4 | 17:27:09 | 2 | report-writer | correccion | OK | runs/v1-base_caso1_caso4/informe_v2.md — correcciones aplicadas: 3, no corregibles: 0 | delegaciones.jsonl |
| 5 | 17:28:12 | 2 | quality-auditor | auditoria | APROBADO | score 89.8; 0 correcciones | auditoria_v2.json |
| 6 | 17:28:34 | 0 | quality-auditor | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 7 | 17:29:15 | 0 | orquestador | fin | APROBADO | 2 auditoría(s); última: APROBADO (score 89.8); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 2 · Correcciones: 1
Duración: 4.3 min · Tokens: 410,149 entrada / 21,005 salida · 40 peticiones

**Estado final: APROBADO** — 2 auditoría(s); última: APROBADO (score 89.8); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
