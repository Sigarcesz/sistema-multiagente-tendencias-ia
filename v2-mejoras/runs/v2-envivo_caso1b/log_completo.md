# Registro de ejecución (reconstruido) — v2-envivo_caso1b

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 22:59:47 | 0 | orquestador | inicio | OK | Elabora el informe ejecutivo 'Tendencias emergentes de inteligencia artificial con potencial impacto empresarial durante los próximos tres años' para Horizonte Digital S.A.S. El informe será utilizado por la alta dirección para decidir qué tendencias deben observarse, evaluarse o incorporarse a futu | log.jsonl |
| 2 | 23:00:15 | 0 | trend-scout:candidatas | investigacion_candidatas | OK | runs/v2-envivo_caso1b/01a_candidatas.json, 6 tendencias, 0 evidencias | delegaciones.jsonl |
| 3 | 23:01:38 | 0 | trend-scout:tendencia:T3 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T3.json, 1 tendencia, 4 evidencias | delegaciones.jsonl |
| 4 | 23:01:54 | 0 | trend-scout:tendencia:T4 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T4.json — 1 tendencia, 4 evidencias | delegaciones.jsonl |
| 5 | 23:01:55 | 0 | trend-scout:tendencia:T1 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T1.json, 1 tendencia, 3 evidencias | delegaciones.jsonl |
| 6 | 23:02:59 | 0 | trend-scout:tendencia:T5 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T5.json, 1 tendencia, 4 evidencias | delegaciones.jsonl |
| 7 | 23:03:02 | 0 | trend-scout:tendencia:T6 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T6.json, 1 tendencia, 3 evidencias | delegaciones.jsonl |
| 8 | 23:03:21 | 0 | trend-scout:tendencia:T2 | investigacion_tendencia | OK | runs/v2-envivo_caso1b/01b_tendencias/T2.json, 1, 3 | delegaciones.jsonl |
| 9 | 23:03:22 | 0 | orquestador | union_hallazgos | OK | 6 tendencias, 21 evidencias; 0 descartadas por el Scout | 01_union.json |
| 10 | 23:03:33 | 0 | orquestador | compuerta_contrato | OK | 6 tendencias, 21 evidencias, 0 violaciones, 3 advertencias | 02_contrato.json |
| 11 | 23:03:33 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E1 (T1): fuente de 2023-12-21, 34 meses | 02_contrato.json |
| 12 | 23:03:33 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E19 (T6): fuente de 2023-01, 45 meses | 02_contrato.json |
| 13 | 23:03:33 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E21 (T6): fuente de 2024-05-01, 29 meses | 02_contrato.json |
| 14 | 23:03:37 | 0 | orquestador | verificacion_mecanica | OK | 21 fuentes (21 desde caché, 21 legibles, 0 inaccesibles); cifras no encontradas en [] | 03_verificacion/mecanica.json |
| 15 | 23:03:58 | 0 | quality-auditor:verificacion_evidencia:T1 | verificacion_tendencia | OK | Tendencia T1: 3 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 16 | 23:04:17 | 0 | quality-auditor:verificacion_evidencia:T2 | verificacion_tendencia | OK | T2: 3 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 17 | 23:04:38 | 0 | quality-auditor:verificacion_evidencia:T3 | verificacion_tendencia | OK | T3: 4 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 18 | 23:04:59 | 0 | quality-auditor:verificacion_evidencia:T4 | verificacion_tendencia | OK | T4: 4 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 19 | 23:05:24 | 0 | quality-auditor:verificacion_evidencia:T5 | verificacion_tendencia | OK | T5: 4 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 20 | 23:05:44 | 0 | quality-auditor:verificacion_evidencia:T6 | verificacion_tendencia | OK | T6: 3 verificadas, 0 rechazadas. | delegaciones.jsonl |
| 21 | 23:05:46 | 0 | orquestador | verificacion_evidencia | OK | 21/21 evidencias válidas; 6/6 tendencias con respaldo; tipos: {'proveedor': 5, 'academica': 8, 'consultora': 6, 'organismo': 2} | 03_filtrado.json |
| 22 | 23:07:05 | 1 | report-writer:redaccion | redaccion | OK | runs/v2-envivo_caso1b/informe_v1.md | delegaciones.jsonl |
| 23 | 23:07:46 | 1 | quality-auditor:auditoria | auditoria | RECHAZADO | score 89.9; rechazos: ninguno; umbrales incumplidos: ['referencias 85 < 90'] | auditoria_v1.json |
| 24 | 23:08:47 | 2 | report-writer:correccion | correccion | OK | runs/v2-envivo_caso1b/informe_v2.md — correcciones aplicadas: 2, no_corregibles: 0 | delegaciones.jsonl |
| 25 | 23:09:20 | 2 | quality-auditor:auditoria | auditoria | APROBADO | score 89.5; rechazos: ninguno; umbrales incumplidos: ninguno | auditoria_v2.json |
| 26 | 23:09:38 | 0 | quality-auditor:publicacion | publicacion | OK | Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | final/ |
| 27 | 23:10:00 | 0 | orquestador | fin | APROBADO | 2 auditoría(s); última: APROBADO (score 89.5); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 2 · Correcciones: 1
Duración: 10.2 min · Tokens: 2,168,557 entrada / 86,542 salida · 147 peticiones

**Estado final: APROBADO** — 2 auditoría(s); última: APROBADO (score 89.5); documento: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
