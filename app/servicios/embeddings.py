"""Embeddings via Ollama. El modelo corre en la maquina, no en un servicio de pago."""

from __future__ import annotations

import httpx

from app.configuracion import configuracion


class ErrorDeOllama(RuntimeError):
    pass


# nomic-embed-text espera que le digas para que es el texto. Sin estos prefijos, el
# modelo mezcla el espacio de las preguntas con el de los documentos y el ranking empeora
# de forma medible: la comprobamos con «como hago que mi web se lea mejor de noche», que
# sin prefijo no encontraba el articulo sobre modo oscuro y con prefijo lo pone el primero.
PREFIJO_DOCUMENTO = "search_document: "
PREFIJO_CONSULTA = "search_query: "


async def embeber(textos: list[str], prefijo: str = PREFIJO_DOCUMENTO) -> list[list[float]]:
    """Devuelve un vector por texto, en el mismo orden."""
    if not textos:
        return []

    textos = [f"{prefijo}{texto}" for texto in textos]

    async with httpx.AsyncClient(timeout=120.0) as cliente:
        try:
            respuesta = await cliente.post(
                f"{configuracion.ollama_url}/api/embed",
                json={"model": configuracion.modelo_embeddings, "input": textos},
            )
        except httpx.HTTPError as error:  # Ollama apagado, puerto cambiado...
            raise ErrorDeOllama(f"No se pudo hablar con Ollama: {error}") from error

    if respuesta.status_code != 200:
        raise ErrorDeOllama(f"Ollama respondio {respuesta.status_code}: {respuesta.text[:200]}")

    vectores = respuesta.json().get("embeddings")
    if not vectores or len(vectores) != len(textos):
        raise ErrorDeOllama("Ollama devolvio un numero de vectores distinto al de textos")
    return vectores


async def ollama_alcanzable() -> bool:
    async with httpx.AsyncClient(timeout=3.0) as cliente:
        try:
            respuesta = await cliente.get(f"{configuracion.ollama_url}/api/tags")
            return respuesta.status_code == 200
        except httpx.HTTPError:
            return False
