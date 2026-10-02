# Registro de ejecución (reconstruido) — v1-base_caso1_caso2

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:22:34 | 0 | orquestador | inicio | OK | Ejecutar en modo prueba sobre runs/v1-base_caso1_caso2 (lee runs/v1-base_caso1_caso2/prueba.json). | log.jsonl |
| 2 | 17:22:34 | 0 | prueba | inyeccion_prueba | CASO_2 | Se agregó la evidencia E15 con una fuente inventada (dominio inexistente). | prueba.json |
| 3 | 17:24:38 | 0 | orquestador | compuerta_contrato | OK | 7 tendencias, 15 evidencias, 0 violaciones, 0 errores | 02_contrato.json |
| 4 | 17:24:38 | 0 | quality-auditor | verificacion_evidencia | OK | 12/15 evidencias válidas; 7/7 tendencias con respaldo | 03_filtrado.json |
| 5 | 17:24:38 | 0 | quality-auditor | evidencia_rechazada | RECHAZADA | E1 (T1): La página contiene 'tens of thousands' y '85%' pero no aparece la cifra '4.7x' mencionada en la afirmación. | 03_filtrado.json |
| 6 | 17:24:38 | 0 | quality-auditor | evidencia_rechazada | RECHAZADA | E15 (T1): URL inaccesible (conexion: HTTPSConnectionPool(host='www.observatorio-latam-prospectiva-ia.org', port=443): Max retries exceeded with url: /informes/2026/adopcion-agentes-autonomos.pdf (C) | 03_filtrado.json |
| 7 | 17:24:38 | 0 | quality-auditor | evidencia_rechazada | RECHAZADA | E3 (T2): La página EUR-Lex no devuelve texto legible (bloqueo/dinámica); no es posible confirmar el contenido. | 03_filtrado.json |
| 8 | 17:26:08 | 1 | report-writer | redaccion | OK | runs/v1-base_caso1_caso2/informe_v1.md | delegaciones.jsonl |
| 9 | 17:26:54 | 1 | quality-auditor | auditoria | APROBADO | score 88.6; 0 correcciones | auditoria_v1.json |
| 10 | 17:27:12 | 0 | quality-auditor | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 11 | 17:27:45 | 0 | orquestador | fin | APROBADO | 1 auditoría(s); última: APROBADO (score 88.6); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 3  
Auditorías: 1 · Correcciones: 0
Duración: 5.5 min · Tokens: 876,950 entrada / 23,484 salida · 61 peticiones

**Estado final: APROBADO** — 1 auditoría(s); última: APROBADO (score 88.6); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
