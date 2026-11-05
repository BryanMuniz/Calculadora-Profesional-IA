"""Un "paso" de la resolución (lo que se muestra en el panel Paso a paso)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    index: int        # número de paso (1, 2, 3...)
    title: str        # nombre de la operación: "Multiplicación"
    operation: str    # la cuenta concreta: "3 × 4 = 12"
    expression: str   # cómo queda la expresión completa tras este paso: "2 + 12"
    hint: str = ""    # explicación corta de POR QUÉ se resuelve en este momento
