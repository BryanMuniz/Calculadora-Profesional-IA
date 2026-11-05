"""Paso 1 del pipeline: TEXTO → TOKENS.

Un *token* es la pieza más pequeña con significado. Ejemplo:

    "2 + sin(30)"  →  [NUM 2] [OP +] [IDENT sin] [LPAREN] [NUM 30] [RPAREN] [END]

El tokenizador solo "lee"; no sabe de prioridades ni de matemáticas.
(Es lo mismo que hace un lexer al procesar JavaScript o JSON.)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Union

from .context import EvalContext
from .errors import SyntaxCalcError

# Tipos de token
NUM, IDENT, OP, LPAREN, RPAREN, END = "NUM", "IDENT", "OP", "LPAREN", "RPAREN", "END"


@dataclass(frozen=True)
class Token:
    type: str
    text: str
    value: Optional[Union[int, float]] = None
    position: int = 0


# Operadores escritos con letras (se aceptan en mayúsculas o minúsculas).
KEYWORD_OPERATORS = {"MOD", "AND", "OR", "XOR", "NAND", "NOR", "NOT"}

# Símbolos de un carácter → nombre "canónico" del operador.
SINGLE_CHAR_OPERATORS = {
    "+": "+",
    "-": "-", "−": "-", "–": "-",
    "*": "*", "×": "*", "·": "*",
    "/": "/", "÷": "/",
    "^": "^", "!": "!", "%": "%",
}

# Símbolos especiales que equivalen a un nombre.
WORD_ALIASES = {"√": "sqrt", "∛": "cbrt", "π": "pi"}

_DECIMAL_NUMBER = re.compile(r"\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?")
_LETTERS = re.compile(r"[A-Za-z]+")
_ALNUM = re.compile(r"[0-9A-Za-z]+")


def tokenize(text: str, ctx: EvalContext) -> List[Token]:
    tokens: List[Token] = []
    i, n = 0, len(text)
    # En modo programador (o en base ≠ 10) un "número" puede llevar letras (A-F).
    digit_words = ctx.integer_mode or ctx.base != 10

    while i < n:
        ch = text[i]

        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            tokens.append(Token(LPAREN, ch, position=i)); i += 1; continue
        if ch == ")":
            tokens.append(Token(RPAREN, ch, position=i)); i += 1; continue
        if text[i:i + 2] in ("<<", ">>"):
            tokens.append(Token(OP, text[i:i + 2], position=i)); i += 2; continue
        if ch in SINGLE_CHAR_OPERATORS:
            tokens.append(Token(OP, SINGLE_CHAR_OPERATORS[ch], position=i)); i += 1; continue
        if ch in WORD_ALIASES:
            tokens.append(Token(IDENT, WORD_ALIASES[ch], position=i)); i += 1; continue

        if digit_words and ch == ".":
            raise SyntaxCalcError("El modo programador solo admite números enteros")

        # Número decimal: 12, 3.14, .5, 1e5
        if not digit_words and (ch.isdigit() or ch == "."):
            match = _DECIMAL_NUMBER.match(text, i)
            if not match:
                raise SyntaxCalcError("Número mal escrito")
            raw = match.group()
            is_float = any(c in raw for c in ".eE")
            tokens.append(Token(NUM, raw, float(raw) if is_float else int(raw), i))
            i = match.end()
            continue

        # Palabra: función, constante, operador con letras o número con letras (hex)
        if ch.isascii() and ch.isalnum():
            match = (_ALNUM if digit_words else _LETTERS).match(text, i)
            word = match.group()
            upper = word.upper()
            if upper in KEYWORD_OPERATORS:
                tokens.append(Token(OP, upper, position=i))
            elif digit_words:
                try:
                    tokens.append(Token(NUM, word, int(word, ctx.base), i))
                except ValueError:
                    raise SyntaxCalcError(f"'{word}' no es válido en base {ctx.base}") from None
            else:
                tokens.append(Token(IDENT, word.lower(), position=i))
            i = match.end()
            continue

        raise SyntaxCalcError(f"Carácter no reconocido: '{ch}'")

    tokens.append(Token(END, "", position=n))
    return tokens
