"""Panel "Paso a paso": muestra cómo se resuelve la expresión actual."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...controller import CalculatorState
from .. import theme

_PLACEHOLDER = (
    "Escribe una operación y aquí verás cómo se resuelve paso a paso.\n\n"
    "Ejemplo:  2 + 3 × 4\n\n"
    "Se respeta el orden de prioridad: paréntesis, potencias, × ÷ y por último + −."
)


class StepsPanel(tk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent, bg=theme.PANEL)
        self._last_key = None

        self._text = tk.Text(
            self, wrap="word", bg=theme.PANEL, fg=theme.TEXT, relief="flat", bd=0,
            highlightthickness=0, padx=16, pady=12, cursor="arrow", state="disabled",
            font=(theme.FONT, 11), spacing1=2, spacing3=2,
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._text.pack(side="left", fill="both", expand=True)

        t = self._text
        t.tag_configure("label", foreground=theme.MUTED, font=(theme.FONT, 9, "bold"))
        t.tag_configure("expression", foreground=theme.TEXT, font=(theme.MONO, 13))
        t.tag_configure("badge", background=theme.ACCENT, foreground="#000000", font=(theme.FONT, 9, "bold"))
        t.tag_configure("title", foreground=theme.TEXT, font=(theme.FONT, 12, "bold"))
        t.tag_configure("operation", foreground=theme.SUCCESS, font=(theme.MONO, 12), lmargin1=12, lmargin2=12)
        t.tag_configure("remaining", foreground=theme.TEXT, font=(theme.MONO, 11), lmargin1=12, lmargin2=12)
        t.tag_configure("hint", foreground=theme.MUTED, font=(theme.FONT, 9, "italic"), lmargin1=12, lmargin2=12)
        t.tag_configure("result", foreground=theme.ACCENT, font=(theme.MONO, 18, "bold"))
        t.tag_configure("placeholder", foreground=theme.MUTED, font=(theme.FONT, 11))

    def render(self, state: CalculatorState) -> None:
        key = (state.steps, state.steps_expression, state.steps_result)
        if key == self._last_key:
            return  # nada cambió: evita redibujar y el parpadeo
        self._last_key = key

        t = self._text
        t.configure(state="normal")
        t.delete("1.0", "end")

        if not state.steps_expression:
            t.insert("end", _PLACEHOLDER, "placeholder")
        else:
            t.insert("end", "EXPRESIÓN\n", "label")
            t.insert("end", f"{state.steps_expression}\n\n", "expression")
            if not state.steps:
                t.insert("end", "No hay operaciones que resolver: ya es un número.\n\n", "placeholder")
            for step in state.steps:
                t.insert("end", f" {step.index} ", "badge")
                t.insert("end", f"  {step.title}\n", "title")
                t.insert("end", f"{step.operation}\n", "operation")
                t.insert("end", f"Queda:  {step.expression}\n", "remaining")
                if step.hint:
                    t.insert("end", f"{step.hint}\n", "hint")
                t.insert("end", "\n")
            t.insert("end", "RESULTADO\n", "label")
            t.insert("end", state.steps_result, "result")

        t.configure(state="disabled")
        t.yview_moveto(0)
