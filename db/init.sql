-- Se ejecuta una sola vez, al crear el volumen de datos.
-- La tabla de fragmentos la crea la aplicacion al arrancar (ver app/base_de_datos.py),
-- porque la dimension del vector depende del modelo de embeddings configurado.
CREATE EXTENSION IF NOT EXISTS vector;
