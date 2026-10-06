#!/bin/sh
# Hook PostToolUse (Write|Edit) de blog-ai. Añade una línea a MARCADORES-blog-ai.txt, en la
# raíz de blog-ai, con la fecha, la herramienta y la ruta del archivo escrito.
#
# Todo va con rutas absolutas: el hook salta también cuando la sesión escribe fuera de este
# árbol (en ../blog-api, por ejemplo), y ahí ni el directorio actual ni la ruta del archivo
# sirven para encontrar la raíz de blog-ai.

MARCADORES=/home/rpa-latam/Escritorio/personnel/projects/lidr/blog/blog-ai/MARCADORES-blog-ai.txt

command -v jq >/dev/null 2>&1 || exit 0

ENTRADA=$(cat)
HERRAMIENTA=$(printf '%s' "$ENTRADA" | jq -r '.tool_name // "?"')
RUTA=$(printf '%s' "$ENTRADA" | jq -r '.tool_input.file_path // "?"')

printf '%s\t%s\t%s\n' "$(date -Iseconds)" "$HERRAMIENTA" "$RUTA" >>"$MARCADORES"

exit 0
