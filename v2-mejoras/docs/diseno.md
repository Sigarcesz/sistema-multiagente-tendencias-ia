# Diseño del sistema

## Arquitectura

```
Usuario
  │  claude --agent orquestador
  ▼
Orquestador (Estratega IA) ── herramientas: Agent(3 especialistas), Read, Bash
  │
  ├── Skill 1: Trend Scout ─────────────► 01_hallazgos_scout.json
  │        │
  │        ▼  compuerta de contrato (scripts/validar_contrato.py)
  │        │     · estructura · elimina y registra recomendaciones del Scout  ── caso 3
  │        ▼
  ├── Skill 3: Auditor, modo verificación de evidencia
  │        │     · URLs existen · la página respalda la afirmación y la cifra   ── caso 2
  │        ▼  03_hallazgos_validados.json   (lo único que ve el escritor)
  │
  ├── Skill 2: Report Writer ───────────► informe_vN.md
  │        │
  │        ▼
  └── Skill 3: Auditor, modo auditoría
           │     · verificar_informe.py: cifras, citas, recomendaciones       ── casos 4, 5
           │     · rúbrica del modelo + decidir_estado.py (pesos y umbrales)
           ├── APROBADO  → modo publicación → final/*.docx                     ── caso 1
           └── RECHAZADO → corrección del escritor → nueva auditoría
                           (máx. 3 correcciones → NO_APROBADO, sin DOCX)       ── caso 6
```

## Skills, subagentes y orquestador: qué hace cada pieza

- **Skill** (`.claude/skills/<rol>/SKILL.md`): el procedimiento reutilizable del rol:
  qué hace, qué no hace, formato de salida, escalas, rúbrica. Es independiente de este
  proyecto: otro orquestador podría usar la misma skill.
- **Subagente** (`.claude/agents/<rol>.md`): el contenedor de ejecución. Precarga su skill,
  corre en un contexto aislado (no ve la conversación ni el trabajo de los otros) y tiene
  solo las herramientas de su rol. El escritor no tiene acceso web: no puede "investigar
  un poquito" aunque quiera.
- **Orquestador** (`.claude/agents/orquestador.md`): el prompt orquestador. Corre como
  agente principal y solo puede delegar en los tres especialistas, leer archivos y ejecutar
  scripts. No tiene búsqueda web ni escritura de archivos.

## Independencia del proveedor de modelos

Las skills y los prompts son texto; las reglas críticas son scripts de Python. Ninguno
depende del proveedor. Por eso el sistema corre con dos motores:

- **Claude Code**: subagentes nativos (`.claude/agents/`) con herramientas restringidas.
- **OpenAI Agents SDK** (`runner/`): carga los mismos archivos como instrucciones. Cada
  especialista es un agente independiente que el orquestador invoca como herramienta,
  con un contexto nuevo en cada delegación. Las restricciones de herramientas se aplican
  en código: el escritor solo tiene lectura y escritura, solo se puede escribir dentro de
  `runs/`, el `.env` no se puede leer y cada rol solo ejecuta su lista blanca de scripts.

## Decisiones de diseño

1. **Contratos en JSON con IDs.** Tendencias `T#`, evidencias `E#`, riesgos `RG#`,
   oportunidades `OP#`, recomendaciones `R#`, correcciones `C#`. Los IDs hacen que la
   trazabilidad sea verificable por un script y no una cuestión de interpretación.
2. **Las transiciones se deciden con archivos, no con mensajes.** El orquestador lee
   `02_contrato.json`, `03_filtrado.json` y `auditoria_vN.json`. Un agente que "dice" que
   terminó bien no basta.
3. **Reglas críticas en código, juicio en el modelo.** Lo verificable mecánicamente
   (estructura, cifras, citas, vínculos de recomendaciones, umbrales, límite de
   publicación) lo hacen scripts. Lo que requiere lectura (¿la fuente respalda la
   afirmación?, ¿el razonamiento es sólido?) lo hace el modelo auditor.
