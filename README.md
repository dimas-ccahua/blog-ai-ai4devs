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
y la carpeta no, así que **el `git clone` lleva siempre la carpeta destino escrita al final**.

Forkéalo y clónalo **desde tu fork**: sobre un clon directo del repositorio del curso no
tienes permiso de escritura, y el ejercicio se entrega por pull request. Es **el primero de los tres**, porque los otros dos dependen de él.

> 🚨 **En el formulario del fork, DESMARCA la casilla que dice copiar solo la rama por
> defecto.** Viene marcada, y si la dejas así tu fork se lleva únicamente `main`. Da igual
> cómo la dejaras: las dos líneas de `upstream` traen la rama de partida del repositorio del
> curso, así que funcionan en los dos casos.

```bash
git clone git@github.com:<tu-usuario>/blog-ai-ai4devs.git blog-ai
cd blog-ai
git remote add upstream git@github.com:LIDR-academy/blog-ai-ai4devs.git
git fetch upstream
git checkout -b s7/start upstream/s7/start
```

## Qué hardware hace falta

Este repositorio es el único de los tres que ejecuta modelos de lenguaje en tu máquina, así
que es el que marca el requisito. Todo lo de esta tabla está **medido**, no estimado.

| | Mínimo | Cómodo |
|---|---|---|
| Memoria (RAM) | 8 GB, cerrando lo que no necesites | 16 GB o más |
| Disco libre | 8 GB | 12 GB |
| Tarjeta gráfica | ninguna: sin ella va más despacio, no deja de ir | la que traiga el equipo |

**En qué se va la memoria**, con los tres proyectos levantados: los dos modelos son **2,8 GB**
(2,4 el de generación y 0,37 el de embeddings), Docker con PostgreSQL ronda **0,8 GB**, y los
tres servicios juntos no llegan a **0,2 GB**. Total, unos **3,8 GB**. El cuello no suelen ser
los modelos: es lo que ya tienes abierto al lado.

**Disco:** 2,1 GB de modelos, 640 MB de imagen de PostgreSQL y ~330 MB de dependencias entre
los tres repositorios.

**Latencias medidas** (MacBook Air M2, con el modelo ya cargado): un embedding tarda entre
**0,02 y 0,05 s**, así que indexar los 43 fragmentos del blog es cuestión de un par de
segundos; una respuesta generada tarda **entre 2 y 3 s**. La **primera** petición tras arrancar
se va a unos **20 s** porque el modelo se está cargando: no está roto, y medir con ella es
medir la carga.

### Modo ligero, si vas justo de memoria

`MODELO_GENERACION` elige quién redacta las respuestas. Con el modelo pequeño los dos bajan de
2,8 GB a **1,8 GB**:

```bash
ollama pull qwen2.5:1.5b-instruct
```

y en tu `.env`:

```
MODELO_GENERACION=qwen2.5:1.5b-instruct
```

Medido: responde **más del doble de rápido** (~1 s frente a ~2,2 s) y redacta igual de bien,
pero **cita peor las fuentes** — tiende a soltar la respuesta sin el `[n]` del extracto del que
salió. Para el ejercicio del módulo da igual; si vas a mirar la calidad de las respuestas, no.

> ⚠️ **Lo que NO hay que cambiar es el modelo de embeddings.** `nomic-embed-text` ya es de los
> más pequeños que dan 768 dimensiones, y es solo el 13% de la huella. Cambiarlo **invalida el
> índice entero** aunque las dimensiones coincidan, porque son espacios vectoriales distintos:
> habría que reindexar, y hasta entonces la búsqueda devuelve resultados sin sentido **sin dar
> ningún error**.

### 🪟 Windows con WSL

**WSL le asigna a Linux la mitad de la memoria del equipo por defecto.** Con 8 GB eso son ~4, y
el ejercicio va a ir mal. Compruébalo con `free -h` desde tu terminal de Ubuntu. Para
ampliarlo, crea `C:\Users\<tu-usuario>\.wslconfig` con:

```ini
[wsl2]
memory=12GB
```

y después `wsl --shutdown` desde PowerShell.

Si instalas Ollama en Windows en vez de dentro de WSL, **el proyecto no lo encuentra**: desde
WSL, `localhost` es la propia Linux. Añade `networkingMode=mirrored` a ese mismo bloque
`[wsl2]` (necesita Windows 11 22H2 o posterior) y `localhost` ya cruza.

## Cómo se levanta

Necesita **Docker corriendo** y **Ollama arrancado**. Lo demás lo hace el atajo:

```bash
make setup    # solo la primera vez: modelos, base de datos y dependencias
make up       # arranca el servicio en http://localhost:8402
```

`make setup` tarda un rato la primera vez, porque descarga los dos modelos de Ollama (unos
2,2 GB entre ambos). Es lo único lento de todo el montaje, y solo pasa una vez.

Antes de tocar nada, comprueba cuatro cosas y **falla diciendo cuál**: que la carpeta se
llama `blog-ai`, que hay un Python 3.11 o superior, que Docker responde y que Ollama contesta.
Ese orden importa, porque los cuatro fallan con errores que no se parecen a su causa.

> ⚠️ **Sobre todo el de Python, que es el que más caro sale.** En muchas máquinas `python3`
> apunta al Python del sistema, que es demasiado antiguo, y entonces la instalación de
> dependencias **falla con un error sobre `psycopg-binary` que no menciona a Python por
> ningún lado**. Y lo contraintuitivo: **instalar un Python moderno no cambia a qué apunta
> `python3`**. Por eso `make setup` no usa `python3`: busca `python3.13`, `python3.12` y
> `python3.11` por su número, y si no encuentra ninguno te dice qué versión tienes y dónde
> conseguir una buena.

<details>
<summary>Qué hace <code>make setup</code> por dentro, si prefieres ir a mano</summary>

```bash
ollama pull nomic-embed-text        # embeddings (768 dimensiones)
ollama pull qwen2.5:3b-instruct     # generación

docker compose up -d                # PostgreSQL + pgvector en el puerto 5433
python3.13 -m venv .venv            # con el número puesto, no 'python3' a secas
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Entre `docker compose up -d` y lo siguiente hay que **esperar** a que PostgreSQL acepte
conexiones. El atajo espera al `healthcheck` que declara `docker-compose.yml`; a mano, si vas
demasiado rápido, la primera conexión falla y el error habla de la red, no del arranque.
</details>

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
