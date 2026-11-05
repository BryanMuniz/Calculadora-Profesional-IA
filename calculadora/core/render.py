"""Convierte un AST (o un AST a medio resolver) otra vez en texto legible."""
from __future__ import annotations

from typing import Dict, Union

from .ast_nodes import Binary, Constant, Function, Group, Node, Number, Postfix, Unary
from .formatting import NumberFormatter
from .operations import BINARY, CONSTANTS, FUNCTIONS, UNARY

Reduced = Dict[int, Union[int, float]]


def render(root: Node, reduced: Reduced, fmt: NumberFormatter) -> str:
    """Dibuja `root` sustituyendo los nodos ya resueltos (`reduced`) por su valor.

    `reduced` es un diccionario {id(nodo): valor}. Así, tras resolver 3 × 4,
    la expresión `2 + 3 × 4` se dibuja como `2 + 12`.
    """

    def go(node: Node) -> str:
        if id(node) in reduced:
            value = reduced[id(node)]
            return fmt.format(value) if node is root else fmt.operand(value)
        if isinstance(node, Number):
            return fmt.operand(node.value)
        if isinstance(node, Constant):
            return CONSTANTS[node.name][0]
        if isinstance(node, Unary):
            return UNARY[node.op].symbol + go(node.operand)
        if isinstance(node, Postfix):
            return go(node.operand) + node.op
        if isinstance(node, Binary):
            return f"{go(node.left)} {BINARY[node.op].symbol} {go(node.right)}"
        if isinstance(node, Function):
            return f"{FUNCTIONS[node.name].label}({go(node.arg)})"
        if isinstance(node, Group):
            return f"({go(node.inner)})"
        raise TypeError(f"Nodo desconocido: {node!r}")

    return go(root)
