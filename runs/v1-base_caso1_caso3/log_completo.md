# Registro de ejecución (reconstruido) — v1-base_caso1_caso3

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 17:24:35 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso3 (lee runs/v1-base_caso1_caso3/prueba.json). | log.jsonl |
| 2 | 17:24:35 | 0 | prueba | inyeccion_prueba | CASO_3 | Se agregó un campo 'recomendaciones' en T1 y una frase prescriptiva en la descripción de T2. | prueba.json |
| 3 | 17:26:43 | 0 | orquestador | compuerta_contrato | SANEADO | 7 tendencias, 14 evidencias, 2 violaciones, 0 errores | 02_contrato.json |
| 4 | 17:26:43 | 0 | orquestador | violacion_responsabilidad | ELIMINADO | $.tendencias[0].recomendaciones: «["Horizonte Digital debería invertir de inmediato en adopción y personalización de modelos de base (foundation models) en la empresa y asignarle un equipo dedicado.", "Se recomienda crear un comité de» | 02_contrato.json |
| 5 | 17:26:43 | 0 | orquestador | violacion_responsabilidad | ELIMINADO | T2.descripcion: «La empresa debería priorizar esta tendencia en su presupuesto de innovación.» | 02_contrato.json |
| 6 | 17:26:43 | 0 | quality-auditor | verificacion_evidencia | OK | 12/14 evidencias válidas; 7/7 tendencias con respaldo | 03_filtrado.json |
| 7 | 17:26:43 | 0 | quality-auditor | evidencia_rechazada | RECHAZADA | E1 (T1): La página respalda 'tens of thousands' y '85%' pero NO contiene '4.7x' (menciona 'up to 4x'), por tanto la cifra no coincide. | 03_filtrado.json |
| 8 | 17:26:43 | 0 | quality-auditor | evidencia_rechazada | RECHAZADA | E3 (T2): Contenido no legible/bloqueado (webfetch devolvió error); no fue posible confirmar la regulación ni las fechas. | 03_filtrado.json |
| 9 | 17:28:01 | 1 | report-writer | redaccion | OK | runs/v1-base_caso1_caso3/informe_v1.md | delegaciones.jsonl |
| 10 | 17:28:48 | 1 | quality-auditor | auditoria | RECHAZADO | score 85.7; umbrales incumplidos: ['exactitud 82 < 90']; 3 correcciones | auditoria_v1.json |
| 11 | 17:29:50 | 2 | report-writer | correccion | OK | runs/v1-base_caso1_caso3/informe_v2.md He corregido 3 de 3 observaciones. | delegaciones.jsonl |
| 12 | 17:30:33 | 2 | quality-auditor | auditoria | APROBADO | score 89.3; 0 correcciones | auditoria_v2.json |
| 13 | 17:30:46 | 0 | quality-auditor | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 14 | 17:31:14 | 0 | orquestador | fin | APROBADO | 2 auditoría(s); última: APROBADO (score 89.3); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 2  
Evidencias rechazadas: 2  
Auditorías: 2 · Correcciones: 1
Duración: 6.9 min · Tokens: 1,318,294 entrada / 33,099 salida · 75 peticiones

**Estado final: APROBADO** — 2 auditoría(s); última: APROBADO (score 89.3); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
