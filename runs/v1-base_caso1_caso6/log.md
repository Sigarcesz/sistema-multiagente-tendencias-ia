# Registro de ejecución — v1-base_caso1_caso6

Inicio: 2026-10-01T17:26:31-05:00  
Fin: 2026-10-01T17:34:13-05:00  
Modo: prueba  
Solicitud: Ejecuta en modo prueba sobre runs/v1-base_caso1_caso6 (lee runs/v1-base_caso1_caso6/prueba.json).

| # | Hora | Paso | Iter. | Componente | Evento | Estado | Detalle | Artefactos |
|---|---|---|---|---|---|---|---|---|
| 1 | 17:26:31 | 0 | 0 | orquestador | inicio | OK | Ejecuta en modo prueba sobre runs/v1-base_caso1_caso6 (lee runs/v1-base_caso1_caso6/prueba.json). |  |
| 2 | 17:27:23 | 4 | 1 | report-writer | redaccion | OK | iteracion 1 | runs/v1-base_caso1_caso6/informe_v1.md |
| 3 | 17:28:55 | 5 | 1 | quality-auditor | auditoria | RECHAZADO | score 79.8; rechazos automáticos: 0; correcciones requeridas: 5 | runs/v1-base_caso1_caso6/auditoria_v1.json |
| 4 | 17:29:58 | 5 | 2 | report-writer | correccion | OK | correcciones aplicadas: 4; no_corregibles: 1 | runs/v1-base_caso1_caso6/respuesta_correcciones_v2.json |
| 5 | 17:30:46 | 5 | 2 | quality-auditor | auditoria | RECHAZADO | score 77.0; rechazos automáticos: 1; correcciones requeridas: 5 | runs/v1-base_caso1_caso6/auditoria_v2.json |
| 6 | 17:31:36 | 5 | 3 | report-writer | correccion | OK | 4 corregidas, 1 no_corregible (C4) | runs/v1-base_caso1_caso6/respuesta_correcciones_v3.json |
| 7 | 17:32:18 | 5 | 3 | quality-auditor | auditoria | RECHAZADO | score 81.8; umbrales_incumplidos: profundidad, global | runs/v1-base_caso1_caso6/auditoria_v3.json |
| 8 | 17:33:18 | 5 | 4 | report-writer | correccion | OK | He corregido 2 y marqué 2 como no corregibles | runs/v1-base_caso1_caso6/respuesta_correcciones_v4.json |
| 9 | 17:34:07 | 5 | 4 | quality-auditor | auditoria | RECHAZADO | score 76.0; umbrales_incumplidos: exactitud, profundidad, global | runs/v1-base_caso1_caso6/auditoria_v4.json |
| 10 | 17:34:13 | 7 | 4 | orquestador | fin | NO_APROBADO | umbrales incumplidos: exactitud 80 < 90; profundidad 50 < 70; global 76.0 < 85 | runs/v1-base_caso1_caso6/informe_v4.md |

Violaciones registradas: 0

**Estado final: NO_APROBADO** — umbrales incumplidos: exactitud 80 < 90; profundidad 50 < 70; global 76.0 < 85
