# Atajos de arranque de blog-ai. Los tres repositorios del modulo traen los mismos:
#
#   make check  - comprueba que la maquina esta lista (no toca nada)
#   make setup  - instala y prepara la base de datos (solo la primera vez)
#   make up     - arranca el servicio
#
# Si algo falla, el mensaje dice que falta. No hace falta leer este archivo.

SHELL := /bin/bash
CARPETA := blog-ai
REPO := blog-ai-ai4devs

# Se busca un interprete moderno con el numero puesto, porque 'python3' a secas
# apunta al Python del sistema en muchas maquinas y ese no sirve para este proyecto.
PY := $(shell command -v python3.13 2>/dev/null || command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3 2>/dev/null)
VENV := .venv/bin

MODELO_EMBEDDINGS := nomic-embed-text
MODELO_GENERACION := qwen2.5:3b-instruct
CONTENEDOR_DB := blog-ai-postgres

.PHONY: ayuda check setup up modelos db db-parar contrato regla

ayuda:
	@echo "make check     comprueba Python, Docker y Ollama"
	@echo "make setup     descarga los modelos, levanta la base de datos e instala las dependencias"
	@echo "make up        arranca el servicio en http://localhost:8402"
	@echo "make db        levanta solo la base de datos (puerto 5433)"
	@echo "make db-parar  para la base de datos"
	@echo "make contrato  regenera y verifica el contrato OpenAPI"
	@echo "make regla     comprueba la regla de comentarios de CLAUDE.md"

check:
	@if [ "$$(basename $$PWD)" != "$(CARPETA)" ]; then \
	  echo "ERROR: esta carpeta se llama '$$(basename $$PWD)' y tiene que llamarse '$(CARPETA)'."; \
	  echo "       Los tres repositorios viven como carpetas hermanas con el nombre corto,"; \
	  echo "       y todo lo demas (las rutas relativas entre ellos) lo da por hecho."; \
	  echo "       Vuelve a clonar poniendo la carpeta destino al final:"; \
	  echo "         git clone git@github.com:<tu-usuario>/$(REPO).git $(CARPETA)"; \
	  exit 1; \
	fi
	@if [ -z "$(PY)" ]; then \
	  echo "ERROR: no encuentro ningun interprete de Python."; \
	  echo "       Descargas por sistema en python.org/downloads. Hace falta 3.11 o superior."; \
	  exit 1; \
	fi
	@$(PY) -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || { \
	  echo "ERROR: '$(PY)' es $$($(PY) -V 2>&1) y este proyecto necesita Python 3.11 o superior."; \
	  echo "       Con una version mas antigua, la instalacion de dependencias falla con un"; \
	  echo "       error sobre un conector de base de datos que no menciona a Python."; \
	  echo "       Ojo: instalar un Python moderno NO cambia a que apunta 'python3'."; \
	  echo "       macOS:  brew install python@3.13"; \
	  echo "       Linux:  el gestor de paquetes de tu distribucion"; \
	  echo "       Otros:  python.org/downloads"; \
	  exit 1; }
	@docker info >/dev/null 2>&1 || { \
	  echo "ERROR: Docker no responde. Instalado no es lo mismo que corriendo."; \
	  echo "       Arranca Docker Desktop (o el servicio de Docker en Linux) y repite."; \
	  exit 1; }
	@curl -sf -m 5 http://localhost:11434/api/tags >/dev/null 2>&1 || { \
	  echo "ERROR: Ollama no responde en http://localhost:11434."; \
	  echo "       Arrancalo y repite. En macOS, abriendo la aplicacion Ollama."; \
	  echo "       En Windows con WSL: si instalaste Ollama en Windows, desde aqui no se ve."; \
	  echo "       Instalalo DENTRO de WSL con: curl -fsSL https://ollama.com/install.sh | sh"; \
	  exit 1; }
	@echo "OK  blog-ai: carpeta correcta, $$($(PY) -V 2>&1), Docker corriendo y Ollama respondiendo."

setup: check modelos db
	$(PY) -m venv .venv
	$(VENV)/python -m pip install --quiet --upgrade pip
	$(VENV)/python -m pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "OK  .env creado a partir de .env.example."; fi
	@echo ""
	@echo "OK  blog-ai listo. Arrancalo con 'make up' (http://localhost:8402)."

modelos:
	ollama pull $(MODELO_EMBEDDINGS)
	ollama pull $(MODELO_GENERACION)

db:
	docker compose up -d
	@echo "Esperando a que PostgreSQL acepte conexiones..."
	@for i in $$(seq 1 60); do \
	  if [ "$$(docker inspect -f '{{.State.Health.Status}}' $(CONTENEDOR_DB) 2>/dev/null)" = "healthy" ]; then \
	    echo "OK  PostgreSQL listo en el puerto 5433."; \
	    exit 0; \
	  fi; \
	  sleep 1; \
	done; \
	echo "ERROR: PostgreSQL no llego a estar listo en 60 segundos."; \
	echo "       Mira que dice con: docker compose logs postgres"; \
	exit 1

db-parar:
	docker compose down

# --reload recoge los cambios de app/ sin reiniciar a mano. Va acotado con
# --reload-dir: sin acotar, el vigilante mira 2300 ficheros y 2241 estan dentro
# de .venv, que no cambia nunca.
up:
	$(VENV)/python -m uvicorn app.main:app --port 8402 --reload --reload-dir app

contrato:
	$(VENV)/python scripts/generar_openapi.py --verificar

# La regla de proceso de CLAUDE.md: toda funcion nueva explica su caso vacio.
# El mismo comprobador que lanza el hook PostToolUse despues de cada edicion. Va con el
# Python del sistema, no con el del .venv: solo usa la biblioteca estandar y asi tambien
# corre antes de 'make setup'.
regla:
	@$(PY) .claude/hooks/regla_sin_resultados.py
