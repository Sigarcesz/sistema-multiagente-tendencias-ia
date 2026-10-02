Estado: FALLIDO — error estructural en la validación del contrato

Qué hice
1. Inicié el run en runs/v2-envivo_caso1 y registré la solicitud en el log.
2. Delegué en el trend-scout (modo candidatas) y generó 7 candidatas (runs/v2-envivo_caso1/01a_candidatas.json).
3. Por cada candidata lancé trend-scout en modo tendencia (en paralelo). Se produjeron 7 archivos runs/v2-envivo_caso1/01b_tendencias/T1..T7.json.
4. Ejecuté scripts/unir_hallazgos.py → runs/v2-envivo_caso1/01_hallazgos_scout.json (7 tendencias, 25 evidencias).
5. Ejecuté scripts/validar_contrato.py sobre 01_hallazgos_scout.json → devolvió ERROR_ESTRUCTURA (código 2).
6. Devolví el JSON al trend-scout para corrección; el scout creó runs/v2-envivo_caso1/01_hallazgos_scout_corregido.json.
7. Volví a ejecutar scripts/validar_contrato.py sobre la versión corregida → volvió a devolver ERROR_ESTRUCTURA (segunda vez).
8. Por política: al segundo ERROR_ESTRUCTURA, el proceso termina con estado FALLIDO.
9. Generé el resumen final del run en runs/v2-envivo_caso1/log.md.

Motivo del fallo
- La ejecución de scripts/validar_contrato.py devolvió ERROR_ESTRUCTURA en dos intentos sucesivos. El primer intento reportó n_errores = 3; el segundo intento reportó n_errores = 24. El script detectó errores de estructura en los hallazgos que impiden continuar (detalles técnicos en runs/v2-envivo_caso1/02_contrato.json).

Estado final y artefactos relevantes
- Estado final: FALLIDO (detenido por ERROR_ESTRUCTURA en la compuerta de contrato).
- Archivo de hallazgos original generado por el scout: runs/v2-envivo_caso1/01_hallazgos_scout.json
- Archivo de hallazgos corregido enviado por el scout: runs/v2-envivo_caso1/01_hallazgos_scout_corregido.json
- Salida del validador / reporte de errores: runs/v2-envivo_caso1/02_contrato.json
- Registro del run (resumen y log de eventos): runs/v2-envivo_caso1/log.md

Qué contenía la última versión disponible (ubicación)
- Última versión de hallazgos (no validada): runs/v2-envivo_caso1/01_hallazgos_scout_corregido.json

Qué se necesitaría para destrabarlo (sin ejecutarlo yo)
- Corregir la estructura del JSON de hallazgos según las indicaciones detalladas en runs/v2-envivo_caso1/02_contrato.json. Específicamente:
  - Revisar las entradas que el validador marcó como errores de estructura (campos faltantes, formatos inválidos o identificadores duplicados) y aplicar las correcciones en el agente responsable (trend-scout).
  - Volver a ejecutar scripts/validar_contrato.py tras la corrección; si el validador pasa, continuar con la preparación de verificación y el resto del flujo.
- Si las correcciones estructurales no son suficientes, podría requerirse una segunda investigación (recolección de evidencia adicional o reindexado de documentos), pero eso solo se decide tras una validación exitosa del formato.

Notas finales
- No se produjo ninguna redacción de informe (report-writer) ni auditoría porque el proceso quedó detenido en la compuerta de contrato.
- Todos los eventos relevantes están registrados en runs/v2-envivo_caso1/log.md.

Si desea, puedo:
- Reintentar enviar una solicitud de corrección al trend-scout (aunque ya se hizo una corrección y la validación volvió a fallar; la política exige terminar tras la segunda falla), o
- Indicar los pasos concretos a un equipo humano para corregir los errores listados en runs/v2-envivo_caso1/02_contrato.json para poder reanudar el pipeline desde la compuerta de contrato.

Indique cómo prefiere proceder.