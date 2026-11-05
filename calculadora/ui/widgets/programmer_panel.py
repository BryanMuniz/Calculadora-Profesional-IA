"""Panel del modo programador: el valor en HEX/DEC/OCT/BIN y el tamaño de palabra."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict

from ...controller import CalculatorState
from .. import theme
from .toggle_group import ToggleGroup

_BASES = (("HEX", 16), ("DEC", 10), ("OCT", 8), ("BIN", 2))


class ProgrammerPanel(tk.Frame):
    def __init__(self, parent, on_base: Callable[[int], None], on_word: Callable[[int], None]) -> None:
        super().__init__(parent, bg=theme.BG)
        self._rows: Dict[int, Dict[str, tk.Widget]] = {}

        for name, base in _BASES:
            row = tk.Frame(self, bg=theme.BG, cursor="hand2")
            row.pack(fill="x", pady=1)
            stripe = tk.Frame(row, width=3, bg=theme.BG)
            stripe.pack(side="left", fill="y")
            label = tk.Label(row, text=name, width=4, anchor="w", fg=theme.MUTED, bg=theme.BG,
                             font=(theme.FONT, 9, "bold"), cursor="hand2")
            label.pack(side="left", padx=(6, 0))
            value = tk.Label(row, anchor="w", fg=theme.TEXT, bg=theme.BG, font=(theme.MONO, 11), cursor="hand2")
            value.pack(side="left", fill="x", expand=True)
            for widget in (row, stripe, label, value):
                widget.bind("<Button-1>", lambda _e, b=base: on_base(b))
            self._rows[base] = {"stripe": stripe, "value": value}

        self._word = ToggleGroup(
            self, [("64", "QWORD"), ("32", "DWORD"), ("16", "WORD"), ("8", "BYTE")],
            on_select=lambda v: on_word(int(v)),
        )
        self._word.pack(fill="x", pady=(6, 2))

    def render(self, state: CalculatorState) -> None:
        for name, base in _BASES:
            row = self._rows[base]
            row["value"].configure(text=state.base_views.get(name, ""))
            row["stripe"].configure(bg=theme.ACCENT if base == state.base else theme.BG)
        self._word.set_value(str(state.word_bits))
