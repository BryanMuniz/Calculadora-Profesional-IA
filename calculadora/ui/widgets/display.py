"""La pantalla: línea pequeña (vista previa), número grande y avisos."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from ...controller import CalculatorState, Mode
from .. import theme

_MAX_CHARS = 30  # si el texto es más largo se muestra solo su final, con "…"


class Display(tk.Frame):
    def __init__(self, parent) -> None:
        super().__init__(parent, bg=theme.BG)

        top = tk.Frame(self, bg=theme.BG)
        top.pack(fill="x")
        self._info = tk.Label(top, anchor="w", fg=theme.MUTED, bg=theme.BG, font=(theme.FONT, 9, "bold"))
        self._info.pack(side="left")
        self._memory = tk.Label(top, anchor="e", fg=theme.ACCENT, bg=theme.BG, font=(theme.FONT, 9, "bold"))
        self._memory.pack(side="right")

        self._secondary = tk.Label(self, anchor="e", fg=theme.MUTED, bg=theme.BG, font=(theme.FONT, 12))
        self._secondary.pack(fill="x")

        self._primary_font = tkfont.Font(family=theme.FONT, size=38, weight="bold")
        self._primary = tk.Label(self, anchor="e", fg=theme.TEXT, bg=theme.BG, font=self._primary_font)
        self._primary.pack(fill="x", pady=(0, 6))

    def render(self, state: CalculatorState) -> None:
        self._info.configure(text=self._info_text(state))
        self._memory.configure(text=f"M = {state.memory_text}" if state.memory_text else "")
        self._secondary.configure(text=self._clip(state.secondary))

        text = self._clip(state.primary)
        self._primary_font.configure(size=self._font_size(len(text), state.is_error))
        self._primary.configure(text=text, fg=theme.ERROR if state.is_error else theme.TEXT)

    @staticmethod
    def _info_text(state: CalculatorState) -> str:
        if state.mode is Mode.SCIENTIFIC:
            return state.angle_mode.value
        if state.mode is Mode.PROGRAMMER:
            return f"BASE {state.base}  ·  {state.word_bits} BITS"
        return ""

    @staticmethod
    def _clip(text: str) -> str:
        return text if len(text) <= _MAX_CHARS else "…" + text[-(_MAX_CHARS - 1):]

    @staticmethod
    def _font_size(length: int, is_error: bool) -> int:
        """Reduce la letra a medida que el texto crece, para que siempre quepa."""
        if is_error:
            return max(12, 20 - max(0, length - 20) // 2)
        return max(16, 38 - max(0, length - 11) * 2)
