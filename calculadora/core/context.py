"""Contexto de evaluación: las "opciones" con las que se calcula una expresión."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AngleMode(Enum):
    """Unidad de los ángulos para sin, cos, tan y sus inversas."""

    DEG = "DEG"    # grados (360 por vuelta)
    RAD = "RAD"    # radianes (2π por vuelta)
    GRAD = "GRAD"  # gradianes (400 por vuelta)


@dataclass(frozen=True)
class EvalContext:
    """Configuración inmutable que viaja junto a cada cálculo.

    - angle_mode:   unidad de ángulos.
    - base:         base numérica de entrada/salida (2, 8, 10 o 16).
    - word_bits:    tamaño de palabra del modo programador (8, 16, 32 o 64 bits).
    - integer_mode: True en modo programador (solo enteros, con desbordamiento
                    "circular" como en un procesador real).
    """

    angle_mode: AngleMode = AngleMode.DEG
    base: int = 10
    word_bits: int = 64
    integer_mode: bool = False
