# ArtifactForge

```text
ArtifactForge
     _________
 ___/  ___   \___
|___   \_/   ___|
    \_______/
```

ArtifactForge es una herramienta DFIR en TUI para indexar y analizar XML exportados por collectors de Redline. Se enfoca en parsing real de artefactos, timeline e identificación de hallazgos iniciales.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
python main.py --self-test
```

## Arquitectura

- `app/core/`: configuración, logging y bootstrap de SQLite.
- `app/models/`: entidades Pydantic/compat (`case`, `artifacts`, `timeline`, `findings`).
- `app/repositories/`: acceso a datos (sin SQL en UI).
- `app/services/`: discovery XML e indexación end-to-end.
- `app/parsers/`: `BaseParser`, `ParserRegistry`, parser dedicado de Prefetch y fallback XML.
- `app/timeline/` y `app/triage/`: construcción de eventos y heurísticas.
- `app/commands/`: parser y dispatcher de mini CLI.
- `app/ui/`: TUI Textual con menú principal, navegación izquierda (28%), análisis derecha (72%) y barra CLI inferior.

## Comandos CLI

Globales: `help`, `clear`, `reset`, `back`, `refresh`, `stats`, `history`, `show`, `open`, `export json|csv|md`.

Analíticos: `search`, `grep`, `filter`, `sort`, `group by`, `pivot`, `tree`, `children`, `parent`, `suspicious`, `listening`, `remote`, `port`, `from`, `to`, `around`.

## Limitaciones actuales

- El soporte profundo está implementado para Prefetch y XML genérico por tipo.
- Algunos artefactos se detectan y clasifican como `partial` o `detected_unmapped` hasta contar con parsers dedicados.
- En entornos sin `textual` instalado, la app cae en modo fallback por consola para evitar crash de import.

## Roadmap

- Parsers dedicados adicionales (AmCache, ShimCache, Jump Lists, Shellbags).
- Vistas de tabla paginadas con ordenamiento server-side por SQLite.
- Correlación avanzada proceso-red-persistencia y findings contextuales.
