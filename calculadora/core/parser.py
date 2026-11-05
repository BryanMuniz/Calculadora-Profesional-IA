"""Paso 2 del pipeline: TOKENS → ÁRBOL (AST).

Es un *parser descendente recursivo*: hay una función por cada nivel de
prioridad. Cada función llama a la del nivel inmediatamente más fuerte,
y por eso las operaciones fuertes quedan más abajo en el árbol.

Prioridad (de la MÁS DÉBIL a la MÁS FUERTE):

    OR, NOR                      _or
    XOR                          _xor
    AND, NAND                    _and
    <<  >>                       _shift
    +  −                         _addsub
    ×  ÷  mod  (y la implícita)  _muldiv
    − unario, NOT                _unary
    ^  (potencia)                _power
    !  %  (posfijos)             _postfix
    número, (grupo), función     _primary
"""
from __future__ import annotations

from typing import Callable, Iterable, List

from .ast_nodes import Binary, Constant, Function, Group, Node, Number, Postfix, Unary
from .errors import SyntaxCalcError
from .operations import CONSTANTS, FUNCTIONS
from .tokenizer import END, IDENT, LPAREN, NUM, OP, RPAREN, Token


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ── API pública ──────────────────────────────────────────────
    def parse(self) -> Node:
        if self._peek().type == END:
            raise SyntaxCalcError("Escribe una operación")
        node = self._or()
        extra = self._peek()
        if extra.type == RPAREN:
            raise SyntaxCalcError("Hay un paréntesis ')' de más")
        if extra.type != END:
            raise SyntaxCalcError(f"No esperaba '{extra.text}' en este lugar")
        return node

    # ── utilidades ───────────────────────────────────────────────
    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _is_op(self, operators: Iterable[str]) -> bool:
        token = self._peek()
        return token.type == OP and token.text in operators

    def _level(self, operators: Iterable[str], next_level: Callable[[], Node]) -> Node:
        """Nivel genérico asociativo a la izquierda: a OP b OP c = (a OP b) OP c."""
        node = next_level()
        while self._is_op(operators):
            op = self._advance().text
            node = Binary(op, node, next_level())
        return node

    # ── niveles de prioridad ─────────────────────────────────────
    def _or(self) -> Node: return self._level(("OR", "NOR"), self._xor)
    def _xor(self) -> Node: return self._level(("XOR",), self._and)
    def _and(self) -> Node: return self._level(("AND", "NAND"), self._shift)
    def _shift(self) -> Node: return self._level(("<<", ">>"), self._addsub)
    def _addsub(self) -> Node: return self._level(("+", "-"), self._muldiv)

    def _muldiv(self) -> Node:
        node = self._unary()
        while True:
            token = self._peek()
            if self._is_op(("*", "/", "MOD")):
                op = self._advance().text
                node = Binary(op, node, self._unary())
            elif token.type in (NUM, IDENT, LPAREN):
                # Multiplicación implícita: 2π, 3(4+1), 2sin(30)
                node = Binary("*", node, self._unary())
            else:
                return node

    def _unary(self) -> Node:
        if self._is_op(("-", "+", "NOT")):
            op = self._advance().text
            operand = self._unary()
            return operand if op == "+" else Unary(op, operand)
        return self._power()

    def _power(self) -> Node:
        base = self._postfix()
        if self._is_op(("^",)):
            self._advance()
            # El exponente se lee con _unary: da asociatividad a la derecha (2^3^2 = 2^9)
            # y permite exponentes negativos (2^-1).
            return Binary("^", base, self._unary())
        return base

    def _postfix(self) -> Node:
        node = self._primary()
        while self._is_op(("!", "%")):
            node = Postfix(self._advance().text, node)
        return node

    def _primary(self) -> Node:
        token = self._advance()

        if token.type == NUM:
            return Number(token.value)

        if token.type == LPAREN:
            inner = self._or()
            if self._peek().type != RPAREN:
                raise SyntaxCalcError("Falta cerrar un paréntesis")
            self._advance()
            return Group(inner)

        if token.type == IDENT:
            if token.text in CONSTANTS:
                return Constant(token.text)
            if token.text in FUNCTIONS:
                if self._peek().type != LPAREN:
                    raise SyntaxCalcError(f"Escribe un paréntesis después de '{token.text}'")
                self._advance()
                arg = self._or()
                if self._peek().type != RPAREN:
                    raise SyntaxCalcError("Falta cerrar un paréntesis")
                self._advance()
                return Function(token.text, arg)
            raise SyntaxCalcError(f"Función o constante desconocida: '{token.text}'")

        if token.type == END:
            raise SyntaxCalcError("La expresión está incompleta")
        raise SyntaxCalcError(f"No esperaba '{token.text}' en este lugar")
