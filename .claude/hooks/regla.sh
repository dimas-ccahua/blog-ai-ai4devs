#!/bin/sh
# Lanza el comprobador de la regla de CLAUDE.md en este repositorio y en su hermano, si
# esta al lado. Es lo que llama el hook PostToolUse de .claude/settings.json.
#
# La vuelta por el hermano no es un capricho: blog-api y blog-ai se editan desde una sola
# sesion de Claude Code abierta en uno de los dos, y el hook solo conoce la carpeta de la
# sesion. Sin esto, la regla se cumpliria en el repositorio abierto y en el otro no.
# Si el hermano no esta clonado al lado, no pasa nada: no hay carpeta y no se mira.

RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
ESTADO=0
VISTOS=""

for CARPETA in "$RAIZ" "$RAIZ/../blog-api" "$RAIZ/../blog-ai"; do
  [ -d "$CARPETA" ] || continue
  CARPETA=$(cd "$CARPETA" && pwd)
  case " $VISTOS " in *" $CARPETA "*) continue ;; esac
  VISTOS="$VISTOS $CARPETA"

  EN_TS="$CARPETA/.claude/hooks/regla-sin-resultados.mjs"
  EN_PY="$CARPETA/.claude/hooks/regla_sin_resultados.py"

  if [ -f "$EN_TS" ] && command -v node >/dev/null 2>&1; then
    node "$EN_TS" || ESTADO=2
  fi
  if [ -f "$EN_PY" ] && command -v python3 >/dev/null 2>&1; then
    python3 "$EN_PY" || ESTADO=2
  fi
done

exit $ESTADO
