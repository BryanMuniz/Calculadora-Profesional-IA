"""Catálogo de operaciones matemáticas.

Aquí vive TODA la matemática. El resto del programa solo pregunta
"¿qué hace el operador `+`?" y este módulo responde con una función.
Agregar una operación nueva = agregar una entrada a un diccionario.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Tuple, Union

from .context import AngleMode, EvalContext
from .errors import MathCalcError

Number = Union[int, float]

OVERFLOW = "Resultado fuera de rango (desbordamiento)"
DIV_ZERO = "No se puede dividir entre cero"
INVALID_INPUT = "Entrada no válida"
INTEGERS_ONLY = "Las operaciones bit a bit solo funcionan con números enteros"


# ─────────────────────────── utilidades ───────────────────────────
def _as_int(x: Number) -> int:
    if isinstance(x, int):
        return x
    if float(x).is_integer():
        return int(x)
    raise MathCalcError(INTEGERS_ONLY)


def _to_radians(x: Number, ctx: EvalContext) -> float:
    if ctx.angle_mode is AngleMode.DEG:
        return math.radians(x)
    if ctx.angle_mode is AngleMode.GRAD:
        return x * math.pi / 200
    return float(x)


def _from_radians(x: float, ctx: EvalContext) -> float:
    if ctx.angle_mode is AngleMode.DEG:
        return math.degrees(x)
    if ctx.angle_mode is AngleMode.GRAD:
        return x * 200 / math.pi
    return x


def _clean(x: float) -> Number:
    """sin(180°) da 1.2e-16 por errores de redondeo; lo tratamos como 0."""
    return 0 if abs(x) < 1e-12 else x


# ─────────────────────── operaciones binarias ─────────────────────
def add(a, b, ctx): return a + b
def subtract(a, b, ctx): return a - b
def multiply(a, b, ctx): return a * b


def divide(a, b, ctx):
    if b == 0:
        raise MathCalcError(DIV_ZERO if a != 0 else "Resultado indefinido (0 ÷ 0)")
    if ctx.integer_mode:  # división entera truncada hacia cero, como en un procesador
        a, b = _as_int(a), _as_int(b)
        quotient = abs(a) // abs(b)
        return -quotient if (a < 0) != (b < 0) else quotient
    if isinstance(a, int) and isinstance(b, int) and a % b == 0:
        return a // b
    return a / b


def power(a, b, ctx):
    if a == 0 and b == 0:
        raise MathCalcError("Resultado indefinido (0 elevado a 0)")
    if a == 0 and b < 0:
        raise MathCalcError(DIV_ZERO)
    # Con enteros pequeños damos el resultado exacto (2^10 = 1024, no 1024.0000000001)
    if isinstance(a, int) and isinstance(b, int) and b >= 0:
        if b * math.log2(abs(a) or 1) < 60:
            return a ** b
    try:
        return math.pow(a, b)
    except OverflowError:
        raise MathCalcError(OVERFLOW) from None
    except ValueError:
        raise MathCalcError("No existe: base negativa con exponente fraccionario") from None


def modulo(a, b, ctx):
    if b == 0:
        raise MathCalcError(DIV_ZERO)
    if isinstance(a, int) and isinstance(b, int):
        remainder = abs(a) % abs(b)      # el resto toma el signo del dividendo
        return remainder if a >= 0 else -remainder
    return math.fmod(a, b)


def bit_and(a, b, ctx): return _as_int(a) & _as_int(b)
def bit_or(a, b, ctx): return _as_int(a) | _as_int(b)
def bit_xor(a, b, ctx): return _as_int(a) ^ _as_int(b)
def bit_nand(a, b, ctx): return ~(_as_int(a) & _as_int(b))
def bit_nor(a, b, ctx): return ~(_as_int(a) | _as_int(b))


def _shift_amount(b) -> int:
    n = _as_int(b)
    if n < 0 or n > 4096:
        raise MathCalcError("Cantidad de bits a desplazar no válida")
    return n


def shift_left(a, b, ctx): return _as_int(a) << _shift_amount(b)
def shift_right(a, b, ctx): return _as_int(a) >> _shift_amount(b)


HINT_POW = "Las potencias se calculan antes que × ÷ + − (y de derecha a izquierda)."
HINT_MUL = "× ÷ y mod se resuelven antes que + y −, de izquierda a derecha."
HINT_ADD = "+ y − se resuelven al final, de izquierda a derecha."
HINT_SHIFT = "Los desplazamientos de bits se resuelven después de sumar y restar."
HINT_AND = "AND y NAND se resuelven antes que XOR; XOR antes que OR y NOR."


@dataclass(frozen=True)
class BinarySpec:
    symbol: str   # cómo se dibuja en pantalla
    title: str    # nombre en el panel de pasos
    func: Callable[[Number, Number, EvalContext], Number]
    hint: str


BINARY: Dict[str, BinarySpec] = {
    "+": BinarySpec("+", "Suma", add, HINT_ADD),
    "-": BinarySpec("−", "Resta", subtract, HINT_ADD),
    "*": BinarySpec("×", "Multiplicación", multiply, HINT_MUL),
    "/": BinarySpec("÷", "División", divide, HINT_MUL),
    "MOD": BinarySpec("mod", "Módulo (resto)", modulo, HINT_MUL),
    "^": BinarySpec("^", "Potencia", power, HINT_POW),
    "AND": BinarySpec("AND", "AND bit a bit", bit_and, HINT_AND),
    "NAND": BinarySpec("NAND", "NAND bit a bit", bit_nand, HINT_AND),
    "XOR": BinarySpec("XOR", "XOR bit a bit", bit_xor, "XOR se resuelve después de AND y antes de OR."),
    "OR": BinarySpec("OR", "OR bit a bit", bit_or, "OR y NOR son los últimos operadores en resolverse."),
    "NOR": BinarySpec("NOR", "NOR bit a bit", bit_nor, "OR y NOR son los últimos operadores en resolverse."),
    "<<": BinarySpec("<<", "Desplazamiento a la izquierda", shift_left, HINT_SHIFT),
    ">>": BinarySpec(">>", "Desplazamiento a la derecha", shift_right, HINT_SHIFT),
}


# ───────────────── operadores unarios y posfijos ──────────────────
def negate(x, ctx): return -x
def bit_not(x, ctx): return ~_as_int(x)


def factorial(x, ctx):
    n = _as_int(x) if float(x).is_integer() else None
    if n is None or n < 0:
        raise MathCalcError("El factorial solo existe para enteros no negativos")
    if n > 170:
        raise MathCalcError(OVERFLOW)
    result = math.factorial(n)
    return result if result < 10 ** 15 else float(result)


def percent(x, ctx): return divide(x, 100, ctx)


@dataclass(frozen=True)
class UnarySpec:
    symbol: str
    title: str
    func: Callable[[Number, EvalContext], Number]
    hint: str


UNARY: Dict[str, UnarySpec] = {
    "-": UnarySpec("−", "Negación", negate, "El signo menos delante cambia el signo del valor."),
    "NOT": UnarySpec("NOT ", "NOT bit a bit", bit_not, "NOT invierte todos los bits del número."),
}

POSTFIX: Dict[str, UnarySpec] = {
    "!": UnarySpec("!", "Factorial", factorial, "n! = n × (n−1) × … × 1"),
    "%": UnarySpec("%", "Porcentaje", percent, "x% equivale a x ÷ 100."),
}


# ───────────────────────── funciones ──────────────────────────────
def sqrt(x, ctx):
    if x < 0:
        raise MathCalcError("No existe la raíz cuadrada de un número negativo")
    if isinstance(x, int):
        root = math.isqrt(x)
        if root * root == x:
            return root
    return math.sqrt(x)


def cbrt(x, ctx):
    root = math.copysign(abs(x) ** (1 / 3), x)
    nearest = round(root)
    return nearest if nearest ** 3 == x else root


def sine(x, ctx): return _clean(math.sin(_to_radians(x, ctx)))
def cosine(x, ctx): return _clean(math.cos(_to_radians(x, ctx)))


def tangent(x, ctx):
    radians = _to_radians(x, ctx)
    if abs(math.cos(radians)) < 1e-12:
        raise MathCalcError("La tangente no está definida para este ángulo")
    return _clean(math.tan(radians))


def arcsine(x, ctx):
    if not -1 <= x <= 1:
        raise MathCalcError(INVALID_INPUT + " (debe estar entre -1 y 1)")
    return _clean(_from_radians(math.asin(x), ctx))


def arccosine(x, ctx):
    if not -1 <= x <= 1:
        raise MathCalcError(INVALID_INPUT + " (debe estar entre -1 y 1)")
    return _clean(_from_radians(math.acos(x), ctx))


def arctangent(x, ctx): return _clean(_from_radians(math.atan(x), ctx))
def hyp_sin(x, ctx): return math.sinh(x)
def hyp_cos(x, ctx): return math.cosh(x)
def hyp_tan(x, ctx): return math.tanh(x)
def hyp_asin(x, ctx): return math.asinh(x)


def hyp_acos(x, ctx):
    if x < 1:
        raise MathCalcError(INVALID_INPUT + " (debe ser ≥ 1)")
    return math.acosh(x)


def hyp_atan(x, ctx):
    if not -1 < x < 1:
        raise MathCalcError(INVALID_INPUT + " (debe estar entre -1 y 1, sin incluirlos)")
    return math.atanh(x)


def _positive_only(x):
    if x <= 0:
        raise MathCalcError("El logaritmo solo existe para números positivos")


def natural_log(x, ctx): _positive_only(x); return math.log(x)
def log10(x, ctx): _positive_only(x); return math.log10(x)
def log2(x, ctx): _positive_only(x); return math.log2(x)
def exponential(x, ctx): return math.exp(x)
def absolute(x, ctx): return abs(x)
def floor(x, ctx): return math.floor(x)
def ceil(x, ctx): return math.ceil(x)


@dataclass(frozen=True)
class FunctionSpec:
    label: str   # cómo se escribe en pantalla: "√", "sin"...
    title: str
    func: Callable[[Number, EvalContext], Number]


FUNCTIONS: Dict[str, FunctionSpec] = {
    "sqrt": FunctionSpec("√", "Raíz cuadrada", sqrt),
    "cbrt": FunctionSpec("∛", "Raíz cúbica", cbrt),
    "abs": FunctionSpec("abs", "Valor absoluto", absolute),
    "sin": FunctionSpec("sin", "Seno", sine),
    "cos": FunctionSpec("cos", "Coseno", cosine),
    "tan": FunctionSpec("tan", "Tangente", tangent),
    "asin": FunctionSpec("asin", "Arcoseno", arcsine),
    "acos": FunctionSpec("acos", "Arcocoseno", arccosine),
    "atan": FunctionSpec("atan", "Arcotangente", arctangent),
    "sinh": FunctionSpec("sinh", "Seno hiperbólico", hyp_sin),
    "cosh": FunctionSpec("cosh", "Coseno hiperbólico", hyp_cos),
    "tanh": FunctionSpec("tanh", "Tangente hiperbólica", hyp_tan),
    "asinh": FunctionSpec("asinh", "Arcoseno hiperbólico", hyp_asin),
    "acosh": FunctionSpec("acosh", "Arcocoseno hiperbólico", hyp_acos),
    "atanh": FunctionSpec("atanh", "Arcotangente hiperbólica", hyp_atan),
    "ln": FunctionSpec("ln", "Logaritmo natural", natural_log),
    "log": FunctionSpec("log", "Logaritmo base 10", log10),
    "log2": FunctionSpec("log2", "Logaritmo base 2", log2),
    "exp": FunctionSpec("exp", "Exponencial (eˣ)", exponential),
    "floor": FunctionSpec("floor", "Redondeo hacia abajo", floor),
    "ceil": FunctionSpec("ceil", "Redondeo hacia arriba", ceil),
}

FUNCTION_HINT = "Las funciones se resuelven de dentro hacia fuera: primero su argumento."

# Constantes: nombre → (símbolo en pantalla, valor)
CONSTANTS: Dict[str, Tuple[str, float]] = {
    "pi": ("π", math.pi),
    "e": ("e", math.e),
}
