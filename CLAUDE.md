# Sistema multiagente de informes de tendencias (Tópicos Avanzados de IA, EIA 2026-2)

Tres especialistas coordinados por un orquestador producen un informe ejecutivo sobre
tendencias de IA para la empresa ficticia Horizonte Digital S.A.S.

**Todo el proyecto vive en `v2-mejoras/`** (desde 2026-10-01; v1 queda en el historial de git,
commit `047813c`). Las rutas de abajo son relativas a esa carpeta y los comandos se corren desde ahí.

- Orquestador: `.claude/agents/orquestador.md` (se ejecuta con `claude --agent orquestador`).
- Especialistas (subagentes con contexto aislado): `.claude/agents/{trend-scout,report-writer,quality-auditor}.md`.
- Skills reutilizables (el procedimiento de cada rol): `.claude/skills/*/SKILL.md`.
- Motor alternativo con la API de OpenAI: `runner/` (`python -m runner.main`), que reutiliza
  las mismas skills, prompts y scripts.
- Scripts deterministas: `scripts/` (orquestador) y `.claude/skills/quality-auditor/scripts/` (auditor).

Convenciones:
- Cada ejecución vive en `runs/<id>/`; los artefactos se numeran por etapa y versión. No se borran:
  son la evidencia del proyecto.
- Idioma de trabajo y de los entregables: español.
- `docs/originales/` contiene los prompts entregados en Moodle; no se modifican.
- Python: usar `python3`, o `python` si `python3` no existe (Windows).
