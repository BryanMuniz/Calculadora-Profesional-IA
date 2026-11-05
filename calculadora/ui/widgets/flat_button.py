"""Botón plano personalizado.

Usamos `tk.Label` en lugar de `tk.Button` porque en macOS los botones nativos
ignoran los colores de fondo. Un Label permite el mismo aspecto en todos los
sistemas, y le añadimos a mano el efecto hover y el clic.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from .. import theme


class FlatButton(tk.Label):
    def __init__(self, parent, text: str, command: Callable[[], None],
                 style: theme.ButtonStyle, **options) -> None:
        super().__init__(parent, text=text, font=style.font, cursor="hand2", **options)
        self._command = command
        self._style = style
        self._enabled = True
        self._hover = False
        self._pressed = False
        self._paint()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    # ── API ──
    def set_style(self, style: theme.ButtonStyle) -> None:
        self._style = style
        self.configure(font=style.font)
        self._paint()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._paint()

    # ── interno ──
    def _paint(self) -> None:
        style = self._style
        if not self._enabled:
            self.configure(bg=style.bg, fg=theme.DISABLED)
        elif self._pressed:
            self.configure(bg=style.pressed, fg=style.fg)
        elif self._hover:
            self.configure(bg=style.hover, fg=style.fg)
        else:
            self.configure(bg=style.bg, fg=style.fg)

    def _on_enter(self, _event) -> None:
        self._hover = True
        self._paint()

    def _on_leave(self, _event) -> None:
        self._hover = self._pressed = False
        self._paint()

    def _on_press(self, _event) -> None:
        if self._enabled:
            self._pressed = True
            self._paint()

    def _on_release(self, event) -> None:
        was_pressed = self._pressed
        self._pressed = False
        self._paint()
        inside = 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        if was_pressed and self._enabled and inside:
            self._command()
