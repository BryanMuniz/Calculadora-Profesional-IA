"""Convierte números en texto (y a distintas bases numéricas)."""
from __future__ import annotations

import math
from typing import Dict, Union

from .context import EvalContext

Number = Union[int, float]

_DIGITS = "0123456789ABCDEF"
_MAX_PLAIN_INT = 10 ** 15  # a partir de aquí usamos notación científica


def wrap_signed(value: int, bits: int) -> int:
    """Ajusta `value` a un entero con signo de `bits` bits (complemento a dos).

    Ejemplo con 8 bits: 127 + 1 = 128 → se "da la vuelta" y queda -128.
    """
    value &= (1 << bits) - 1
    if value >> (bits - 1):
        value -= 1 << bits
    return value


def to_base(value: int, base: int, bits: int) -> str:
    """Escribe un entero en base 2, 8, 10 o 16 (los negativos, en complemento a dos)."""
    if base == 10:
        return str(value)
    value &= (1 << bits) - 1
    if value == 0:
        return "0"
    digits = []
    while value:
        value, remainder = divmod(value, base)
        digits.append(_DIGITS[remainder])
    return "".join(reversed(digits))


def group_digits(text: str, size: int = 4) -> str:
    """Agrupa dígitos de derecha a izquierda: '11111111' → '1111 1111'."""
    chunks = []
    while text:
        chunks.append(text[-size:])
        text = text[:-size]
    return " ".join(reversed(chunks))


def format_decimal(value: Number) -> str:
    """Formato decimal "bonito": sin ceros sobrantes y con 15 cifras significativas.

    Con 15 cifras desaparece el ruido típico de los decimales binarios:
    0.1 + 0.2 = 0.30000000000000004 → se muestra "0.3".
    """
    if isinstance(value, int):
        if abs(value) < _MAX_PLAIN_INT:
            return str(value)
        value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "∞" if value > 0 else "-∞"
    if value == 0:
        return "0"
    if value.is_integer() and abs(value) < _MAX_PLAIN_INT:
        return str(int(value))
    return f"{value:.15g}"


class NumberFormatter:
    """Formatea números según el contexto activo (decimal o base del modo programador)."""

    def __init__(self, ctx: EvalContext) -> None:
        self._ctx = ctx

    def format(self, value: Number) -> str:
        if self._ctx.integer_mode:
            return to_base(int(value), self._ctx.base, self._ctx.word_bits)
        return format_decimal(value)

    def operand(self, value: Number) -> str:
        """Igual que `format`, pero los negativos van entre paréntesis: (-5)."""
        text = self.format(value)
        return f"({text})" if text.startswith("-") else text


def all_bases(value: int, bits: int) -> Dict[str, str]:
    """Representaciones del mismo valor en HEX, DEC, OCT y BIN (para el modo programador)."""
    return {
        "HEX": group_digits(to_base(value, 16, bits)),
        "DEC": str(value),
        "OCT": group_digits(to_base(value, 8, bits), 3),
        "BIN": group_digits(to_base(value, 2, bits)),
    }
