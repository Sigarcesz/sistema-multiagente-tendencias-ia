# Registro de ejecución — v1-base_caso1_caso7

Inicio: 2026-10-01T17:26:52-05:00  
Fin: 2026-10-01T17:32:31-05:00  
Modo: prueba  
Solicitud: Ejecuta en modo prueba sobre runs/v1-base_caso1_caso7 (lee runs/v1-base_caso1_caso7/prueba.json)

| # | Hora | Paso | Iter. | Componente | Evento | Estado | Detalle | Artefactos |
|---|---|---|---|---|---|---|---|---|
| 1 | 17:26:52 | 0 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso7 (lee runs/v1-base_caso1_caso7/prueba.json) |  |
| 2 | 17:27:05 | 0 | 0 | prueba | inyeccion_prueba | INYECCION | Se insertó una afirmación citando [E99], evidencia que no existe. |  |
| 3 | 17:27:59 | 5 | 1 | quality_auditor | auditoria | RECHAZADO | score_global:80.2;umbrales_incumplidos: exactitud 88<90, referencias 50<90, global 80.2<85 | runs/v1-base_caso1_caso7/auditoria_v1.json |
| 4 | 17:29:19 | 5 | 2 | report_writer | correccion | PARCIAL | aplicadas 2; no_corregibles 1 | runs/v1-base_caso1_caso7/informe_v2.md, runs/v1-base_caso1_caso7/respuesta_correcciones_v2.json |
| 5 | 17:30:07 | 5 | 2 | quality_auditor | auditoria | RECHAZADO | score_global:84.8;umbrales_incumplidos: exactitud 85<90, global 84.8<85 | runs/v1-base_caso1_caso7/auditoria_v2.json |
| 6 | 17:31:21 | 5 | 3 | report_writer | correccion | COMPLETO | correcciones aplicadas: 3 | runs/v1-base_caso1_caso7/informe_v3.md, runs/v1-base_caso1_caso7/respuesta_correcciones_v3.json |
| 7 | 17:32:06 | 5 | 3 | quality_auditor | auditoria | APROBADO | score_global:89.4 | runs/v1-base_caso1_caso7/auditoria_v3.json |
| 8 | 17:32:28 | 6 | 0 | quality_auditor | publicacion | APROBADO | Documento generado: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | runs/v1-base_caso1_caso7/final/Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx |
| 9 | 17:32:31 | 7 | 0 | orquestador | fin | APROBADO | Proceso finalizado con publicación. |  |

Violaciones registradas: 0

**Estado final: APROBADO** — Proceso finalizado con publicación.
