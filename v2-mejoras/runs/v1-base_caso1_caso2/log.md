# Registro de ejecución — v1-base_caso1_caso2

Inicio: 2026-10-01T17:22:34-05:00  
Fin: 2026-10-01T17:27:30-05:00  
Modo: prueba  
Solicitud: Ejecutar en modo prueba sobre runs/v1-base_caso1_caso2 (lee runs/v1-base_caso1_caso2/prueba.json).

| # | Hora | Paso | Iter. | Componente | Evento | Estado | Detalle | Artefactos |
|---|---|---|---|---|---|---|---|---|
| 1 | 17:22:34 | 0 | 0 | orquestador | inicio | OK | Ejecutar en modo prueba sobre runs/v1-base_caso1_caso2 (lee runs/v1-base_caso1_caso2/prueba.json). |  |
| 2 | 17:22:43 | 0 | 0 | prueba | inyeccion_prueba | INFO | Se agregó la evidencia E15 con una fuente inventada (dominio inexistente). |  |
| 3 | 17:22:53 | 2 | 0 | contrato | validar_contrato | OK | {"estado": "OK", "tendencias": 7, "evidencias": 15, "n_errores": 0, "n_violaciones": 0} | runs/v1-base_caso1_caso2/02_hallazgos_contrato.json, runs/v1-base_caso1_caso2/02_contrato.json |
| 4 | 17:24:46 | 3 | 0 | verificacion_evidencia | evidencia_rechazada | RECHAZADA | La página contiene 'tens of thousands' y '85%' pero no aparece la cifra '4.7x' mencionada en la afirmación. | https://press.aboutamazon.com/2024/4/amazon-bedrock-launches-new-capabilities-as-tens-of-thousands-of-customers-choose-it-as-the-foundation-to-build-and-scale-secure-generative-ai-applications |
| 5 | 17:24:50 | 3 | 0 | verificacion_evidencia | evidencia_rechazada | RECHAZADA | URL inaccesible (conexion: HTTPSConnectionPool(host='www.observatorio-latam-prospectiva-ia.org', port=443): Max retries exceeded with url: /informes/2026/adopcion-agentes-autonomos.pdf (C)) | https://www.observatorio-latam-prospectiva-ia.org/informes/2026/adopcion-agentes-autonomos.pdf |
| 6 | 17:24:53 | 3 | 0 | verificacion_evidencia | evidencia_rechazada | RECHAZADA | La página EUR-Lex no devuelve texto legible (bloqueo/dinámica); no es posible confirmar el contenido. | https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A32024R1689 |
| 7 | 17:24:56 | 3 | 0 | verificacion_evidencia | verificacion_evidencia | OK | Tendencias válidas: 7; Evidencias válidas: 12; Evidencias rechazadas: 3 | runs/v1-base_caso1_caso2/03_filtrado.json, runs/v1-base_caso1_caso2/03_hallazgos_validados.json |
| 8 | 17:26:12 | 4 | 0 | report_writer | redaccion | OK | iteracion 1 | runs/v1-base_caso1_caso2/informe_v1.md |
| 9 | 17:27:02 | 5 | 0 | auditoria | auditoria | APROBADO | score_global: 88.6 | runs/v1-base_caso1_caso2/auditoria_v1.json |
| 10 | 17:27:23 | 6 | 0 | publicacion | publicacion | OK | Documento publicado: Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx | runs/v1-base_caso1_caso2/final/Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx |
| 11 | 17:27:30 | 7 | 0 | fin | fin | APROBADO | Iteraciones auditoría: 1; Correcciones aplicadas: 0 |  |

Violaciones registradas: 0

**Estado final: APROBADO** — Iteraciones auditoría: 1; Correcciones aplicadas: 0
