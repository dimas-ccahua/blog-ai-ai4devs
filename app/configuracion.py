"""Configuracion de blog-ai, leida del entorno (o del fichero .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    puerto: int = 8402
    base_de_datos_url: str = "postgresql://corriente:corriente@localhost:5433/corriente_ia"

    ollama_url: str = "http://localhost:11434"
    modelo_embeddings: str = "nomic-embed-text:latest"
    modelo_generacion: str = "qwen2.5:3b-instruct"
    # nomic-embed-text devuelve vectores de 768 dimensiones.
    dimension_embedding: int = 768


configuracion = Configuracion()
