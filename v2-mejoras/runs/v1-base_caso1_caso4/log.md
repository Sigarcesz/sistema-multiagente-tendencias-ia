# Registro de ejecución — v1-base_caso1_caso4

Inicio: 2026-10-01T17:25:11-05:00  
Fin: 2026-10-01T17:28:45-05:00  
Modo: prueba  
Solicitud: Ejecuta en modo prueba sobre runs/v1-base_caso1_caso4 (lee runs/v1-base_caso1_caso4/prueba.json).

| # | Hora | Paso | Iter. | Componente | Evento | Estado | Detalle | Artefactos |
|---|---|---|---|---|---|---|---|---|
| 1 | 17:25:11 | 0 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso4 (lee runs/v1-base_caso1_caso4/prueba.json). |  |
| 2 | 17:27:20 | 5 | 1 | quality-auditor | auditoria | RECHAZADO | score 79.5; umbrales incumplidos: exactitud 60 < 90; referencias 88 < 90; global 79.5 < 85 | runs/v1-base_caso1_caso4/auditoria_v1.json |
| 3 | 17:27:24 | 5 | 2 | report-writer | correccion | OK | correcciones aplicadas: 3 | runs/v1-base_caso1_caso4/informe_v2.md, runs/v1-base_caso1_caso4/respuesta_correcciones_v2.json |
| 4 | 17:28:17 | 5 | 2 | quality-auditor | auditoria | APROBADO | score 89.8 | runs/v1-base_caso1_caso4/auditoria_v2.json |
| 5 | 17:28:40 | 6 | 2 | quality-auditor | publicacion | OK | Documento publicado | runs/v1-base_caso1_caso4/final/Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx |
| 6 | 17:28:45 | 7 | 2 | orquestador | fin | APROBADO | Informe aprobado y publicado | runs/v1-base_caso1_caso4/final/Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx |

Violaciones registradas: 0

**Estado final: APROBADO** — Informe aprobado y publicado
