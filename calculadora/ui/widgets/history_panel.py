"""Panel "Historial": lista de cálculos anteriores (clic para recuperarlos)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ...controller import CalculatorState
from .. import theme
from .flat_button import FlatButton


class HistoryPanel(tk.Frame):
    def __init__(self, parent, on_select: Callable[[int], None], on_clear: Callable[[], None]) -> None:
        super().__init__(parent, bg=theme.PANEL)
        self._on_select = on_select
        self._last_key = None

        body = tk.Frame(self, bg=theme.PANEL)
        body.pack(fill="both", expand=True)
        self._text = tk.Text(
            body, wrap="word", bg=theme.PANEL, fg=theme.TEXT, relief="flat", bd=0,
            highlightthickness=0, padx=16, pady=12, cursor="arrow", state="disabled",
            font=(theme.FONT, 11),
        )
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._text.pack(side="left", fill="both", expand=True)

        self._text.tag_configure("expression", foreground=theme.MUTED, font=(theme.MONO, 10), justify="right")
        self._text.tag_configure("result", foreground=theme.TEXT, font=(theme.MONO, 15, "bold"), justify="right")
        self._text.tag_configure("empty", foreground=theme.MUTED)

        FlatButton(self, "Borrar historial", on_clear, theme.STYLES["tab"], pady=6).pack(fill="x", padx=8, pady=6)

    def render(self, state: CalculatorState) -> None:
        if state.history == self._last_key:
            return
        self._last_key = state.history

        t = self._text
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not state.history:
            t.insert("end", "Todavía no hay cálculos.\nPresiona = para guardar uno.", "empty")
        for index, entry in enumerate(state.history):
            tag = f"entry{index}"
            t.insert("end", f"{entry.expression} =\n", ("expression", tag))
            t.insert("end", f"{entry.result}\n\n", ("result", tag))
            t.tag_bind(tag, "<Button-1>", lambda _e, i=index: self._on_select(i))
            t.tag_bind(tag, "<Enter>", lambda _e: t.configure(cursor="hand2"))
            t.tag_bind(tag, "<Leave>", lambda _e: t.configure(cursor="arrow"))
        t.configure(state="disabled")
