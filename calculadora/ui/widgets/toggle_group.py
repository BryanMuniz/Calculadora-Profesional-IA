"""Grupo de botones tipo "pestañas": solo uno está activo a la vez."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Sequence, Tuple

from .. import theme
from .flat_button import FlatButton


class ToggleGroup(tk.Frame):
    def __init__(self, parent, options: Sequence[Tuple[str, str]],
                 on_select: Callable[[str], None], bg: str = theme.BG) -> None:
        super().__init__(parent, bg=bg)
        self._buttons: Dict[str, FlatButton] = {}
        for value, label in options:
            button = FlatButton(self, label, lambda v=value: on_select(v), theme.STYLES["tab"],
                                padx=10, pady=6)
            button.pack(side="left", fill="x", expand=True, padx=1)
            self._buttons[value] = button

    def set_value(self, selected: str) -> None:
        for value, button in self._buttons.items():
            button.set_style(theme.STYLES["tab_on" if value == selected else "tab"])
