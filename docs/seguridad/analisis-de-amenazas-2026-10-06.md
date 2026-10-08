# Análisis de amenazas — blog-ai — 2026-10-06

- **Fecha:** 2026-10-06 (UTC)
- **Commit:** 7c0c258 (con cambios sin commitear: endpoint `POST /resumir` y `app/servicios/limite.py`)
- **Alcance:** El servicio blog-ai (FastAPI + pgvector + Ollama) y su harness de Claude Code, tal como están en el árbol de trabajo.

## Superficies

### Producto
Sí integra modelos. `app/configuracion.py` apunta a Ollama (`ollama_url`, `http://localhost:11434`) con dos modelos locales: `nomic-embed-text:latest` para embeddings (`app/servicios/embeddings.py`, `/api/embed`) y `qwen2.5:3b-instruct` para generación (`app/servicios/generacion.py`, `/api/chat`). No hay SDK de proveedor: las llamadas van con `httpx` (`requirements.txt`). Los modelos se usan en `POST /indexar` (embeddings de los posts), `POST /buscar` (embedding de la consulta), `POST /preguntar` (RAG) y `POST /resumir` (resumen de un texto arbitrario), todos en `app/main.py`. El índice vive en la tabla `fragmentos` de PostgreSQL/pgvector (`app/base_de_datos.py`), en el contenedor de `docker-compose.yml`.

### Harness
`CLAUDE.md` (dos reglas: comentario `Sin resultados:` y contrato en español); `.claude/settings.json` con dos hooks `PostToolUse` y sin bloque de permisos; `.claude/hooks/regla.sh`, que ejecuta el comprobador de la regla en este repositorio y en `../blog-api` (`../blog-api/.claude/hooks/regla-sin-resultados.mjs`) tras cada `Write`, `Edit` y `Bash`; `.claude/hooks/marcador.sh`, que anota fecha, herramienta y ruta en `MARCADORES-blog-ai.txt`; 13 skills en `.claude/skills/` (una de marcador, `analisis-de-amenazas` copiada de flowsync-ai4devs, y once de OpenSpec); 11 comandos en `.claude/commands/opsx/`. No hay `AGENTS.md`, `.mcp.json`, `.claude/settings.local.json`, `.claude/agents/` ni `.github/workflows/`.

### Archivos abiertos
- `requirements.txt`
- `app/main.py`
- `app/configuracion.py`
- `app/esquemas.py`
- `app/base_de_datos.py`
- `app/servicios/embeddings.py`
- `app/servicios/generacion.py`
- `app/servicios/indice.py`
- `app/servicios/limite.py`
- `.env.example`
- `db/init.sql`
- `docker-compose.yml`
- `README.md` (líneas 140-215)
- `CLAUDE.md`
- `.claude/settings.json`
- `.claude/hooks/regla.sh`
- `.claude/hooks/marcador.sh`
- `.claude/skills/marcador-blog-ai/SKILL.md`

### Búsquedas
- existencia de `backend/`, `frontend/`, `backend/package.json`, `frontend/package.json` (rutas que pide la skill, heredadas de FlowSync) — no existen
- existencia de `AGENTS.md`, `.mcp.json`, `.github/workflows/`, `.claude/settings.local.json`, `.claude/agents/` — no existen
- `anthropic|openai|@ai-sdk|langchain|ollama|llm|embedding|completion|chat|prompt` en `app/` — coincidencias en `app/main.py`, `app/configuracion.py`, `app/esquemas.py`, `app/base_de_datos.py`, `app/servicios/embeddings.py`, `app/servicios/generacion.py`, `app/servicios/indice.py`
- `OLLAMA|MODELO` en `.env.example` — `OLLAMA_URL`, `MODELO_EMBEDDINGS`, `MODELO_GENERACION`
- `git push|curl|rm -rf|allowed-tools|WebFetch|http` en `.claude/skills/` y `.claude/commands/` — sin resultados
- `^up:` en `Makefile` — `uvicorn app.main:app --port 8402 --reload --reload-dir app`, sin `--host`
- listado de `../blog-api/.claude/hooks/` — `marcador.sh`, `regla.sh`, `regla-sin-resultados.mjs`

## LLM01 — Prompt Injection

**Qué se miró:** `app/servicios/generacion.py`, `app/main.py`, `app/esquemas.py`, `app/servicios/indice.py`

**Decisión:** `aceptado` — En `/resumir`, `resumir()` de `app/servicios/generacion.py` mete el texto entre marcas `<documento-{etiqueta}>` con etiqueta aleatoria por petición y repite la instrucción después (`RECORDATORIO_RESUMEN`); el propio comentario del archivo dice que eso reduce la inyección y no la elimina. En `/preguntar`, `responder()` concatena la `consulta` del lector y los fragmentos del índice en el mensaje sin delimitarlos como datos. Se acepta porque la salida del modelo en ambos casos es solo un `str` que `app/main.py` devuelve en `respuesta` o `resumen`, sin herramientas ni acciones encadenadas. Se vuelve inaceptable si la salida de `_chat()` pasa a decidir alguna acción (llamadas a herramientas, escrituras en `fragmentos`, peticiones salientes) o si `/indexar` empieza a recibir posts de autores no fiables.

