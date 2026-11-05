"""Prueba de humo de la interfaz usando un tkinter simulado (ver fake_tk.py)."""
import sys
import unittest

import fake_tk

fake_tk.install()   # debe ejecutarse ANTES de importar calculadora.ui

from calculadora.controller import CalculatorController, Mode  # noqa: E402
from calculadora.ui.app import CalculatorApp                    # noqa: E402
from calculadora.ui.keypads import LAYOUTS                      # noqa: E402


class UiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.controller = CalculatorController()
        self.app = CalculatorApp(self.controller)

    def press_all_keys(self):
        """Simula el clic en cada tecla del teclado visible."""
        for _spec, button in self.app._keypad._keys:
            button._command()

    def test_window_builds_and_shows_placeholder(self):
        self.assertIn("paso a paso", self.app._steps_panel._text.get_text())

    def test_steps_panel_renders_a_calculation(self):
        for command in ("digit:2", "operator:+", "digit:3", "operator:×", "digit:4"):
            name, _, arg = command.partition(":")
            self.controller.dispatch(name, arg)
        text = self.app._steps_panel._text.get_text()
        self.assertIn("Multiplicación", text)
        self.assertIn("3 × 4 = 12", text)
        self.assertIn("Queda:  2 + 12", text)
        self.assertEqual(self.app._display._primary.options["text"], "2 + 3 × 4")

    def test_history_panel_lists_results(self):
        for command in ("digit:6", "operator:×", "digit:7", "equals"):
            name, _, arg = command.partition(":")
            self.controller.dispatch(name, arg)
        self.assertIn("42", self.app._history_panel._text.get_text())

    def test_every_mode_builds_and_every_key_can_be_pressed(self):
        for mode in Mode:
            self.controller.dispatch("set_mode", mode.name)
            self.assertIs(self.app._shown_mode, mode)
            self.assertEqual(len(self.app._keypad._keys), sum(len(r) for r in LAYOUTS[mode]))
            for _ in range(2):          # dos vueltas: pasa por estados distintos
                self.press_all_keys()
                self.controller.dispatch("clear")

    def test_programmer_panel_updates(self):
        self.controller.dispatch("set_mode", "PROGRAMMER")
        self.controller.dispatch("digit", "5")
        self.controller.dispatch("digit", "5")
        panel = self.app._programmer_panel
        self.assertEqual(panel._rows[16]["value"].options["text"], "37")
        self.controller.dispatch("set_base", "2")
        self.assertEqual(panel._rows[2]["stripe"].options["bg"], "#4cc2ff")

    def test_error_is_shown_in_red(self):
        for command in ("digit:5", "operator:÷", "digit:0", "equals"):
            name, _, arg = command.partition(":")
            self.controller.dispatch(name, arg)
        self.assertEqual(self.app._display._primary.options["fg"], "#ff7b72")


if __name__ == "__main__":
    unittest.main()
