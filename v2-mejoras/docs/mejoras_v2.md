# Versión 2: menos latencia y más control de calidad

La versión 1 (`v1-base`) cumplió los ocho casos de prueba. Los runs dejaron ver dónde se iba
el tiempo y qué controles dependían de que el modelo cumpliera una instrucción. Esta versión
ataca esos dos frentes sin cambiar el contrato con el usuario ni la estructura del informe.

## Diagnóstico (run v1 del caso 1, 9,3 min)

| Etapa | Tiempo | Observación |
|---|---|---|
| Trend Scout | 283 s (51 %) | 908 mil tokens de entrada en 11 peticiones: cada página leída quedaba en el contexto |
| Verificación de evidencia | 100 s | el auditor volvía a descargar, una por una, las mismas páginas que ya había leído el Scout |
| Redacción | 70 s | |
| Auditoría y publicación | 40 s | |
| Orquestador | ~60 s propios | solo coordina, pero razonaba con el esfuerzo por defecto |

Problemas de control observados:
- El orquestador no registró los eventos en dos de siete corridas.
- Tendencias con una sola evidencia tras el filtrado conservaban confianza "alta"; en el
  caso 6 eso generó un ir y venir entre escritor y auditor.
- La regla de recencia (24 meses) estaba solo en el prompt y se incumplía.
- Una tendencia se sostenía solo con fuentes de proveedores con confianza "alta".
- Una fuente legítima (EUR-Lex) se perdía en todas las corridas por no ser legible.

## Cambios de latencia

| # | Cambio | Dónde |
|---|---|---|
| L1 | **Investigación en dos fases.** Un Scout identifica candidatas (sin abrir páginas) y luego un Scout por tendencia trabaja en paralelo, con contexto propio y pequeño. Un script une y renumera. | `trend-scout/SKILL.md`, `orquestador.md`, `unir_hallazgos.py` |
| L2 | **Cada fuente se descarga una vez.** `web_fetch` guarda el texto en `fuentes_cache/`; la verificación lo reutiliza y descarga en paralelo solo lo que falte. | `texto_fuentes.py`, `preparar_verificacion.py` |
| L3 | **Verificación en paralelo por tendencia.** Un auditor por tendencia, leyendo el texto local en vez de la web. | `quality-auditor/SKILL.md`, `orquestador.md` |
| L4 | **Menos texto por lectura.** `web_fetch` devuelve el inicio de la página y las líneas con cifras o con las palabras buscadas (~5.000 caracteres), no la página entera. | `texto_fuentes.extracto_relevante` |
| L5 | **Esfuerzo de razonamiento por rol.** El orquestador corre con esfuerzo `low`; los especialistas con el del modelo. Configurable en `.env`. | `runner/main.py` |
| L6 | **Concurrencia con límite.** Como máximo 4 especialistas a la vez (`MAX_PARALELO`), para no cambiar latencia por errores de límite de tasa. | `runner/main.py` |
| L7 | **Progreso visible y medición por paso.** La terminal muestra cada herramienta en uso; quedan registradas duraciones de delegaciones, scripts, herramientas y descargas. | `runner/main.py`, `runner/herramientas.py` |

Lo que no aplicó del análisis de latencia: no había esperas fijas ni reintentos con espera
excesiva (el SDK ya maneja los reintentos).

## Cambios de calidad

| # | Cambio | Dónde |
|---|---|---|
| Q1 | **Chequeo mecánico contra la fuente.** Un script comprueba que cada cifra declarada y el extracto textual aparezcan en la página descargada. Una cifra ausente rechaza la evidencia aunque el auditor diga lo contrario. | `preparar_verificacion.py`, `unir_verificacion.py` |
| Q2 | **Extracto textual por evidencia.** El Scout copia la frase de la página que contiene la cifra (máx. 25 palabras). | `trend-scout/SKILL.md`, `validar_contrato.py` |
| Q3 | **Tipo de fuente obligatorio** (organismo, académica, consultora, proveedor, medio). | `validar_contrato.py` |
| Q4 | **Recencia en código.** Fuentes de más de 24 meses quedan como advertencia registrada. | `validar_contrato.py` |
| Q5 | **Confianza recalculada tras el filtrado.** Baja de alta a media con menos de 2 evidencias, solo fuentes de proveedores o todas antiguas. El escritor usa ese nivel tal cual. | `unir_verificacion.py`, `report-writer/SKILL.md` |
| Q6 | **Resumen ejecutivo en pirámide.** Conclusión primero, tabla de clasificación, argumentos con evidencia. | `report-writer/SKILL.md` |
| Q7 | **Registro por código.** El runner registra delegaciones, scripts, herramientas y descargas; al final genera el registro completo y el reporte. | `runner/`, `reconstruir_log.py` |
| Q8 | **Reporte del run.** HTML con tablero, línea de tiempo (se ve el paralelismo), visor de evidencia y el informe con cada [E#] enlazado. | `reporte_run.py` |
| Q9 | **CI.** Lint y smoke test en cada push. | `.github/workflows/ci.yml` |

**Independencia de la verificación.** El auditor reutiliza el texto que descargó el código,
no lo que el Scout interpretó. La decisión de qué respalda cada página sigue siendo de un
agente distinto al que la citó, y las reglas duras (cifras, URL inexistente) son de un script.

## Cómo comparar

```bash
python -m runner.main --run runs/v2-mejoras_caso1
python scripts/comparar_runs.py runs/v1-base_caso1 runs/v2-mejoras_caso1 --salida docs/comparacion_caso1.md
```

Para que la comparación sea justa: mismo modelo (`MODELO=gpt-5-mini`) y misma solicitud. Los
casos 2 a 7 se repiten sobre `runs/v2-mejoras_caso1` con `scripts/inyectar_fallo.py`.

Las mejoras de tiempo son una proyección a partir de la v1 hasta que el run v2 las mida. El
paralelismo depende de que el modelo orquestador emita varias delegaciones en el mismo turno;
si no lo hace, el flujo es correcto pero secuencial, y la línea de tiempo del reporte lo muestra.
