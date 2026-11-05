import unittest

from calculadora.controller import CalculatorController, Mode
from calculadora.core import EvalContext
from calculadora.services import HistoryEntry, HistoryService, MemoryService
from calculadora.ui.bindings import translate_key
from calculadora.ui.keypads import LAYOUTS, disabled_digits


def entry(n):
    return HistoryEntry(f"{n}+1", f"{n} + 1", str(n + 1), (), "STANDARD", EvalContext())


class HistoryServiceTests(unittest.TestCase):
    def test_newest_first_and_limit(self):
        service = HistoryService(max_items=3)
        for n in range(5):
            service.add(entry(n))
        self.assertEqual([e.result for e in service.all()], ["5", "4", "3"])
        self.assertEqual(len(service), 3)
        service.clear()
        self.assertEqual(len(service), 0)


class MemoryServiceTests(unittest.TestCase):
    def test_operations(self):
        memory = MemoryService()
        self.assertFalse(memory.has_value)
        memory.add(5); memory.add(2); memory.subtract(1)
        self.assertEqual(memory.value, 6)
        memory.store(10); self.assertEqual(memory.value, 10)
        memory.clear(); self.assertIsNone(memory.value)


class KeyboardTranslation(unittest.TestCase):
    def state(self, mode=Mode.STANDARD, base=10):
        controller = CalculatorController()
        controller.dispatch("set_mode", mode.name)
        if base != 10:
            controller.dispatch("set_base", str(base))
        return controller.state

    def test_common_keys(self):
        st = self.state()
        self.assertEqual(translate_key("7", "7", st), ("digit", "7"))
        self.assertEqual(translate_key("-", "minus", st), ("operator", "−"))
        self.assertEqual(translate_key("*", "asterisk", st), ("operator", "×"))
        self.assertEqual(translate_key("/", "slash", st), ("operator", "÷"))
        self.assertEqual(translate_key("", "Return", st), ("equals", ""))
        self.assertEqual(translate_key("", "BackSpace", st), ("backspace", ""))
        self.assertEqual(translate_key("", "Escape", st), ("clear", ""))
        self.assertEqual(translate_key("a", "a", st), None)

    def test_mode_specific_keys(self):
        self.assertEqual(translate_key("p", "p", self.state(Mode.SCIENTIFIC)), ("constant", "π"))
        self.assertEqual(translate_key("e", "e", self.state(Mode.SCIENTIFIC)), ("constant", "e"))
        self.assertIsNone(translate_key("p", "p", self.state(Mode.STANDARD)))
        hexa = self.state(Mode.PROGRAMMER, 16)
        self.assertEqual(translate_key("e", "e", hexa), ("digit", "E"))
        self.assertIsNone(translate_key("e", "e", self.state(Mode.PROGRAMMER, 10)))


class KeypadLayouts(unittest.TestCase):
    def test_every_key_maps_to_a_real_controller_command(self):
        controller = CalculatorController()
        for mode, rows in LAYOUTS.items():
            for row in rows:
                for key in row:
                    self.assertIn(key.command, controller._handlers, f"{mode}: {key.label}")

    def test_disabled_digits(self):
        self.assertEqual(disabled_digits(2), set("23456789ABCDEF"))
        self.assertEqual(disabled_digits(8), set("89ABCDEF"))
        self.assertEqual(disabled_digits(16), set())


if __name__ == "__main__":
    unittest.main()
