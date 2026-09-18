#!/usr/bin/env python3
"""Comprueba la regla de proceso de blog-ai: toda funcion nueva lleva justo encima un
comentario que dice que devuelve cuando no encuentra resultados. La regla en prosa, con
ejemplos, esta en CLAUDE.md; esto es solo el que la hace cumplir.

Lo lanza el hook PostToolUse de .claude/settings.json despues de cada edicion, y tambien
'make regla' a mano o en CI.

Solo mira las lineas que no estan en HEAD. Si mirase el archivo entero, cada edicion de
un servicio ya existente escupiria la lista de todas las funciones que el repositorio
traia de serie, que no es lo que se pide y hace que se ignore el aviso.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MARCA = re.compile(r"sin resultados\s*:", re.IGNORECASE)
DECLARACION = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(")
DECORADOR = re.compile(r"^\s*@\w")


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def archivos(salida: str) -> list[str]:
    # .claude/ queda fuera: ahi vive esta misma herramienta, que no es codigo del servicio.
    return [linea for linea in salida.split("\n") if linea and not linea.startswith(".claude/")]


def lineas_nuevas(archivo: str) -> set[int]:
    nuevas: set[int] = set()
    for linea in git("diff", "-U0", "HEAD", "--", archivo).split("\n"):
        cabecera = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", linea)
        if not cabecera:
            continue
        inicio = int(cabecera.group(1))
        cuantas = 1 if cabecera.group(2) is None else int(cabecera.group(2))
        nuevas.update(range(inicio, inicio + cuantas))
    return nuevas


def tiene_comentario(texto: list[str], indice: int) -> bool:
    """El comentario tiene que estar pegado a la funcion: una linea en blanco entre
    los dos lo separa de ella y deja de valer. Un docstring tampoco vale, esta debajo."""
    i = indice - 1
    while i >= 0 and DECORADOR.match(texto[i]):
        i -= 1

    while i >= 0:
        linea = texto[i].strip()
        if not linea.startswith("#"):
            return False
        if MARCA.search(linea):
            return True
        i -= 1
    return False


def revisar(archivo: str, todo_es_nuevo: bool) -> list[str]:
    try:
        texto = (RAIZ / archivo).read_text(encoding="utf-8").split("\n")
    except OSError:
        return []

    nuevas = None if todo_es_nuevo else lineas_nuevas(archivo)
    fallos = []

    for indice, linea in enumerate(texto):
        if nuevas is not None and indice + 1 not in nuevas:
            continue
        declaracion = DECLARACION.match(linea)
        if declaracion and not tiene_comentario(texto, indice):
            fallos.append(f"  {archivo}:{indice + 1}  {declaracion.group(1)}")

    return fallos


def main() -> int:
    modificados = archivos(git("diff", "--name-only", "--diff-filter=ACM", "HEAD", "--", "*.py"))
    sin_seguir = archivos(git("ls-files", "--others", "--exclude-standard", "--", "*.py"))

    fallos = [f for archivo in modificados for f in revisar(archivo, False)]
    fallos += [f for archivo in sin_seguir for f in revisar(archivo, True)]

    if not fallos:
        return 0

    print(
        "Regla de blog-ai sin cumplir: toda funcion nueva lleva justo encima un comentario\n"
        'que empieza por "Sin resultados:" y dice que devuelve cuando no encuentra nada.\n\n'
        + "\n".join(fallos)
        + "\n\nEscribelo en la linea de encima de cada una, sin linea en blanco en medio, y\n"
        "no en el docstring: el docstring va debajo del def, no encima.\n"
        'Si la funcion no busca nada, el comentario lo dice: "# Sin resultados: no aplica, no consulta nada."\n'
        "La regla entera esta en CLAUDE.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
