"""El "estado" que la interfaz necesita para dibujarse.

Es una foto inmutable: la UI NO guarda estado propio, solo la dibuja.
(Equivalente web: el `state` de React / un store de Redux.)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

from ..core import AngleMode, Step
from ..services import HistoryEntry


class Mode(Enum):
    STANDARD = "Estándar"
    SCIENTIFIC = "Científica"
    PROGRAMMER = "Programador"


@dataclass(frozen=True)
class CalculatorState:
    mode: Mode
    primary: str                    # texto grande de la pantalla
    secondary: str                  # línea pequeña de arriba (vista previa o "expresión =")
    is_error: bool
    expression: str                 # lo que hay escrito en el búfer
    steps: Tuple[Step, ...]         # pasos de la expresión actual
    steps_expression: str           # expresión normalizada para el panel de pasos
    steps_result: str               # resultado para el panel de pasos
    history: Tuple[HistoryEntry, ...]
    memory_text: str                # "" si la memoria está vacía
    angle_mode: AngleMode
    base: int                       # 2, 8, 10 o 16
    word_bits: int                  # 8, 16, 32 o 64
    base_views: Dict[str, str]      # {"HEX": "FF", "DEC": "255", ...} (modo programador)
