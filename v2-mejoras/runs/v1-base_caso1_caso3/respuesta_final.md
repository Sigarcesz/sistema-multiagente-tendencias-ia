1) Resumen ejecutivo (sección 1 del informe aprobado)

## 1. Resumen Ejecutivo

Este informe analiza siete tendencias de IA con evidencia validada y propone una clasificación clara para la toma de decisiones: cuáles tendencias observar, evaluar o incorporar en la estrategia de Horizonte Digital S.A.S.

- T1. Adopción y personalización de modelos de base (foundation models): Incorporar por su impacto alto y respaldo de adopción empresarial y inversión en generative AI [E2].
- T2. Regulación y gestión de riesgos (AI governance / TRiSM): Incorporar dado que marcos y obligaciones empujan a cambios operativos y de cumplimiento [E4].
- T3. Uso de IA por atacantes y necesidad de defensas AI-centradas en ciberseguridad: Incorporar por la evidencia de uso adversario y la doble cara de la IA en defensa y ataque [E5], [E6].
- T4. Automatización del desarrollo con asistentes de código y agentes: Evaluar mediante pilotos estructurados antes de escalamiento, por mejoras de productividad documentadas pero variabilidad por contexto [E7], [E8].
- T5. Generación y uso de datos sintéticos: Evaluar mediante proyectos piloto y marcos de validación, por interés creciente pero madurez emergente [E9], [E10].
- T6. Observabilidad y monitoreo de modelos (ML/AI observability): Incorporar prácticas y herramientas de observabilidad para soportar operación y cumplimiento [E11], [E12].
- T7. Despliegue en edge y aceleradores especializados: Evaluar la viabilidad por línea de producto y costo; la tendencia tiene potencial pero depende de inversión en hardware y optimizaciones [E13], [E14].

Recomendación principal: priorizar en horizonte inmediato la gobernanza de IA (TRiSM), la seguridad AI-centrada y un programa controlado de adopción de foundation models con observabilidad integrada, mientras se ejecutan pilotos en desarrollo asistido, datos sintéticos y edge para evaluar escalamiento futuro [E4], [E5], [E2], [E11].

2) Puntuación de calidad (auditoría final v2)
- Score global: 89.3
- Puntaje por criterio:
  - exactitud: 95
  - calidad_evidencia: 85
  - referencias: 95
  - profundidad: 80
  - claridad: 90
  - utilidad: 88

3) Estado final e iteraciones usadas
- Estado final: APROBADO
- Iteraciones de auditoría: 2 (auditoría v1 → corrección → auditoría v2)
- Correcciones aplicadas: 1 ciclo de corrección (3 observaciones corregidas)

4) Nombre del documento DOCX generado
- Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx

5) Ubicación del documento y del registro
- Documento: runs/v1-base_caso1_caso3/final/Informe_Tendencias_IA_Horizonte_Digital_2026-10-01.docx
- Registro (log): runs/v1-base_caso1_caso3/log.md

6) Violaciones y evidencias rechazadas durante el proceso
- Violaciones de responsabilidad (registradas tras validar contrato, estado ELIMINADO):
  1. ubicacion: $.tendencias[0].recomendaciones
     contenido_eliminado: ["Horizonte Digital debería invertir de inmediato en adopción y personalización de modelos de base (foundation models) en la empresa y asignarle un equipo dedicado.", "Se recomienda crear un comité de adopción de IA antes de fin de año."]
  2. ubicacion: T2.descripcion
     contenido_eliminado: "La empresa debería priorizar esta tendencia en su presupuesto de innovación."

- Evidencias rechazadas por la verificación de evidencia (estado RECHAZADA):
  1. E1 (T1) — motivo: La fuente respalda 'tens of thousands' y '85%' pero NO contiene la cifra "4.7x" (menciona "up to 4x"). URL: https://press.aboutamazon.com/2024/4/amazon-bedrock-launches-new-capabilities-as-tens-of-thousands-of-customers-choose-it-as-the-foundation-to-build-and-scale-secure-generative-ai-applications
  2. E3 (T2) — motivo: Contenido no legible / bloqueado (webfetch devolvió error); no fue posible confirmar la regulación ni las fechas. URL: https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A32024R1689

Fin.