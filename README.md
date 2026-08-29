# blog-ai

Servicio de **búsqueda semántica y RAG** del blog «Corriente». Es un repositorio aparte, con su
propio stack y su propia base de datos: **no comparte tablas con `blog-api`**, recibe los posts
por HTTP.

Stack: **FastAPI + PostgreSQL con pgvector + Ollama** (modelos locales). Puerto **8402**.

> 📌 **El ejercicio del Módulo 7 y cómo se entrega están en el `README.md` de `blog-api`**, no
> aquí. Este repositorio lo vas a tocar mientras lo haces, pero la entrega es una sola y va por
> allí. Lee ese archivo antes de empezar.

## Dónde encaja

```
blog-web  :5402  ──HTTP──▶  blog-api  :3402  ──HTTP──▶  blog-ai  :8402
                                                         (este repo)
```

Los tres repositorios viven como **carpetas hermanas** llamadas exactamente `blog-api`,
`blog-web` y `blog-ai` dentro de una carpeta común. El repositorio se llama `blog-ai-ai4devs`
y la carpeta no, así que **el `git clone` lleva siempre la carpeta destino escrita al final**:

```bash
git clone git@github.com:<tu-usuario>/blog-ai-ai4devs.git blog-ai
```

## Cómo se levanta

Necesita Docker y Ollama corriendo, con los dos modelos ya descargados:

```bash
ollama pull nomic-embed-text        # embeddings (768 dimensiones)
ollama pull qwen2.5:3b-instruct     # generación

docker compose up -d                # PostgreSQL + pgvector en el puerto 5433
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m uvicorn app.main:app --port 8402
```

> ⚠️ **Cuidado con qué Python te da `python3 -m venv`, porque el error no lo dice.** En una
> máquina donde `python3` resuelve al Python del sistema (3.9), `pip install -r
> requirements.txt` **falla** con un error sobre `psycopg-binary` que no menciona la versión de
> Python en ningún sitio. El entorno que funciona se construyó con **Python 3.13**. Si montas
> el entorno de cero, crea el venv con un intérprete moderno explícito
> (`python3.13 -m venv .venv`).

Comprobación:

```bash
curl -s localhost:8402/salud | jq
```

> ⚠️ **`/salud` dice `estado: "ok"` aunque Ollama esté caído.** El campo que hay que mirar es
> **`ollama_alcanzable`**. Sin Ollama, `/indexar`, `/buscar` y `/preguntar` responden **503**
> con el motivo.

Para llenar el índice, la vía normal es pedírselo a `blog-api`, que es quien tiene los posts:

```bash
curl -s -X POST localhost:3402/indexar | jq
```

## Rutas

```
POST /indexar     {posts: [...]}          → indexados / omitidos / fragmentos
POST /buscar      {consulta, limite}      → resultados por similitud coseno, con su puntuación
POST /preguntar   {consulta, limite}      → respuesta generada citando sus fuentes
GET  /salud                               → modelos, alcanzabilidad de Ollama y recuentos
GET  /docs                                → interfaz interactiva de OpenAPI
```

## El contrato es un artefacto, no un acuerdo verbal

`contrato/openapi.json` es el documento OpenAPI de este servicio, **generado desde el código y
versionado en git**:

```bash
./.venv/bin/python scripts/generar_openapi.py             # regenera
./.venv/bin/python scripts/generar_openapi.py --verificar # falla si está desactualizado
```

La segunda forma es la que conviene atar a integración continua. `blog-api` guarda una **copia
fijada** de ese mismo documento y compara contra ella, así que el contrato público de este
servicio son los esquemas de `app/esquemas.py`, no lo que cada cliente haya escrito a mano.

## La regla del dominio que cruza el límite de servicio

**Aquí solo se indexan posts publicados.** Un borrador que llegue a `POST /indexar` se omite
con su motivo, y además se **retira** del índice por si estuvo publicado antes:

```bash
curl -s -X POST localhost:8402/indexar -H 'Content-Type: application/json' \
  -d '{"posts":[{"id":99,"slug":"un-borrador","titulo":"Un borrador","resumen":"...",
       "cuerpo":"...","estado":"borrador"}]}' | jq
# → {"indexados":0,"omitidos":1,"motivos_omision":[{"slug":"un-borrador",
#     "motivo":"El post esta en borrador: blog-ai solo indexa publicados"}]}
```

`blog-api` ya filtra los borradores antes de enviarlos. Esta comprobación es deliberadamente
**redundante**: cuando una regla de negocio cruza un límite de servicio, el servicio que recibe
no puede delegar su cumplimiento en el que emite.

## De qué depende de los otros dos

| Repositorio | Relación | Qué pasa si no está |
|---|---|---|
| **blog-api** (3402) | Es su **único cliente** y su fuente de contenido: sin `POST /indexar`, el índice está vacío. | `/buscar` responde con lista vacía; `/preguntar` responde «No lo encuentro en los artículos del blog». |
| **blog-web** (5402) | Ninguna. El navegador nunca habla con este servicio: siempre pasa por `blog-api`. | Nada. |

Dependencias de infraestructura: **PostgreSQL 5433** (`docker compose up -d`) y **Ollama
11434**.

## Cómo está organizado

```
app/main.py                   rutas finas de FastAPI
app/esquemas.py               Pydantic; ESTO es el contrato público
app/servicios/embeddings.py   Ollama (nomic-embed-text) con los prefijos de tarea
app/servicios/indice.py       troceado, indexado y búsqueda por coseno
app/servicios/generacion.py   RAG con qwen2.5:3b-instruct
app/base_de_datos.py          esquema de `fragmentos` (vector(768) + índice ivfflat)
contrato/openapi.json         el artefacto versionado
```

Un post no ocupa una fila, ocupa **una por sección**: se trocea el Markdown por encabezados
`##` y se embebe cada trozo. Buscar sobre secciones da resultados bastante más finos que
embeber el artículo entero en un solo vector.

`nomic-embed-text` espera prefijos de tarea (`search_document:` / `search_query:`). No es
cosmética: sin ellos, el ranking empeora de forma medible en consultas oblicuas.

## Hasta dónde llega (y hasta dónde no)

La recuperación es deliberadamente mínima: un vector por fragmento, coseno y el mejor fragmento
de cada post. Medida con nueve consultas de referencia en lenguaje natural, acierta **7 de 9 en
la primera posición y 8 de 9 en el top 3**. La que falla («trabajar de noche sin que la pantalla
me deslumbre», sin usar la palabra *oscuro*) es el límite real de un modelo de embeddings de
137M de parámetros: se apoya bastante en el léxico.

Lo mismo con la generación: `qwen2.5:3b-instruct` es un modelo pequeño. Cuando la recuperación
le da los fragmentos correctos, responde bien y cita; cuando le da fragmentos poco relacionados,
**los une igual** y produce una respuesta segura de sí misma y equivocada. No es un fallo de
configuración, es lo que hace un 3B: si esto fuera producción, el siguiente paso sería un umbral
mínimo de puntuación para no contestar, y un modelo mayor.

Otras dos simplificaciones deliberadas, por si alguien copia esto a un sitio serio: hay **una
sola conexión global** a PostgreSQL en vez de un pool, y las llamadas a la base de datos son
**síncronas dentro de rutas `async`**, así que bloquean el bucle de eventos. Con un lector a la
vez no se nota; con cien, sí. Y no hay autenticación: cualquiera que alcance el puerto 8402
puede reindexar.
