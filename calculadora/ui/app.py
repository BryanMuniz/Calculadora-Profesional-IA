"""Ventana principal: ensambla los widgets y los conecta al controlador.

Esta clase NO calcula nada. Solo:
  1. construye la interfaz (los widgets),
  2. envía cada clic/tecla al controlador con `dispatch(...)`,
  3. cuando el controlador avisa de un cambio, dibuja el nuevo estado (`_render`).
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional

from ..controller import CalculatorController, CalculatorState, Mode
from ..core import AngleMode
from . import theme
from .bindings import install_keyboard_shortcuts
from .keypads import LAYOUTS, disabled_digits
from .widgets import Display, HistoryPanel, Keypad, ProgrammerPanel, StepsPanel, ToggleGroup


class CalculatorApp(tk.Tk):
    def __init__(self, controller: CalculatorController) -> None:
        super().__init__()
        self.title("Calculadora paso a paso")
        self.geometry("980x740")
        self.minsize(880, 660)
        self.configure(bg=theme.BG)

        self._controller = controller
        self._shown_mode: Optional[Mode] = None
        self._keypad: Optional[Keypad] = None

        self._build_calculator_column()
        self._build_side_column()
        install_keyboard_shortcuts(self, controller)

        controller.subscribe(self._render)   # "avísame cuando cambie el estado"
        self._render(controller.state)       # primer dibujado

    # ═══════════════ construcción de la interfaz ═══════════════
    def _build_calculator_column(self) -> None:
        self.columnconfigure(0, weight=3, minsize=470)
        self.columnconfigure(1, weight=2, minsize=340)
        self.rowconfigure(0, weight=1)

        column = tk.Frame(self, bg=theme.BG)
        column.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)

        self._mode_toggle = ToggleGroup(
            column, [(m.name, m.value) for m in Mode],
            on_select=lambda name: self._controller.dispatch("set_mode", name),
        )
        self._mode_toggle.pack(fill="x", pady=(0, 8))

        self._display = Display(column)
        self._display.pack(fill="x", padx=4)

        # Zona de opciones: cambia según el modo (ángulos / programador)
        self._options_row = tk.Frame(column, bg=theme.BG)
        self._options_row.pack(fill="x", pady=(4, 6))
        self._angle_toggle = ToggleGroup(
            self._options_row, [(a.name, a.value) for a in AngleMode],
            on_select=lambda name: self._controller.dispatch("set_angle", name),
        )
        self._programmer_panel = ProgrammerPanel(
            self._options_row,
            on_base=lambda base: self._controller.dispatch("set_base", str(base)),
            on_word=lambda bits: self._controller.dispatch("set_word", str(bits)),
        )

        self._keypad_host = tk.Frame(column, bg=theme.BG)
        self._keypad_host.pack(fill="both", expand=True)

    def _build_side_column(self) -> None:
        side = tk.Frame(self, bg=theme.PANEL)
        side.grid(row=0, column=1, sticky="nsew", padx=(7, 14), pady=14)
        side.rowconfigure(1, weight=1)
        side.columnconfigure(0, weight=1)

        tabs = ToggleGroup(
            side, [("steps", "Paso a paso"), ("history", "Historial")],
            on_select=self._show_tab, bg=theme.PANEL,
        )
        tabs.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self._tabs = tabs

        container = tk.Frame(side, bg=theme.PANEL)
        container.grid(row=1, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self._steps_panel = StepsPanel(container)
        self._history_panel = HistoryPanel(
            container,
            on_select=self._recall_history,
            on_clear=lambda: self._controller.dispatch("history_clear"),
        )
        for panel in (self._steps_panel, self._history_panel):
            panel.grid(row=0, column=0, sticky="nsew")  # una encima de otra
        self._panels = {"steps": self._steps_panel, "history": self._history_panel}
        self._show_tab("steps")

    # ═══════════════ eventos de la interfaz ═══════════════
    def _show_tab(self, name: str) -> None:
        self._panels[name].tkraise()
        self._tabs.set_value(name)

    def _recall_history(self, index: int) -> None:
        self._controller.dispatch("history_recall", str(index))
        self._show_tab("steps")

    # ═══════════════ dibujar el estado ═══════════════
    def _show_mode(self, mode: Mode) -> None:
        """Cambia el teclado y las opciones cuando cambia el modo."""
        if self._keypad is not None:
            self._keypad.destroy()
        self._keypad = Keypad(self._keypad_host, LAYOUTS[mode], self._controller.dispatch)
        self._keypad.pack(fill="both", expand=True)

        self._angle_toggle.pack_forget()
        self._programmer_panel.pack_forget()
        if mode is Mode.SCIENTIFIC:
            self._angle_toggle.pack(fill="x")
        elif mode is Mode.PROGRAMMER:
            self._programmer_panel.pack(fill="x")
        self._shown_mode = mode

    def _render(self, state: CalculatorState) -> None:
        if state.mode is not self._shown_mode:
            self._show_mode(state.mode)
        self._mode_toggle.set_value(state.mode.name)
        self._display.render(state)
        self._angle_toggle.set_value(state.angle_mode.name)
        if state.mode is Mode.PROGRAMMER:
            self._programmer_panel.render(state)
            self._keypad.set_disabled_digits(disabled_digits(state.base))
        self._steps_panel.render(state)
        self._history_panel.render(state)
