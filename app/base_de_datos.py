"""Acceso a PostgreSQL + pgvector. Una sola conexion perezosa, que sobra para un ejemplo."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from app.configuracion import configuracion

_conexion: psycopg.Connection | None = None


def conexion() -> psycopg.Connection:
    global _conexion
    if _conexion is None or _conexion.closed:
        _conexion = psycopg.connect(configuracion.base_de_datos_url, row_factory=dict_row)
        _conexion.autocommit = True
    return _conexion


def preparar_esquema() -> None:
    """
    Crea la extension y la tabla de fragmentos. Se ejecuta al arrancar la aplicacion.

    Un post no ocupa una fila: ocupa una por seccion (fragmento). Buscar sobre secciones
    da resultados mucho mas finos que embeber un articulo entero en un solo vector.
    """
    with conexion().cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS fragmentos (
                id           BIGSERIAL PRIMARY KEY,
                post_id      INTEGER NOT NULL,
                slug         TEXT    NOT NULL,
                titulo       TEXT    NOT NULL,
                resumen      TEXT    NOT NULL,
                orden        INTEGER NOT NULL,
                texto        TEXT    NOT NULL,
                embedding    VECTOR({configuracion.dimension_embedding}) NOT NULL,
                indexado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS fragmentos_post_id_idx ON fragmentos (post_id)")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS fragmentos_embedding_idx
            ON fragmentos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
            """
        )


def a_literal_vector(vector: list[float]) -> str:
    """pgvector acepta el vector como texto '[1,2,3]' y lo castea con ::vector."""
    return "[" + ",".join(f"{valor:.6f}" for valor in vector) + "]"
