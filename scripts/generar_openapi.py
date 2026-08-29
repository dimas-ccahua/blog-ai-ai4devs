#!/usr/bin/env python3
"""
Genera (o verifica) `contrato/openapi.json`, el contrato publico de blog-ai.

    python scripts/generar_openapi.py             # regenera el archivo
    python scripts/generar_openapi.py --verificar # falla si el archivo no esta al dia

La segunda forma es la que conviene atar a la integracion continua: si alguien cambia
un esquema y no regenera el contrato, el commit no pasa. Sin eso, el artefacto
versionado se convierte en documentacion vieja, que es peor que no tenerla.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

DESTINO = pathlib.Path(__file__).resolve().parents[1] / "contrato" / "openapi.json"


def documento() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    generado = documento()

    if "--verificar" in sys.argv:
        if not DESTINO.exists():
            print(f"✗ Falta {DESTINO.relative_to(DESTINO.parents[1])}")
            return 1
        if DESTINO.read_text(encoding="utf-8") != generado:
            print("✗ El contrato versionado NO coincide con el codigo.")
            print("  Ejecuta: python scripts/generar_openapi.py")
            return 1
        print("✓ El contrato versionado esta al dia.")
        return 0

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generado, encoding="utf-8")
    print(f"✓ Escrito {DESTINO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
