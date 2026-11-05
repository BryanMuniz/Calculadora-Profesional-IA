"""Errores "esperados" de la calculadora.

Idea clave: cuando el usuario escribe algo inválido (por ejemplo `5 ÷ 0` o `(2+`)
NO es un bug del programa, es una situación normal. Por eso usamos excepciones
propias: la interfaz las atrapa y muestra `error.message` en pantalla.

(Equivalente web: un `400 Bad Request` con un mensaje legible, en lugar de un `500`).
"""
from __future__ import annotations


class CalcError(Exception):
    """Clase base de todos los errores de cálculo."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SyntaxCalcError(CalcError):
    """La expresión está mal escrita (falta un paréntesis, un operando, etc.)."""


class MathCalcError(CalcError):
    """La expresión está bien escrita pero no se puede calcular (÷ 0, √ de negativo...)."""
