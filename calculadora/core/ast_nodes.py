"""Nodos del árbol de sintaxis abstracta (AST).

El AST representa la *estructura* de una expresión. Por ejemplo, `2 + 3 × 4` es:

            Binary(+)
            /       \\
      Number(2)   Binary(×)
                   /      \\
             Number(3)  Number(4)

Cuanto más profundo está un nodo, antes se calcula: así se respeta la prioridad
de operadores sin tener que "recordar" reglas mientras se evalúa.

`eq=False` hace que cada nodo se compare por identidad (id), lo que nos permite
usarlos como claves en diccionarios (ver `evaluator.py`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(eq=False)
class Number:
    value: Union[int, float]


@dataclass(eq=False)
class Constant:
    name: str  # "pi" o "e"


@dataclass(eq=False)
class Unary:
    op: str            # "-" o "NOT"
    operand: "Node"


@dataclass(eq=False)
class Postfix:
    op: str            # "!" o "%"
    operand: "Node"


@dataclass(eq=False)
class Binary:
    op: str            # "+", "-", "*", "/", "^", "MOD", "AND", ...
    left: "Node"
    right: "Node"


@dataclass(eq=False)
class Function:
    name: str          # "sin", "sqrt", "ln"...
    arg: "Node"


@dataclass(eq=False)
class Group:
    inner: "Node"      # una expresión entre paréntesis


Node = Union[Number, Constant, Unary, Postfix, Binary, Function, Group]
