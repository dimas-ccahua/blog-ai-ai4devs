"""Generacion aumentada con recuperacion (RAG) usando qwen2.5:3b-instruct en Ollama."""

from __future__ import annotations

import httpx

from app.configuracion import configuracion
from app.esquemas import ResultadoBusqueda
from app.servicios.embeddings import ErrorDeOllama

INSTRUCCIONES = (
    "Eres el asistente del blog «Corriente». Responde SIEMPRE en español, en dos o tres "
    "frases, usando unicamente los extractos que te doy. Cita las fuentes por su numero "
    "entre corchetes, asi: [1]. Si los extractos no contienen la respuesta, di exactamente: "
    "«No lo encuentro en los articulos del blog»."
)


def _montar_contexto(resultados: list[ResultadoBusqueda]) -> str:
    bloques = []
    for numero, resultado in enumerate(resultados, start=1):
        bloques.append(f"[{numero}] {resultado.titulo}\n{resultado.fragmento}")
    return "\n\n".join(bloques)


async def responder(consulta: str, resultados: list[ResultadoBusqueda]) -> str:
    if not resultados:
        return "No lo encuentro en los articulos del blog"

    mensaje = (
        f"Extractos del blog:\n\n{_montar_contexto(resultados)}\n\n"
        f"Pregunta del lector: {consulta}"
    )

    async with httpx.AsyncClient(timeout=180.0) as cliente:
        try:
            respuesta = await cliente.post(
                f"{configuracion.ollama_url}/api/chat",
                json={
                    "model": configuracion.modelo_generacion,
                    "messages": [
                        {"role": "system", "content": INSTRUCCIONES},
                        {"role": "user", "content": mensaje},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 320},
                },
            )
        except httpx.HTTPError as error:
            raise ErrorDeOllama(f"No se pudo generar la respuesta: {error}") from error

    if respuesta.status_code != 200:
        raise ErrorDeOllama(f"Ollama respondio {respuesta.status_code}: {respuesta.text[:200]}")

    return respuesta.json()["message"]["content"].strip()
