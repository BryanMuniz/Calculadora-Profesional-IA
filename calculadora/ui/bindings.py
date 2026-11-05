"""Atajos de teclado: traducen una tecla física en un comando del controlador."""
from __future__ import annotations

from typing import Optional, Tuple

from ..controller import CalculatorState, Mode

Action = Tuple[str, str]  # (comando, argumento)

_SYMBOL_KEYS = {
    "+": ("operator", "+"), "-": ("operator", "−"), "*": ("operator", "×"),
    "/": ("operator", "÷"), "^": ("operator", "^"),
    "(": ("open_paren", ""), ")": ("close_paren", ""),
    "%": ("postfix", "%"), "!": ("postfix", "!"), "=": ("equals", ""),
    "&": ("operator", "AND"), "|": ("operator", "OR"),
}
_SPECIAL_KEYSYMS = {
    "Return": ("equals", ""), "KP_Enter": ("equals", ""),
    "BackSpace": ("backspace", ""), "Escape": ("clear", ""), "Delete": ("clear_entry", ""),
}


def translate_key(char: str, keysym: str, state: CalculatorState) -> Optional[Action]:
    """Devuelve el comando asociado a la tecla, o None si no hace nada.

    Es una función pura (no usa tkinter), así que se puede probar con tests.
    """
    if keysym in _SPECIAL_KEYSYMS:
        return _SPECIAL_KEYSYMS[keysym]
    if not char:
        return None

    programmer = state.mode is Mode.PROGRAMMER
    scientific = state.mode is Mode.SCIENTIFIC

    if char.isdigit() and char.isascii():
        return ("digit", char)
    if programmer and state.base == 16 and char.upper() in "ABCDEF":
        return ("digit", char.upper())
    if char in ".,":
        return ("decimal", "")
    if char in _SYMBOL_KEYS:
        return _SYMBOL_KEYS[char]
    if scientific and char.lower() == "p":
        return ("constant", "π")
    if scientific and char.lower() == "e":
        return ("constant", "e")
    return None


def install_keyboard_shortcuts(root, controller) -> None:
    """Conecta el teclado físico a la ventana (`root.bind` = addEventListener)."""

    def on_key(event):
        action = translate_key(event.char, event.keysym, controller.state)
        if action:
            controller.dispatch(*action)
            return "break"

    def copy_result(_event=None):
        root.clipboard_clear()
        root.clipboard_append(controller.state.primary)
        return "break"

    root.bind("<Key>", on_key)
    root.bind("<Control-c>", copy_result)
