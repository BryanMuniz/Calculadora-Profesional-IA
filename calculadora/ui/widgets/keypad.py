"""Cuadrícula de teclas generada a partir de una lista de `KeySpec`."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, List, Set, Tuple

from .. import theme
from ..keypads import KeySpec, Row
from .flat_button import FlatButton


class Keypad(tk.Frame):
    def __init__(self, parent, rows: List[Row], on_press: Callable[[str, str], None]) -> None:
        super().__init__(parent, bg=theme.BG)
        self._keys: List[Tuple[KeySpec, FlatButton]] = []

        for row in rows:
            compact = all(key.kind == "memory" for key in row)  # la fila de memoria es más baja
            frame = tk.Frame(self, bg=theme.BG)
            frame.pack(fill="both", expand=not compact, pady=1)
            frame.rowconfigure(0, weight=1)
            for column, key in enumerate(row):
                frame.columnconfigure(column, weight=1, uniform="keys")
                button = FlatButton(
                    frame, key.label, lambda k=key: on_press(k.command, k.arg),
                    theme.STYLES[key.kind], pady=3 if compact else 8,
                )
                button.grid(row=0, column=column, sticky="nsew", padx=1)
                self._keys.append((key, button))

    def set_disabled_digits(self, digits: Set[str]) -> None:
        """Atenúa los dígitos que no existen en la base actual."""
        for key, button in self._keys:
            if key.command == "digit":
                button.set_enabled(key.arg not in digits)