## LLM02 — Sensitive Information Disclosure

**Qué se miró:** `app/servicios/indice.py`, `app/esquemas.py`, `app/base_de_datos.py`, `.env.example`, `app/configuracion.py`

**Decisión:** `mitigado` — Lo único que el modelo de generación ve son fragmentos de la tabla `fragmentos` y el texto que manda el cliente. `indexar()` en `app/servicios/indice.py` solo escribe posts con `estado == "publicado"` y además borra del índice los que llegan como borrador (`_borrar_post`), así que un borrador no puede acabar en el contexto de `/preguntar`. `PostEntrante` en `app/esquemas.py` declara el `estado` como `Literal["borrador", "publicado"]` para que el filtro no dependa del emisor. Ni `app/configuracion.py` ni `.env.example` tienen claves de proveedor: Ollama es local y sin credenciales.

## LLM03 — Supply Chain

**Qué se miró:** `requirements.txt`, `app/configuracion.py`, `.env.example`, `docker-compose.yml`, `.claude/hooks/regla.sh`, `.claude/settings.json`

**Decisión:** `aceptado` — `requirements.txt` fija versiones con `==` pero sin hashes; `docker-compose.yml` usa `pgvector/pgvector:pg16` por etiqueta, no por digest; el modelo de embeddings es `nomic-embed-text:latest` (`app/configuracion.py`, `.env.example`), una etiqueta móvil cuya dimensión se da por hecha en `dimension_embedding = 768`. En el harness, `.claude/hooks/regla.sh` ejecuta en cada `Write`, `Edit` y `Bash` código que vive fuera de este repositorio (`../blog-api/.claude/hooks/regla-sin-resultados.mjs`). Se acepta por ser un proyecto de formación que corre en local. Se vuelve inaceptable si el servicio se despliega fuera de la máquina del desarrollador, o si `../blog-api` deja de estar bajo el control de la misma persona.

## LLM04 — Data and Model Poisoning

**Qué se miró:** `requirements.txt`, `app/configuracion.py`, `app/servicios/embeddings.py`, `app/servicios/generacion.py`

**Decisión:** `fuera de alcance` — El repositorio no entrena ni ajusta ningún modelo: usa `nomic-embed-text` y `qwen2.5:3b-instruct` preentrenados a través de Ollama (`app/configuracion.py`), y `requirements.txt` no incluye ninguna biblioteca de entrenamiento. El envenenamiento del índice RAG se trata en LLM08. Se reabre cuando el repositorio incluya un `Modelfile`, datos de ajuste fino o una dependencia de entrenamiento en `requirements.txt`.

## LLM05 — Improper Output Handling

**Qué se miró:** `app/servicios/generacion.py`, `app/main.py`, `app/esquemas.py`, `app/servicios/indice.py`

**Decisión:** `aceptado` — La salida de `_chat()` en `app/servicios/generacion.py` se devuelve tal cual, tras un `strip()`, en los campos `respuesta` (`RespuestaPreguntar`) y `resumen` (`RespuestaResumir`) de `app/esquemas.py`. blog-ai no la interpreta: no la mete en SQL (las consultas de `app/servicios/indice.py` van parametrizadas y nunca reciben salida del modelo), ni la ejecuta, ni la renderiza. Cómo la tratan blog-api y blog-web no se ha mirado en esta ejecución. Se vuelve inaceptable si blog-ai empieza a usar esa salida en SQL, en rutas de archivo, en comandos o en HTML que genere él mismo.

## LLM06 — Excessive Agency

**Qué se miró:** `app/servicios/generacion.py`, `.claude/settings.json`, `.claude/hooks/regla.sh`, `.claude/hooks/marcador.sh`, `CLAUDE.md`

**Decisión:** `aceptado` — En el producto, el modelo no tiene agencia: `_chat()` manda a `/api/chat` solo un mensaje `system` y uno `user`, sin `tools`. En el harness, `.claude/settings.json` no declara permisos (ni `allow` ni `deny`), así que lo que puede hacer el agente depende del modo de permisos de cada sesión. Los hooks son scripts deterministas: `.claude/hooks/regla.sh` lee y avisa, y `.claude/hooks/marcador.sh` añade líneas a `MARCADORES-blog-ai.txt`. No hay servidores MCP ni CI. Se acepta porque es un espacio de trabajo local de un solo desarrollador. Se vuelve inaceptable si aparece un `.mcp.json` con servidores que escriban fuera del repositorio, si `.github/workflows/` empieza a lanzar un agente, o si `.claude/settings.json` añade un `allow` amplio para `Bash`.

