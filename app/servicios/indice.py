"""
Indexado y busqueda semantica.

Regla del dominio que cruza el limite de servicio: **solo se indexan posts publicados**.
Un borrador no se puede recuperar por busqueda semantica, y eso no se consigue confiando
en que blog-api filtre bien: se comprueba aqui otra vez.
"""

from __future__ import annotations

import re

from app.base_de_datos import a_literal_vector, conexion
from app.esquemas import MotivoOmision, PostEntrante, ResultadoBusqueda
from app.servicios.embeddings import PREFIJO_CONSULTA, embeber

# Un fragmento mas largo que esto se parte: nomic-embed-text trabaja con 2048 tokens.
LIMITE_DE_CARACTERES = 1200


def trocear(post: PostEntrante) -> list[str]:
    """
    Trocea el cuerpo Markdown por secciones de segundo nivel.

    El PRIMER fragmento lleva titulo + resumen, para que una consulta con las palabras
    del titulo encuentre el post aunque el cuerpo hable de otra cosa. Los demas van
    limpios: repetir el titulo en cada seccion acerca todos los fragmentos del corpus
    entre si y emborrona el ranking. Medido con nueve consultas de referencia,
    repitiendolo salian 7 aciertos en el top 3; sin repetirlo, 8.
    """
    cabecera = f"{post.titulo}. {post.resumen}"
    secciones = [
        seccion.strip() for seccion in re.split(r"\n(?=## )", post.cuerpo) if seccion.strip()
    ]

    fragmentos = [cabecera]
    for seccion in secciones:
        texto = seccion
        while len(texto) > LIMITE_DE_CARACTERES:
            fragmentos.append(texto[:LIMITE_DE_CARACTERES])
            texto = texto[LIMITE_DE_CARACTERES:]
        if texto.strip():
            fragmentos.append(texto.strip())
    return fragmentos


def _borrar_post(post_id: int) -> None:
    with conexion().cursor() as cursor:
        cursor.execute("DELETE FROM fragmentos WHERE post_id = %s", (post_id,))


async def indexar(posts: list[PostEntrante]) -> tuple[int, int, int, list[MotivoOmision]]:
    indexados = 0
    fragmentos_escritos = 0
    omisiones: list[MotivoOmision] = []

    for post in posts:
        if post.estado != "publicado":
            # Y ademas se retira del indice, por si estuvo publicado y se despublico.
            _borrar_post(post.id)
            omisiones.append(
                MotivoOmision(
                    slug=post.slug,
                    motivo="El post esta en borrador: blog-ai solo indexa publicados",
                )
            )
            continue

        trozos = trocear(post)
        vectores = await embeber(trozos)

        _borrar_post(post.id)
        with conexion().cursor() as cursor:
            for orden, (texto, vector) in enumerate(zip(trozos, vectores)):
                cursor.execute(
                    """
                    INSERT INTO fragmentos (post_id, slug, titulo, resumen, orden, texto, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                    """,
                    (post.id, post.slug, post.titulo, post.resumen, orden, texto,
                     a_literal_vector(vector)),
                )
                fragmentos_escritos += 1
        indexados += 1

    return indexados, len(omisiones), fragmentos_escritos, omisiones


async def buscar(consulta: str, limite: int) -> list[ResultadoBusqueda]:
    """
    Similitud coseno con el operador `<=>` de pgvector.

    `<=>` devuelve DISTANCIA coseno (0 = identico), asi que la puntuacion que se publica
    es `1 - distancia`. Se agrupa por post quedandose con su mejor fragmento.
    """
    vectores = await embeber([consulta], prefijo=PREFIJO_CONSULTA)
    literal = a_literal_vector(vectores[0])

    with conexion().cursor() as cursor:
        cursor.execute(
            """
            SELECT post_id, slug, titulo, resumen, texto, puntuacion
            FROM (
                SELECT DISTINCT ON (post_id)
                       post_id, slug, titulo, resumen, texto,
                       1 - (embedding <=> %(vector)s::vector) AS puntuacion
                FROM fragmentos
                ORDER BY post_id, embedding <=> %(vector)s::vector
            ) AS mejores
            ORDER BY puntuacion DESC
            LIMIT %(limite)s
            """,
            {"vector": literal, "limite": limite},
        )
        filas = cursor.fetchall()

    return [
        ResultadoBusqueda(
            post_id=fila["post_id"],
            slug=fila["slug"],
            titulo=fila["titulo"],
            resumen=fila["resumen"],
            puntuacion=round(float(fila["puntuacion"]), 4),
            fragmento=fila["texto"][:900],
        )
        for fila in filas
    ]


def recuentos() -> tuple[int, int]:
    with conexion().cursor() as cursor:
        cursor.execute("SELECT COUNT(DISTINCT post_id) AS posts, COUNT(*) AS fragmentos FROM fragmentos")
        fila = cursor.fetchone()
    return int(fila["posts"]), int(fila["fragmentos"])
