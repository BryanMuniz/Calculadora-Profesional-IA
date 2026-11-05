"""Distribución de las teclas de cada modo (datos puros, sin tkinter).

Cada tecla es un `KeySpec(etiqueta, comando, argumento, estilo)`.
Al presionarla, la interfaz llama a `controller.dispatch(comando, argumento)`.
Para cambiar o agregar una tecla solo hay que editar estas listas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from ..controller import Mode


@dataclass(frozen=True)
class KeySpec:
    label: str
    command: str
    arg: str = ""
    kind: str = "operator"   # clave de theme.STYLES


Row = List[KeySpec]


def num(d: str) -> KeySpec: return KeySpec(d, "digit", d, "number")
def op(symbol: str) -> KeySpec: return KeySpec(symbol, "operator", symbol, "operator")
def fn(label: str, name: str) -> KeySpec: return KeySpec(label, "function", name, "function")
def cmd(label: str, command: str, arg: str = "", kind: str = "function") -> KeySpec:
    return KeySpec(label, command, arg, kind)


EQUALS = cmd("=", "equals", kind="equals")
DECIMAL = cmd(".", "decimal", kind="number")
NEGATE = cmd("±", "negate", kind="number")
BACKSPACE = cmd("⌫", "backspace", kind="operator")

MEMORY_ROW: Row = [
    cmd("MC", "mem_clear", kind="memory"), cmd("MR", "mem_recall", kind="memory"),
    cmd("M+", "mem_add", kind="memory"), cmd("M−", "mem_sub", kind="memory"),
    cmd("MS", "mem_store", kind="memory"),
]

STANDARD: List[Row] = [
    MEMORY_ROW,
    [cmd("%", "postfix", "%"), cmd("CE", "clear_entry", kind="operator"), cmd("C", "clear", kind="operator"), BACKSPACE],
    [cmd("1/x", "reciprocal"), cmd("x²", "postfix", "^2"), cmd("√x", "sqrt"), op("÷")],
    [num("7"), num("8"), num("9"), op("×")],
    [num("4"), num("5"), num("6"), op("−")],
    [num("1"), num("2"), num("3"), op("+")],
    [NEGATE, num("0"), DECIMAL, EQUALS],
]

SCIENTIFIC: List[Row] = [
    MEMORY_ROW,
    [cmd("π", "constant", "π"), cmd("e", "constant", "e"), cmd("C", "clear", kind="operator"),
     cmd("CE", "clear_entry", kind="operator"), BACKSPACE],
    [fn("sin", "sin"), fn("cos", "cos"), fn("tan", "tan"), cmd("x²", "postfix", "^2"), cmd("1/x", "reciprocal")],
    [fn("sin⁻¹", "asin"), fn("cos⁻¹", "acos"), fn("tan⁻¹", "atan"), cmd("√x", "sqrt"), cmd("∛x", "cbrt")],
    [fn("sinh", "sinh"), fn("cosh", "cosh"), fn("tanh", "tanh"), cmd("|x|", "abs"), cmd("n!", "postfix", "!")],
    [fn("log", "log"), fn("ln", "ln"), cmd("(", "open_paren", kind="operator"),
     cmd(")", "close_paren", kind="operator"), op("÷")],
    [op("^"), num("7"), num("8"), num("9"), op("×")],
    [cmd("10ˣ", "power10"), num("4"), num("5"), num("6"), op("−")],
    [fn("eˣ", "exp"), num("1"), num("2"), num("3"), op("+")],
    [op("mod"), NEGATE, num("0"), DECIMAL, EQUALS],
]

PROGRAMMER: List[Row] = [
    [op("AND"), op("OR"), op("XOR"), cmd("NOT", "prefix", "NOT", "operator"), op("NAND"), op("NOR")],
    [op("<<"), op(">>"), cmd("(", "open_paren", kind="operator"), cmd(")", "close_paren", kind="operator"),
     op("mod"), BACKSPACE],
    [num("A"), num("B"), num("7"), num("8"), num("9"), op("÷")],
    [num("C"), num("D"), num("4"), num("5"), num("6"), op("×")],
    [num("E"), num("F"), num("1"), num("2"), num("3"), op("−")],
    [cmd("AC", "clear", kind="operator"), cmd("CE", "clear_entry", kind="operator"), NEGATE, num("0"), EQUALS, op("+")],
]

LAYOUTS: Dict[Mode, List[Row]] = {
    Mode.STANDARD: STANDARD,
    Mode.SCIENTIFIC: SCIENTIFIC,
    Mode.PROGRAMMER: PROGRAMMER,
}


def disabled_digits(base: int) -> Set[str]:
    """Dígitos que no existen en `base` (ej. 8 y 9 en octal)."""
    return {d for d in "0123456789ABCDEF" if int(d, 16) >= base}
