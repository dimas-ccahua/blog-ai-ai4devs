---
name: analisis-de-amenazas
description: Genera el análisis de amenazas fechado de FlowSync frente al OWASP Top 10 for LLM Applications 2025 y lo escribe en docs/seguridad/analisis-de-amenazas-AAAA-MM-DD.md. Procedimiento fijo. Usar cuando se pida un análisis de amenazas o /analisis-de-amenazas.
---
# Análisis de amenazas — OWASP Top 10 for LLM Applications 2025

Esto es un procedimiento, no una opinión. Cada ejecución recorre los mismos pasos, en el mismo orden,
y produce un documento con la misma forma. No añadas secciones, no las reordenes y no te saltes
ninguna.

## Prohibiciones

1. **No afirmes que se comprobó lo que no se abrió.** Solo puedes citar en «Qué se miró» un archivo
   que hayas abierto durante esta ejecución. Una búsqueda (`grep`) sobre un directorio se cita como
   búsqueda, con su patrón y su resultado, y no convierte en «mirados» los archivos que recorrió. Lo
   que no abriste no se cita, y sobre su contenido no se razona.
2. **No rellenes una entrada con generalidades del catálogo.** Prohibido explicar qué es la amenaza
   en abstracto o enumerar mitigaciones de manual. Cada frase se refiere a un archivo, una
   configuración o un flujo concreto de este repositorio.

Si para una entrada no hay nada en este sistema que mirar, la decisión es `fuera de alcance`, con su
motivo y su disparador. Es una respuesta válida, no un hueco que haya que rellenar.

Tampoco se leen los valores de los archivos `.env` ni las filas de la base de datos local: para saber
qué hay basta con los nombres de las claves y el esquema.

## Paso 1 — Inventario de superficies

Dos superficies en las que un modelo de lenguaje lee o escribe. Para cada una, apunta qué archivos
abriste: la lista entera va en el documento.

1. **Producto** (`backend/`, `frontend/`). ¿Integra hoy algún modelo? Se decide mirando el código,
   no suponiéndolo:
   - dependencias en `backend/package.json` y `frontend/package.json`;
   - búsqueda en `backend/app/`, `backend/start/`, `backend/config/` y `frontend/src/` de SDK y
     llamadas a modelos (`anthropic`, `openai`, `@ai-sdk`, `langchain`, `ollama`, `llm`, `embedding`,
     `completion`, `chat`, `prompt`) y de variables de entorno que apunten a un proveedor
     (`backend/start/env.ts`, `backend/.env.example`).
2. **Harness de desarrollo**:
   - `CLAUDE.md`, y qué es `AGENTS.md` (comprueba si es un enlace);
   - `.claude/`: `settings.json`, `settings.local.json` si existe, `hooks/`, `skills/`, `agents/`,
     `commands/`;
   - `.mcp.json`;
   - `.github/workflows/`.

## Paso 2 — Las diez entradas

Recórrelas todas, en este orden, sin saltarte ninguna:

| Código | Entrada |
|---|---|
| LLM01 | Prompt Injection |
| LLM02 | Sensitive Information Disclosure |
| LLM03 | Supply Chain |
| LLM04 | Data and Model Poisoning |
| LLM05 | Improper Output Handling |
| LLM06 | Excessive Agency |
| LLM07 | System Prompt Leakage |
| LLM08 | Vector and Embedding Weaknesses |
| LLM09 | Misinformation |
| LLM10 | Unbounded Consumption |

Cada entrada se evalúa contra las dos superficies del paso 1 y tiene **dos campos, y solo dos**:

- **Qué se miró**: archivos concretos, con ruta relativa a la raíz del repositorio.
- **Decisión**: exactamente uno de estos tres valores, seguido de su justificación:
  - `mitigado`: con qué, nombrando el archivo, el hook, la regla o la configuración.
  - `aceptado`: por qué, y qué lo volvería inaceptable.
  - `fuera de alcance`: por qué, y cuándo se reabre. El disparador tiene que ser observable, por
    ejemplo «cuando `backend/package.json` incluya un SDK de modelo».

## Paso 3 — Formato del documento

Exactamente esta forma, sin secciones de más:

```markdown
# Análisis de amenazas — FlowSync — AAAA-MM-DD

- **Fecha:** AAAA-MM-DD (UTC)
- **Commit:** <git rev-parse --short HEAD>
- **Alcance:** <una sola frase>

## Superficies

### Producto
<si integra o no un modelo, y la evidencia>

### Harness
<qué piezas hay>

### Archivos abiertos
- `ruta/uno`
- `ruta/dos`

### Búsquedas
- `<patrón>` en `ruta/` — <sin resultados | archivos con coincidencia>

## LLM01 — Prompt Injection

**Qué se miró:** `ruta`, `ruta`

**Decisión:** `mitigado` | `aceptado` | `fuera de alcance` — <justificación>

<!-- … una sección igual por entrada, hasta LLM10 -->

## Fuera de alcance y cuándo se reabre

| Entrada | Motivo | Disparador para reabrir |
|---|---|---|
```

La tabla final recoge **todas** las entradas con decisión `fuera de alcance`. Si no hay ninguna, se
dice en una línea en lugar de la tabla.

## Paso 4 — El archivo

1. Fecha: `date -u +%F`. Commit: `git rev-parse --short HEAD`.
2. Ruta: `docs/seguridad/analisis-de-amenazas-<fecha>.md`. Si ya existe uno con la fecha de hoy, se
   sobrescribe.
3. Antes de darlo por terminado, comprueba:
   - que están las diez secciones, de LLM01 a LLM10 y en orden;
   - que cada sección tiene solo los dos campos;
   - que cada decisión es uno de los tres valores;
   - que toda ruta citada en «Qué se miró» aparece en «Archivos abiertos» o, si es un directorio,
     en «Búsquedas»;
   - que cada `fuera de alcance` aparece en la tabla final.
4. Esta skill no hace commits. El documento se commitea siguiendo las reglas de proceso de `CLAUDE.md`.