## LLM07 — System Prompt Leakage

**Qué se miró:** `app/servicios/generacion.py`

**Decisión:** `aceptado` — Los prompts de sistema (`INSTRUCCIONES`, `INSTRUCCIONES_RESUMEN` y `RECORDATORIO_RESUMEN` en `app/servicios/generacion.py`) solo contienen el tono, el formato y la frase de «no lo encuentro»; no llevan credenciales, URLs internas ni reglas de autorización. Están en el código fuente del repositorio, así que filtrarlos no revela nada que no se pueda leer ya. Se vuelve inaceptable si un prompt pasa a contener secretos o una regla de acceso que el código no haga cumplir por su cuenta.

## LLM08 — Vector and Embedding Weaknesses

**Qué se miró:** `app/main.py`, `app/servicios/indice.py`, `app/base_de_datos.py`, `db/init.sql`, `docker-compose.yml`, `README.md`

**Decisión:** `aceptado` — `POST /indexar` en `app/main.py` no tiene autenticación: quien llegue al puerto 8402 puede escribir en `fragmentos` cualquier post marcado como `publicado` o sustituir uno existente por su `id` (`indexar()` hace `_borrar_post` y después `INSERT` en `app/servicios/indice.py`), y ese contenido acaba en el contexto de `/preguntar`. Por otro lado, `docker-compose.yml` publica PostgreSQL como `'5433:5432'`, sin IP, con el usuario y la contraseña `corriente` en claro: cualquiera que alcance ese puerto puede editar los embeddings directamente. Lo que lo contiene hoy: `make up` lanza uvicorn sin `--host` (búsqueda en `Makefile`), y el `README.md` dice que blog-api es el único cliente. La tabla es de un solo inquilino y solo guarda contenido publicado, sin datos por usuario. Se vuelve inaceptable si la máquina entra en una red compartida mientras el contenedor esté levantado, o si uvicorn arranca con `--host 0.0.0.0`.

## LLM09 — Misinformation

**Qué se miró:** `app/servicios/generacion.py`, `app/main.py`, `app/esquemas.py`

**Decisión:** `aceptado` — `INSTRUCCIONES` en `app/servicios/generacion.py` pide responder solo con los extractos, citarlos como `[n]` y decir «No lo encuentro en los articulos del blog» si no está, con `temperature` a 0.2; `/preguntar` devuelve en `fuentes` los posts que se usaron (`app/main.py`), para que se pueda comprobar. Nada verifica que la respuesta se apoye en las fuentes, ni que el resumen de `/resumir` tenga dos frases o sea fiel al texto. Se acepta porque las respuestas siempre llevan sus fuentes y la herramienta es de consulta, no de decisión. Se vuelve inaceptable si un consumidor muestra `respuesta` o `resumen` sin `fuentes` ni aviso de que lo ha generado un modelo.

## LLM10 — Unbounded Consumption

**Qué se miró:** `app/main.py`, `app/esquemas.py`, `app/servicios/limite.py`, `app/servicios/generacion.py`, `app/servicios/embeddings.py`, `app/configuracion.py`

**Decisión:** `aceptado` — `/resumir` es el único con controles completos: `texto` de 20 a 20 000 caracteres (`PeticionResumir`), `num_ctx` 8192 y `num_predict` 200 (`app/servicios/generacion.py`), y 10 llamadas por minuto por IP (`LimitadorPorCliente` en `app/servicios/limite.py`, `resumir_llamadas_por_minuto` en `app/configuracion.py`). Ese límite cuenta en memoria y por IP, así que comparte el cupo entre todos los usuarios que llegan a través de blog-api. `/buscar` y `/preguntar` acotan `consulta` a 500 caracteres y `limite` a 20 o 10, pero no tienen límite de llamadas. `/indexar` no acota ni el número de posts de `PeticionIndexar` ni la longitud de `cuerpo`, y cada fragmento es una llamada de embedding con 120 s de timeout (`app/servicios/embeddings.py`). Se acepta porque Ollama es local, no hay coste por token y el servicio solo escucha en localhost. Se vuelve inaceptable si blog-ai se expone fuera de localhost, o si `ollama_url` apunta a un proveedor que cobre por uso.

## Fuera de alcance y cuándo se reabre

| Entrada | Motivo | Disparador para reabrir |
|---|---|---|
| LLM04 — Data and Model Poisoning | El repositorio no entrena ni ajusta modelos: usa modelos preentrenados de Ollama. | Que el repositorio incluya un `Modelfile`, datos de ajuste fino o una dependencia de entrenamiento en `requirements.txt`. |
