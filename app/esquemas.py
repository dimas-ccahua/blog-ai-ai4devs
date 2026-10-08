"""
Los esquemas de entrada y salida del servicio.

Estas clases NO son un detalle interno: son el contrato que blog-api consume.
FastAPI las publica en /openapi.json con estos mismos nombres, y ese documento
se versiona en `contrato/openapi.json`. Renombrar un campo de aqui es romper
el contrato, aunque el codigo siga compilando.
"""

from typing import Literal

from pydantic import BaseModel, Field


class PostEntrante(BaseModel):
    """Un post tal y como lo manda blog-api para indexarlo."""

    id: int
    slug: str
    titulo: str
    resumen: str
    cuerpo: str
    # blog-ai indexa SOLO los publicados. El estado viaja para poder rechazar
    # explicitamente un borrador, en vez de confiar en que el emisor ya filtro.
    estado: Literal["borrador", "publicado"]
    categoria: str | None = None
    etiquetas: list[str] = Field(default_factory=list)
    publicado_en: str | None = None


class PeticionIndexar(BaseModel):
    posts: list[PostEntrante]


class MotivoOmision(BaseModel):
    slug: str
    motivo: str


class RespuestaIndexar(BaseModel):
    indexados: int
    omitidos: int
    fragmentos: int
    motivos_omision: list[MotivoOmision]


class PeticionBuscar(BaseModel):
    consulta: str = Field(min_length=2, max_length=500)
    limite: int = Field(default=5, ge=1, le=20)


class ResultadoBusqueda(BaseModel):
    post_id: int
    slug: str
    titulo: str
    resumen: str
    # Similitud coseno en [0, 1]: 1 es identico.
    puntuacion: float
    fragmento: str


class RespuestaBuscar(BaseModel):
    consulta: str
    resultados: list[ResultadoBusqueda]


class PeticionPreguntar(BaseModel):
    consulta: str = Field(min_length=2, max_length=500)
    limite: int = Field(default=3, ge=1, le=10)


class Fuente(BaseModel):
    post_id: int
    slug: str
    titulo: str
    puntuacion: float


class RespuestaPreguntar(BaseModel):
    consulta: str
    respuesta: str
    fuentes: list[Fuente]
    modelo: str


class PeticionResumir(BaseModel):
    # El tope esta pensado para caber en CONTEXTO_RESUMEN (servicios/generacion.py):
    # 20 000 caracteres son unos 6 000 tokens. Si se sube uno, hay que subir el otro.
    texto: str = Field(min_length=20, max_length=20000)


class RespuestaResumir(BaseModel):
    resumen: str
    modelo: str


class RespuestaSalud(BaseModel):
    estado: str
    servicio: str
    modelo_embeddings: str
    modelo_generacion: str
    ollama_alcanzable: bool
    posts_indexados: int
    fragmentos_indexados: int
