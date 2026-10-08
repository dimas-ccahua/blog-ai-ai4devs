"""Limite de llamadas por cliente, en memoria y con ventana deslizante.

Vive en el proceso: con un solo worker de uvicorn basta. Con varios, cada uno llevaria
su propia cuenta y el limite real se multiplicaria por el numero de workers.
"""

from __future__ import annotations

import time
from collections import deque


class LimitadorPorCliente:
    # Sin resultados: no aplica, no consulta nada.
    def __init__(self, llamadas: int, ventana_segundos: float) -> None:
        self.llamadas = llamadas
        self.ventana = ventana_segundos
        self._marcas: dict[str, deque[float]] = {}

    # Sin resultados: devuelve 0 si el cliente no tiene llamadas previas; si no, los
    # segundos que le quedan por esperar (0 tambien cuando todavia tiene cupo).
    def registrar(self, cliente: str) -> float:
        """Anota la llamada si cabe en la ventana y devuelve 0; si no cabe, no la anota."""
        ahora = time.monotonic()
        marcas = self._marcas.setdefault(cliente, deque())
        while marcas and ahora - marcas[0] >= self.ventana:
            marcas.popleft()
        if len(marcas) >= self.llamadas:
            return self.ventana - (ahora - marcas[0])
        marcas.append(ahora)
        return 0.0
