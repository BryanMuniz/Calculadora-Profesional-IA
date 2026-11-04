"""El búfer de la expresión: el texto que el usuario va construyendo.

Aquí están las reglas de "edición" (sin matemáticas y sin ventanas):
reemplazar un operador por otro, borrar un token completo, envolver el
último número con √( ), alternar su signo, etc.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

_OPERATOR = r"(?:[+−×÷^]|mod|AND|OR|XOR|NAND|NOR|<<|>>)"
# Operador binario con espacios alrededor (" + ") o prefijo NOT ("NOT ") al final del texto.
_TRAILING_OPERATOR = re.compile(rf"(?:\s{_OPERATOR}\s|NOT\s)$", re.IGNORECASE)
# Nombre de función abierto al final: "sin(", "asin(", "√(".
_TRAILING_FUNCTION = re.compile(r"(?:[A-Za-z]{2,}|√|∛)\($")
# Último operando "simple": número (con decimales/exponente), π o dígitos hex.
_TAIL_NUMBER = re.compile(r"(?:\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+|π|[0-9A-Fa-f]+)$")
_FUNCTION_NAME_BEFORE_PAREN = re.compile(r"(?:[A-Za-z]+|√|∛)$")


class ExpressionBuffer:
    def __init__(self) -> None:
        self._text = ""

    # ── lectura ──────────────────────────────────────────────────
    @property
    def text(self) -> str:
        return self._text

    @property
    def is_empty(self) -> bool:
        return self._text == ""

    def ends_with_operator(self) -> bool:
        return _TRAILING_OPERATOR.search(self._text) is not None

    # ── escritura básica ─────────────────────────────────────────
    def set(self, text: str) -> None:
        self._text = text

    def clear(self) -> None:
        self._text = ""

    def append(self, text: str) -> None:
        self._text += text

    # ── reglas de edición ────────────────────────────────────────
    def add_digit(self, digit: str) -> None:
        self._text += digit

    def add_decimal_point(self) -> None:
        tail = re.search(r"[0-9.]*$", self._text).group()
        if "." in tail:
            return  # el número actual ya tiene punto decimal
        self._text += "." if tail else "0."

    def add_operator(self, symbol: str) -> None:
        """Agrega " + ". Si ya había un operador al final, lo reemplaza (como Windows)."""
        while self.ends_with_operator():
            self._text = _TRAILING_OPERATOR.sub("", self._text)
        self._text += f" {symbol} "

    def add_open_paren(self) -> None:
        self._text += "("

    def add_close_paren(self) -> None:
        opened = self._text.count("(") - self._text.count(")")
        if opened > 0 and not self.ends_with_operator() and not self._text.endswith("("):
            self._text += ")"

    def add_function(self, name: str) -> None:
        self._text += f"{name}("

    def backspace(self) -> None:
        """Borra un "token" completo: un operador, el nombre de una función o un carácter."""
        for pattern in (_TRAILING_OPERATOR, _TRAILING_FUNCTION):
            if pattern.search(self._text):
                self._text = pattern.sub("", self._text)
                return
        self._text = self._text[:-1]

    def clear_entry(self) -> None:
        """CE: borra el último operando; si no hay, borra todo."""
        span = self.last_operand_span()
        if span:
            self._text = self._text[:span[0]] + self._text[span[1]:]
        else:
            self._text = ""

    # ── trabajar con el último operando ──────────────────────────
    def last_operand_span(self) -> Optional[Tuple[int, int]]:
        """Posición (inicio, fin) del último operando: un número, π o un grupo "(…)" / "f(…)".

        Si el operando ya lleva un exponente pegado ("5^2", puesto por el botón x²),
        el operando incluye también la base, para que ± o √ afecten a "5^2" completo.
        """
        if self.ends_with_operator():
            return None
        return self._operand_span(self._text)

    @classmethod
    def _operand_span(cls, text: str) -> Optional[Tuple[int, int]]:
        if not text:
            return None
        end = len(text)
        span: Optional[Tuple[int, int]] = None
        if text.endswith(")"):
            depth = 0
            for i in range(end - 1, -1, -1):
                if text[i] == ")":
                    depth += 1
                elif text[i] == "(":
                    depth -= 1
                    if depth == 0:
                        name = _FUNCTION_NAME_BEFORE_PAREN.search(text[:i])
                        span = (name.start() if name else i, end)
                        break
        else:
            match = _TAIL_NUMBER.search(text)
            span = (match.start(), match.end()) if match else None
        if span is None:
            return None
        start = span[0]
        # Exponente pegado (sin espacios): el operando incluye también su base.
        if start > 0 and text[start - 1] == "^":
            base = cls._operand_span(text[:start - 1])
            if base:
                return (base[0], end)
        return span

    def wrap_last_operand(self, prefix: str, suffix: str) -> bool:
        """5 → √(5); (2+3) → abs((2+3))... Devuelve False si no hay operando."""
        span = self.last_operand_span()
        if not span:
            return False
        start, end = span
        self._text = self._text[:start] + prefix + self._text[start:end] + suffix + self._text[end:]
        return True

    def reciprocal_last_operand(self) -> bool:
        """x → (1 ÷ (x)). Los paréntesis externos protegen la prioridad: 2^3 → 2^(1 ÷ (3))."""
        span = self.last_operand_span()
        if not span:
            return False
        start, end = span
        operand = self._text[start:end]
        body = operand if operand.startswith("(") and self._is_single_group(operand) else f"({operand})"
        self._text = self._text[:start] + f"(1 ÷ {body})" + self._text[end:]
        return True

    def add_power_suffix(self, suffix: str) -> bool:
        """Botones x² y x³. Encadenados, protegen lo anterior: 5^2 → (5^2)^3."""
        span = self.last_operand_span()
        if not span:
            return False
        start, end = span
        operand = self._text[start:end]
        if re.search(r"\^\d$", operand):
            self._text = self._text[:start] + f"({operand})" + suffix + self._text[end:]
        else:
            self._text = self._text[:end] + suffix + self._text[end:]
        return True

    def negate_last_operand(self) -> bool:
        """Alterna el signo del último operando: 5 → (−5) → 5."""
        span = self.last_operand_span()
        if not span:
            return False
        start, end = span
        operand = self._text[start:end]
        if operand.startswith("(−") and operand.endswith(")") and self._is_single_group(operand):
            replacement = operand[2:-1]
        else:
            replacement = f"(−{operand})"
        self._text = self._text[:start] + replacement + self._text[end:]
        return True

    @staticmethod
    def _is_single_group(text: str) -> bool:
        """¿El primer '(' se cierra justo en el último carácter?"""
        depth = 0
        for i, ch in enumerate(text):
            depth += (ch == "(") - (ch == ")")
            if depth == 0:
                return i == len(text) - 1
        return False

    # ── preparar para calcular ───────────────────────────────────
    def for_evaluation(self) -> str:
        """Texto listo para calcular: sin operador colgando y con los paréntesis cerrados."""
        text = self._text
        while _TRAILING_OPERATOR.search(text):
            text = _TRAILING_OPERATOR.sub("", text)
        text = text.strip()
        if not text:
            return ""
        return text + ")" * max(0, text.count("(") - text.count(")"))
