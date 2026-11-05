"""Tema visual: colores, tipografías y estilos de botón en UN solo lugar.

(Equivalente web: el archivo de variables CSS / design tokens.)
Para cambiar el aspecto de toda la app basta con editar este archivo.
"""
from __future__ import annotations

from dataclasses import dataclass

FONT = "Segoe UI"
MONO = "Consolas"

# Colores base
BG = "#1c1c1c"
PANEL = "#272727"
TEXT = "#ffffff"
MUTED = "#a8a8a8"
DISABLED = "#5e5e5e"
ACCENT = "#4cc2ff"
ERROR = "#ff7b72"
SUCCESS = "#7ee787"


@dataclass(frozen=True)
class ButtonStyle:
    bg: str
    hover: str
    pressed: str
    fg: str
    size: int = 13
    bold: bool = False

    @property
    def font(self):
        return (FONT, self.size, "bold" if self.bold else "normal")


STYLES = {
    "number":   ButtonStyle("#3b3b3b", "#4a4a4a", "#2c2c2c", TEXT, 15, True),
    "operator": ButtonStyle("#2f2f2f", "#3c3c3c", "#242424", TEXT, 14),
    "function": ButtonStyle("#2f2f2f", "#3c3c3c", "#242424", TEXT, 12),
    "equals":   ButtonStyle(ACCENT, "#76d0ff", "#3aa5e0", "#000000", 17, True),
    "memory":   ButtonStyle(BG, "#2b2b2b", "#222222", MUTED, 10, True),
    "tab":      ButtonStyle(BG, "#2b2b2b", "#222222", MUTED, 10, True),
    "tab_on":   ButtonStyle("#3b3b3b", "#4a4a4a", "#2c2c2c", ACCENT, 10, True),
}