4. **Verificación de evidencia por el auditor, antes del escritor.** Nadie valida su propio
   trabajo: ni el Scout sus fuentes, ni el orquestador el contenido. El auditor se invoca en
   dos puntos del flujo.
5. **Fail-closed.** Evidencia sin veredicto, URL inaccesible o página que no se puede leer
   se rechazan. Es preferible perder una tendencia que sostenerla con una fuente dudosa.
6. **Límite de iteraciones explícito.** Tres correcciones como máximo; al agotarse, el
   estado es `NO_APROBADO` y `generar_docx.py` se niega a publicar.
7. **El escritor no puede introducir números propios.** Cuenta en palabras, no pone metas
   en los indicadores y solo usa cifras de la evidencia citada.

## Cambios respecto a los prompts originales (`docs/originales/`)

| Original | Problema | Cambio |
|---|---|---|
| Orquestador: "repetir hasta obtener aprobación" | Ciclo infinito; contradice el caso 6 | Límite de 3 correcciones y estado `NO_APROBADO` |
| Orquestador pasa la investigación directo al escritor | Una fuente inventada llega al informe (caso 2) | Compuerta de contrato + verificación de evidencia por el auditor |
| Nadie verifica que el Scout no recomiende | Caso 3 sin control | `validar_contrato.py` elimina y registra la violación |
| Auditor recibe solo el borrador | No puede contrastar cifras (caso 4) | Recibe también los hallazgos validados; `verificar_informe.py` compara números |
| "Recomendaciones injustificadas" sin definición | Caso 5 depende del criterio del modelo | Cada recomendación declara evidencia, riesgo, oportunidad e indicador |
| Score global sin pesos | "≥ 85" no es verificable | Pesos explícitos y cálculo en `decidir_estado.py` |
| "Si existen errores → RECHAZADO" ambiguo con los umbrales | Un informe con una cifra inventada podría pasar por promedio | Rechazos automáticos independientes del score |
| Formato de texto libre del Scout | No verificable automáticamente | Mismo contenido en JSON, con IDs |
| Sin registro | No hay evidencia de ejecución | `log.jsonl` + `log.md` por run |
| Solo salida para el caso aprobado | — | Salida definida para `NO_APROBADO` y `FALLIDO` |

## Artefactos de un run

| Archivo | Lo produce | Contenido |
|---|---|---|
| `01_hallazgos_scout.json` | Trend Scout | Investigación cruda |
| `02_hallazgos_contrato.json`, `02_contrato.json` | `validar_contrato.py` | Hallazgos saneados y violaciones |
| `03_verificacion_fuentes.json` | `preparar_verificacion.py` (v2; en v1 `verificar_fuentes.py`) | Estado HTTP de cada URL |
| `03_verificacion_evidencia.json` | Auditor | Veredicto por evidencia |
| `03_hallazgos_validados.json`, `03_filtrado.json` | `unir_verificacion.py` (v2; en v1 `aplicar_verificacion.py`) | Lo único que lee el escritor |
| `informe_vN.md` | Report Writer | Borrador versión N |
| `respuesta_correcciones_vN.json` | Report Writer | Qué corrigió y qué no |
| `verificacion_informe_vN.json` | `verificar_informe.py` | Hallazgos mecánicos |
| `auditoria_borrador_vN.json` | Auditor | Puntajes y correcciones de juicio |
| `auditoria_vN.json` | `decidir_estado.py` | Estado final de la versión N |
| `final/*.docx` | `generar_docx.py` | Solo si APROBADO |
| `log.jsonl`, `log.md` | `log.py` | Registro de la ejecución |

## Limitaciones conocidas

- `verificar_informe.py` detecta cifras escritas con dígitos; una cifra inventada escrita en
  palabras ("casi la mitad") la debe detectar el auditor por juicio.
- Que una página exista y mencione una cifra no garantiza que la fuente sea confiable ni
  que la cifra se use en su contexto correcto.
- Sitios que bloquean bots se rechazan aunque sean legítimos (costo del fail-closed).
- La revisión de juicio del auditor usa un modelo de la misma familia que el escritor;
  puede compartir sesgos.
