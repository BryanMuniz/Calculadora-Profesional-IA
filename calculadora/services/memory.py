"""Servicio de memoria: los botones MC, MR, M+, M− y MS."""
from __future__ import annotations

from typing import Optional, Union

Number = Union[int, float]


class MemoryService:
    def __init__(self) -> None:
        self._value: Optional[Number] = None

    @property
    def has_value(self) -> bool:
        return self._value is not None

    @property
    def value(self) -> Optional[Number]:
        return self._value

    def store(self, value: Number) -> None:        # MS
        self._value = value

    def add(self, value: Number) -> None:          # M+
        self._value = (self._value or 0) + value

    def subtract(self, value: Number) -> None:     # M−
        self._value = (self._value or 0) - value

    def clear(self) -> None:                       # MC
        self._value = None
