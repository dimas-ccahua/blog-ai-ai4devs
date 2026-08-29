"""
blog-ai — el servicio de busqueda semantica y RAG del blog «Corriente».

Es un repositorio aparte con su propio stack (Python + FastAPI + PostgreSQL/pgvector)
y su propia base de datos. No comparte tablas con blog-api: recibe posts por HTTP.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.base_de_datos import preparar_esquema
from app.configuracion import configuracion
from app.esquemas import (
    Fuente,
    PeticionBuscar,
    PeticionIndexar,
    PeticionPreguntar,
    RespuestaBuscar,
    RespuestaIndexar,
    RespuestaPreguntar,
    RespuestaSalud,
)
from app.servicios import indice
from app.servicios.embeddings import ErrorDeOllama, ollama_alcanzable
from app.servicios.generacion import responder


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    preparar_esquema()
    yield


app = FastAPI(
    title="blog-ai",
    description=(
        "Busqueda semantica y RAG para el blog «Corriente». Lo consume blog-api; "
        "el navegador nunca habla directamente con este servicio."
    ),
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


@app.get("/salud", response_model=RespuestaSalud, summary="Estado del servicio")
async def salud() -> RespuestaSalud:
    posts, fragmentos = indice.recuentos()
    return RespuestaSalud(
        estado="ok",
        servicio="blog-ai",
        modelo_embeddings=configuracion.modelo_embeddings,
        modelo_generacion=configuracion.modelo_generacion,
        ollama_alcanzable=await ollama_alcanzable(),
        posts_indexados=posts,
        fragmentos_indexados=fragmentos,
    )


@app.post("/indexar", response_model=RespuestaIndexar, summary="Indexa posts publicados")
async def indexar(peticion: PeticionIndexar) -> RespuestaIndexar:
    """Los posts en borrador se omiten y se retiran del indice si ya estaban."""
    try:
        indexados, omitidos, fragmentos, motivos = await indice.indexar(peticion.posts)
    except ErrorDeOllama as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return RespuestaIndexar(
        indexados=indexados,
        omitidos=omitidos,
        fragmentos=fragmentos,
        motivos_omision=motivos,
    )


@app.post("/buscar", response_model=RespuestaBuscar, summary="Busqueda semantica")
async def buscar(peticion: PeticionBuscar) -> RespuestaBuscar:
    try:
        resultados = await indice.buscar(peticion.consulta, peticion.limite)
    except ErrorDeOllama as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return RespuestaBuscar(consulta=peticion.consulta, resultados=resultados)


@app.post("/preguntar", response_model=RespuestaPreguntar, summary="Pregunta al blog (RAG)")
async def preguntar(peticion: PeticionPreguntar) -> RespuestaPreguntar:
    try:
        resultados = await indice.buscar(peticion.consulta, peticion.limite)
        texto = await responder(peticion.consulta, resultados)
    except ErrorDeOllama as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return RespuestaPreguntar(
        consulta=peticion.consulta,
        respuesta=texto,
        fuentes=[
            Fuente(
                post_id=resultado.post_id,
                slug=resultado.slug,
                titulo=resultado.titulo,
                puntuacion=resultado.puntuacion,
            )
            for resultado in resultados
        ],
        modelo=configuracion.modelo_generacion,
    )
