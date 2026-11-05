"""Servicio de historial: guarda los cálculos ya hechos.

Es una clase "pura" de Python: no importa tkinter ni sabe cómo se dibuja nada.
(Equivalente web: una tabla en la base de datos + su repositorio.)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..core import EvalContext, Step


@dataclass(frozen=True)
class HistoryEntry:
    source_text: str            # lo que se escribió (para poder recuperarlo)
    expression: str             # la expresión normalizada
    result: str                 # el resultado formateado
    steps: Tuple[Step, ...]     # pasos de la resolución
    mode: str                   # nombre del modo en que se calculó ("STANDARD"...)
    ctx: EvalContext            # base, ángulos y tamaño de palabra usados


class HistoryService:
    def __init__(self, max_items: int = 100) -> None:
        self._max_items = max_items
        self._entries: List[HistoryEntry] = []  # la más reciente primero

    def add(self, entry: HistoryEntry) -> None:
        self._entries.insert(0, entry)
        del self._entries[self._max_items:]

    def all(self) -> Tuple[HistoryEntry, ...]:
        return tuple(self._entries)

    def get(self, index: int) -> HistoryEntry:
        return self._entries[index]

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
