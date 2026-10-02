# Sistema multiagente para informes de tendencias de IA

Proyecto del curso **Tópicos Avanzados de IA (Universidad EIA, 2026-2)**: tres skills
reutilizables y un prompt orquestador en Claude Code que investigan, redactan, auditan y
publican un informe ejecutivo, sin que ningún agente asuma todo el proceso.

Caso: *"Tendencias emergentes de inteligencia artificial con potencial impacto empresarial
durante los próximos tres años"* para la empresa ficticia Horizonte Digital S.A.S.

## Estructura

```
runner/                    # motor OpenAI: main.py + herramientas.py
.claude/
  agents/
    orquestador.md         # prompt orquestador (agente principal)
    trend-scout.md         # subagente: investiga (web, sin redacción)
    report-writer.md       # subagente: redacta (sin acceso web)
    quality-auditor.md     # subagente: verifica, audita y publica
  skills/
    trend-scout/SKILL.md
    report-writer/SKILL.md
    quality-auditor/SKILL.md + scripts/   # verificación, decisión y DOCX
  settings.json            # permisos para scripts y búsqueda web
scripts/
  log.py                   # registro de ejecución (log.jsonl / log.md)
  validar_contrato.py      # compuerta de contrato: estructura, invasión de roles, recencia
  unir_hallazgos.py        # une las tendencias investigadas en paralelo (v2)
  preparar_verificacion.py # descarga paralela de fuentes y chequeo mecánico de cifras/extractos (v2)
  unir_verificacion.py     # reglas fail-closed y recálculo de confianza (v2)
  texto_fuentes.py         # descarga, caché y extracción de texto (compartido)
  reconstruir_log.py       # registro completo desde la traza del runner
  reporte_run.py           # reporte HTML: tablero, línea de tiempo, visor de evidencia (v2)
  comparar_runs.py         # compara runs lado a lado (v2)
  inyectar_fallo.py        # prepara los casos de prueba 2-7
  smoke_test.py            # prueba de los scripts con datos ficticios
tests/
  casos_de_prueba.md       # 8 casos con criterios de aprobación
  fixtures/sintetico/      # datos FICTICIOS solo para smoke_test.py
docs/
  diseno.md                # arquitectura, decisiones y cambios vs. originales
  reflexion.md             # guía del informe de reflexión
  originales/              # prompts entregados en Moodle
runs/                      # una carpeta por ejecución (evidencia)
```

## Dos motores, las mismas skills

Las skills, los prompts de los agentes y los scripts de control son comunes. Cambia solo
el motor que los ejecuta:

| Motor | Cómo se ejecuta | Qué usa |
|---|---|---|
| **OpenAI Agents SDK** (`runner/`) | `python -m runner.main` | `OPENAI_API_KEY` en `.env` |
| Claude Code | `claude --agent orquestador` | cuenta o API key de Anthropic |

`runner/main.py` carga los mismos `SKILL.md` y `.claude/agents/*.md` como instrucciones y
da a cada agente solo las herramientas de su rol (`runner/herramientas.py`).

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt`
- Una API key de OpenAI en `.env` (copiar `.env.ejemplo`)

## Uso (OpenAI)

```bash
# 0. Verificar los scripts (sin red ni modelo)
python scripts/smoke_test.py

# 1. Ejecución completa (caso 1)
python -m runner.main --run runs/v1-base_caso1

# 2. Casos de prueba sobre el run del caso 1
python scripts/inyectar_fallo.py --base runs/v1-base_caso1 --caso 4
python -m runner.main --prueba runs/v1-base_caso1_caso4
```

Cada run deja en `runs/<id>/` todos los artefactos y, generados por código al terminar:
`log_completo.md` (registro), `reporte_run.html` (tablero, línea de tiempo y visor de
evidencia), `uso.json` (tokens y tiempo por agente), `delegaciones.jsonl`, `scripts.jsonl`,
`herramientas.jsonl` y `descargas.jsonl` (trazas de cada paso).

```bash
# Comparar dos runs (p. ej. v1 contra v2)
python scripts/comparar_runs.py runs/v1-base_caso1 runs/v2-mejoras_caso1 --salida docs/comparacion_caso1.md
```

Ver `tests/casos_de_prueba.md` para los criterios de cada caso y `docs/mejoras_v2.md` para
los cambios de la versión 2.
