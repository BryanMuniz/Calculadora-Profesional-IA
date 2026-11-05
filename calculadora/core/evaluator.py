"""Paso 3 del pipeline: ÁRBOL → VALOR (+ lista de pasos).

En vez de calcular "de golpe", el evaluador resuelve UNA operación a la vez,
igual que lo haríamos con lápiz y papel. En cada vuelta del bucle:

  1. Busca las operaciones "listas" (aquellas cuyos operandos ya son números).
  2. Elige la de mayor prioridad:
        a) la que está más adentro de paréntesis,
        b) a igualdad, la de operador más fuerte (^ antes que × antes que +),
        c) a igualdad, la más a la izquierda.
  3. La calcula y guarda un `Step` con la operación y cómo queda la expresión.

Esa lista de `Step` alimenta el panel "Paso a paso" de la interfaz.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Union

from .ast_nodes import Binary, Constant, Function, Group, Node, Number, Postfix, Unary
from .context import EvalContext
from .errors import MathCalcError
from .formatting import NumberFormatter, wrap_signed
from .operations import (
    BINARY, CONSTANTS, DIV_ZERO, FUNCTION_HINT, FUNCTIONS, OVERFLOW, POSTFIX, UNARY,
    _as_int, divide, multiply,
)
from .render import render
from .steps import Step

Value = Union[int, float]
_MISSING = object()  # "este nodo todavía no tiene valor"

# Fuerza de cada operador al elegir qué resolver primero (mayor = antes).
_RANK = {
    "^": 8, "*": 6, "/": 6, "MOD": 6, "+": 5, "-": 5,
    "<<": 4, ">>": 4, "AND": 3, "NAND": 3, "XOR": 2, "OR": 1, "NOR": 1,
}
_PAREN_HINT = "Está dentro de paréntesis, así que se resuelve primero. "


class Evaluator:
    def __init__(self, root: Node, ctx: EvalContext) -> None:
        self.root = root
        self.ctx = ctx
        self.fmt = NumberFormatter(ctx)
        self.steps: List[Step] = []
        self._reduced: Dict[int, Value] = {}   # {id(nodo): valor ya calculado}
        self._order: List[Node] = []           # nodos en post-orden (hijos antes que padres)
        self._depth: Dict[int, int] = {}       # profundidad de paréntesis de cada nodo
        self._parent: Dict[int, Optional[Node]] = {}

    # ── API pública ──────────────────────────────────────────────
    def run(self) -> Value:
        self._index(self.root, depth=0, parent=None)
        self._collapse_groups()
        while self._value_of(self.root) is _MISSING:
            self._execute(self._pick_next())
            self._collapse_groups()
        return self._normalize(self._value_of(self.root))

    # ── preparación ──────────────────────────────────────────────
    def _index(self, node: Node, depth: int, parent: Optional[Node]) -> None:
        """Recorre el árbol anotando profundidad y padre de cada nodo."""
        self._depth[id(node)] = depth
        self._parent[id(node)] = parent
        if isinstance(node, Group):
            self._index(node.inner, depth + 1, node)
        elif isinstance(node, Function):
            self._index(node.arg, depth + 1, node)
        elif isinstance(node, (Unary, Postfix)):
            self._index(node.operand, depth, node)
        elif isinstance(node, Binary):
            self._index(node.left, depth, node)
            self._index(node.right, depth, node)
        self._order.append(node)

    def _value_of(self, node: Node):
        if id(node) in self._reduced:
            return self._reduced[id(node)]
        if isinstance(node, Number):
            return node.value
        if self._is_negative_literal(node):
            return -node.operand.value
        return _MISSING

    @staticmethod
    def _is_negative_literal(node: Node) -> bool:
        return isinstance(node, Unary) and node.op == "-" and isinstance(node.operand, Number)

    def _collapse_groups(self) -> None:
        """Un paréntesis cuyo contenido ya es un número deja de mostrarse."""
        for node in self._order:  # post-orden: los grupos internos se resuelven antes
            if isinstance(node, Group) and id(node) not in self._reduced:
                value = self._value_of(node.inner)
                if value is not _MISSING:
                    self._reduced[id(node)] = value

    # ── elegir la siguiente operación ────────────────────────────
    def _needs_step(self, node: Node) -> bool:
        if id(node) in self._reduced:
            return False
        if isinstance(node, (Number, Group)) or self._is_negative_literal(node):
            return False
        return True

    def _is_percent_of(self, node: Node) -> bool:
        parent = self._parent[id(node)]
        return (isinstance(node, Postfix) and node.op == "%" and isinstance(parent, Binary)
                and parent.op in ("+", "-") and parent.right is node)

    def _is_ready(self, node: Node) -> bool:
        if isinstance(node, Constant):
            return True
        if isinstance(node, (Unary, Postfix)):
            if self._value_of(node.operand) is _MISSING:
                return False
            if self._is_percent_of(node):  # necesita conocer el número de la izquierda
                return self._value_of(self._parent[id(node)].left) is not _MISSING
            return True
        if isinstance(node, Binary):
            return self._value_of(node.left) is not _MISSING and self._value_of(node.right) is not _MISSING
        if isinstance(node, Function):
            return self._value_of(node.arg) is not _MISSING
        return False

    @staticmethod
    def _rank(node: Node) -> int:
        if isinstance(node, Constant):
            return 10
        if isinstance(node, (Function, Postfix)):
            return 9
        if isinstance(node, Unary):
            return 7
        return _RANK[node.op]

    def _pick_next(self) -> Node:
        candidates = [
            (-self._depth[id(n)], -self._rank(n), index, n)
            for index, n in enumerate(self._order)
            if self._needs_step(n) and self._is_ready(n)
        ]
        if not candidates:  # no debería ocurrir con un árbol válido
            raise MathCalcError("No se pudo resolver la expresión")
        return min(candidates, key=lambda c: c[:3])[3]

    # ── ejecutar una operación ───────────────────────────────────
    def _execute(self, node: Node) -> None:
        if isinstance(node, Constant):
            self._do_constant(node)
        elif isinstance(node, Unary):
            self._do_unary(node)
        elif isinstance(node, Postfix):
            self._do_postfix(node)
        elif isinstance(node, Binary):
            self._do_binary(node)
        elif isinstance(node, Function):
            self._do_function(node)

    def _hint(self, node: Node, hint: str) -> str:
        return (_PAREN_HINT if self._depth[id(node)] > 0 else "") + hint

    def _record(self, node: Node, value: Value, title: str, operation: str, hint: str = "") -> None:
        self._reduced[id(node)] = value
        self.steps.append(Step(len(self.steps) + 1, title, operation,
                               render(self.root, self._reduced, self.fmt), self._hint(node, hint)))

    def _apply(self, operation: Callable[[], Value]) -> Value:
        """Ejecuta la operación traduciendo errores de Python a mensajes claros."""
        try:
            return operation()
        except ZeroDivisionError:
            raise MathCalcError(DIV_ZERO) from None
        except OverflowError:
            raise MathCalcError(OVERFLOW) from None
        except ValueError:
            raise MathCalcError("Operación no válida") from None

    def _normalize(self, value: Value) -> Value:
        """Valida el resultado y, en modo programador, lo ajusta al tamaño de palabra."""
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise MathCalcError(OVERFLOW)
        if self.ctx.integer_mode:
            value = wrap_signed(_as_int(value), self.ctx.word_bits)
        elif isinstance(value, int) and value.bit_length() > 1000:
            raise MathCalcError(OVERFLOW)
        return value

    def _do_constant(self, node: Constant) -> None:
        symbol, value = CONSTANTS[node.name]
        self._record(node, value, "Constante", f"{symbol} = {self.fmt.format(value)}",
                     "Se sustituye la constante por su valor.")

    def _do_unary(self, node: Unary) -> None:
        spec = UNARY[node.op]
        operand = self._value_of(node.operand)
        result = self._normalize(self._apply(lambda: spec.func(operand, self.ctx)))
        text = f"{spec.symbol.strip()}({self.fmt.format(operand)}) = {self.fmt.format(result)}"
        self._record(node, result, spec.title, text, spec.hint)

    def _do_postfix(self, node: Postfix) -> None:
        operand = self._value_of(node.operand)
        if self._is_percent_of(node):
            # Regla de la calculadora de Windows: en `a + b%`, b% significa "b% de a".
            base = self._value_of(self._parent[id(node)].left)
            amount = self._apply(lambda: divide(multiply(base, operand, self.ctx), 100, self.ctx))
            text = (f"{self.fmt.format(operand)}% de {self.fmt.format(base)}"
                    f" = {self.fmt.format(amount)}")
            self._record(node, amount, "Porcentaje", text,
                         "En una suma o resta, a + b% significa a + (b% de a).")
            return
        spec = POSTFIX[node.op]
        result = self._normalize(self._apply(lambda: spec.func(operand, self.ctx)))
        text = f"{self.fmt.operand(operand)}{spec.symbol} = {self.fmt.format(result)}"
        self._record(node, result, spec.title, text, spec.hint)

    def _do_binary(self, node: Binary) -> None:
        spec = BINARY[node.op]
        left, right = self._value_of(node.left), self._value_of(node.right)
        result = self._normalize(self._apply(lambda: spec.func(left, right, self.ctx)))
        text = (f"{self.fmt.operand(left)} {spec.symbol} {self.fmt.operand(right)}"
                f" = {self.fmt.format(result)}")
        self._record(node, result, spec.title, text, spec.hint)

    def _do_function(self, node: Function) -> None:
        spec = FUNCTIONS[node.name]
        argument = self._value_of(node.arg)
        result = self._normalize(self._apply(lambda: spec.func(argument, self.ctx)))
        text = f"{spec.label}({self.fmt.format(argument)}) = {self.fmt.format(result)}"
        self._record(node, result, spec.title, text, FUNCTION_HINT)
