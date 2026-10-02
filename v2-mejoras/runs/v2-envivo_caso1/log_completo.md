# Registro de ejecución (reconstruido) — v2-envivo_caso1

Reconstruido con `scripts/reconstruir_log.py` a partir de `delegaciones.jsonl` (traza que el runner escribe en código en cada delegación) y de los artefactos de cada etapa. La columna *Hora* es el momento en que terminó cada delegación y *Fuente* indica de dónde sale cada fila. El registro escrito por el orquestador se conserva sin cambios en `log.md`.

| # | Hora | Iter. | Componente | Evento | Estado | Detalle | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | 19:23:23 | 0 | orquestador | inicio | OK | Elabora el informe ejecutivo 'Tendencias emergentes de inteligencia artificial con potencial impacto empresarial durante los próximos tres años' para Horizonte Digital S.A.S. | log.jsonl |
| 2 | 19:23:59 | 0 | trend-scout:candidatas | investigacion_candidatas | OK | runs/v2-envivo_caso1/01a_candidatas.json, 7 tendencias, 0 evidencias | delegaciones.jsonl |
| 3 | 19:25:00 | 0 | trend-scout:tendencia:T1 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T1.json \| 1 tendencias \| 3 evidencias | delegaciones.jsonl |
| 4 | 19:25:16 | 0 | trend-scout:tendencia:T3 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T3.json \| 1 tendencia \| 4 evidencias | delegaciones.jsonl |
| 5 | 19:25:58 | 0 | trend-scout:tendencia:T4 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T4.json \| tendencias: 1 \| evidencias: 3 | delegaciones.jsonl |
| 6 | 19:26:03 | 0 | trend-scout:tendencia:T5 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T5.json 1 tendencia(s), 4 evidencia(s) | delegaciones.jsonl |
| 7 | 19:26:27 | 0 | trend-scout:tendencia:T6 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T6.json, 1, 4 | delegaciones.jsonl |
| 8 | 19:26:27 | 0 | trend-scout:tendencia:T2 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T2.json, 1, 4 | delegaciones.jsonl |
| 9 | 19:29:19 | 0 | trend-scout:tendencia:T7 | investigacion_tendencia | OK | runs/v2-envivo_caso1/01b_tendencias/T7.json \| 1 tendencia \| 3 evidencias | delegaciones.jsonl |
| 10 | 19:29:21 | 0 | orquestador | union_hallazgos | OK | 7 tendencias, 25 evidencias; 0 descartadas por el Scout | 01_union.json |
| 11 | 19:29:26 | 0 | orquestador | compuerta_contrato | ERROR_ESTRUCTURA | 7 tendencias, 25 evidencias, 0 violaciones, 3 advertencias | 02_contrato.json |
| 12 | 19:29:26 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E1 (T3): fuente de 2024-07-25, 27 meses | 02_contrato.json |
| 13 | 19:29:26 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E2 (T5): fuente de 2024-07-15, 27 meses | 02_contrato.json |
| 14 | 19:29:26 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E1 (T6): fuente de 2024-05-14, 29 meses | 02_contrato.json |
| 15 | 19:31:15 | 0 | trend-scout:corregir_estructura | investigacion_tendencia | OK | runs/v2-envivo_caso1/01_hallazgos_scout_corregido.json, 7 tendencias, 25 evidencias | delegaciones.jsonl |
| 16 | 19:31:21 | 0 | orquestador | compuerta_contrato | ERROR_ESTRUCTURA | 7 tendencias, 25 evidencias, 0 violaciones, 3 advertencias | 02_contrato.json |
| 17 | 19:31:21 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E1 (T3): fuente de 2024-07-25, 27 meses | 02_contrato.json |
| 18 | 19:31:21 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E2 (T5): fuente de 2024-07-15, 27 meses | 02_contrato.json |
| 19 | 19:31:21 | 0 | orquestador | advertencia | FUENTE_ANTIGUA | E1 (T6): fuente de 2024-05-14, 29 meses | 02_contrato.json |
| 20 | 19:31:33 | 0 | orquestador | fin | FALLIDO | no se llegó a auditar ningún informe | artefactos del run |

Violaciones registradas: 0  
Evidencias rechazadas: 0  
Auditorías: 0 · Correcciones: 0
Duración: 8.2 min · Tokens: 1,474,098 entrada / 69,739 salida · 69 peticiones

**Estado final: FALLIDO** — no se llegó a auditar ningún informe
