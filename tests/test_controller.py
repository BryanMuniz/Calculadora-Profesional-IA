import unittest

from calculadora.controller import CalculatorController, Mode
from calculadora.services import HistoryService, MemoryService


class Session:
    """Ayuda para escribir tests como si se presionaran botones: s.press("digit:2", "equals")."""

    def __init__(self):
        self.controller = CalculatorController(HistoryService(), MemoryService())

    def press(self, *commands):
        for command in commands:
            name, _, arg = command.partition(":")
            self.controller.dispatch(name, arg)
        return self.controller.state

    def type(self, text):
        mapping = {"+": "+", "-": "−", "*": "×", "/": "÷"}
        for ch in text:
            if ch.isdigit():
                self.press(f"digit:{ch}")
            elif ch == ".":
                self.press("decimal")
            elif ch in mapping:
                self.press(f"operator:{mapping[ch]}")
        return self.controller.state


class StandardMode(unittest.TestCase):
    def setUp(self):
        self.s = Session()

    def test_basic_flow_with_live_preview(self):
        state = self.s.type("2+3*4")
        self.assertEqual(state.primary, "2 + 3 × 4")
        self.assertEqual(state.secondary, "= 14")
        state = self.s.press("equals")
        self.assertEqual((state.primary, state.secondary), ("14", "2 + 3 × 4 ="))
        self.assertEqual(len(state.steps), 2)

    def test_operator_after_equals_continues_from_result(self):
        self.s.type("2+3"); self.s.press("equals")
        state = self.s.type("*2")
        self.assertEqual(state.primary, "5 × 2")

    def test_digit_after_equals_starts_over(self):
        self.s.type("2+3"); self.s.press("equals")
        self.assertEqual(self.s.type("7").primary, "7")

    def test_negative_result_is_protected_when_continuing(self):
        self.s.type("2-5"); self.s.press("equals")
        self.assertEqual(self.s.type("*2").primary, "(-3) × 2")
        self.assertEqual(self.s.press("equals").primary, "-6")

    def test_error_and_recovery(self):
        self.s.type("5/0")
        state = self.s.press("equals")
        self.assertTrue(state.is_error)
        self.assertIn("cero", state.primary)
        state = self.s.press("backspace", "digit:2")      # el error desaparece al seguir editando
        self.assertFalse(state.is_error)
        self.assertEqual(self.s.press("equals").primary, "2.5")

    def test_unclosed_parentheses_are_closed_on_equals(self):
        self.s.press("open_paren", "digit:2", "operator:+", "digit:3")
        state = self.s.press("equals")
        self.assertEqual(state.primary, "5")
        self.assertEqual(state.secondary, "(2 + 3) =")

    def test_unary_buttons(self):
        self.assertEqual(self.s.type("9") and self.s.press("sqrt", "equals").primary, "3")
        self.s.press("clear"); self.s.type("4")
        self.assertEqual(self.s.press("reciprocal", "equals").primary, "0.25")
        self.s.press("clear"); self.s.type("5")
        self.assertEqual(self.s.press("postfix:^2", "equals").primary, "25")
        self.s.press("clear"); self.s.type("5")
        self.assertEqual(self.s.press("negate", "equals").primary, "-5")

    def test_percent_like_windows(self):
        self.s.type("200+10"); 
        self.assertEqual(self.s.press("postfix:%", "equals").primary, "220")

    def test_backspace_after_equals_edits_the_expression(self):
        self.s.type("2+3"); self.s.press("equals")
        state = self.s.press("backspace")
        self.assertEqual(state.primary, "2 + ")  # (el "3" se borró; queda editable)

    def test_clear_entry_and_clear(self):
        self.s.type("2+345")
        self.assertEqual(self.s.press("clear_entry").primary, "2 + ")
        self.assertEqual(self.s.press("clear").primary, "0")

    def test_leading_operator_assumes_zero(self):
        self.assertEqual(self.s.press("operator:+").primary, "0 + ")

    def test_decimal_input(self):
        self.assertEqual(self.s.press("decimal").primary, "0.")
        self.assertEqual(self.s.type("5").primary, "0.5")

    def test_close_paren_ignored_when_nothing_open(self):
        self.assertEqual(self.s.type("5") and self.s.press("close_paren").primary, "5")


class Memory(unittest.TestCase):
    def test_memory_buttons(self):
        s = Session()
        s.type("5"); state = s.press("mem_store")
        self.assertEqual(state.memory_text, "5")
        s.press("clear"); s.type("3"); s.press("mem_add")
        self.assertEqual(s.controller.state.memory_text, "8")
        s.press("mem_sub")
        self.assertEqual(s.controller.state.memory_text, "5")
        s.press("clear"); s.type("1+")
        self.assertEqual(s.press("mem_recall").primary, "1 + 5")
        self.assertEqual(s.press("mem_clear").memory_text, "")

    def test_memory_with_invalid_expression_shows_error(self):
        s = Session()
        s.press("open_paren", "function:sin")
        self.assertTrue(s.press("mem_store").is_error)


class ScientificMode(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.s.press("set_mode:SCIENTIFIC")

    def test_functions_and_angle_modes(self):
        self.s.press("function:sin", "digit:3", "digit:0", "close_paren")
        self.assertEqual(self.s.press("equals").primary, "0.5")
        state = self.s.press("set_angle:RAD")          # el resultado se recalcula
        self.assertNotEqual(state.primary, "0.5")
        self.assertEqual(state.angle_mode.name, "RAD")

    def test_constants_and_power(self):
        self.s.press("constant:π", "operator:^", "digit:2")
        self.assertEqual(self.s.press("equals").primary, "9.86960440108936")

    def test_power10_and_exp(self):
        self.s.press("power10", "digit:3")
        self.assertEqual(self.s.press("equals").primary, "1000")

    def test_factorial(self):
        self.s.press("digit:5", "postfix:!")
        self.assertEqual(self.s.press("equals").primary, "120")


class ProgrammerMode(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.s.press("set_mode:PROGRAMMER")

    def test_base_views(self):
        self.s.press("digit:2", "digit:5", "digit:5")
        views = self.s.controller.state.base_views
        self.assertEqual((views["DEC"], views["HEX"], views["BIN"]), ("255", "FF", "1111 1111"))

    def test_changing_base_converts_the_value(self):
        self.s.press("digit:2", "digit:5", "digit:5", "set_base:16")
        state = self.s.controller.state
        self.assertEqual((state.primary, state.base), ("FF", 16))
        state = self.s.press("set_base:2")
        self.assertEqual(state.primary, "11111111")

    def test_invalid_digits_are_ignored(self):
        self.s.press("set_base:8", "digit:9")
        self.assertEqual(self.s.controller.state.primary, "0")
        self.s.press("digit:7")
        self.assertEqual(self.s.controller.state.primary, "7")

    def test_bitwise_with_hex(self):
        self.s.press("set_base:16", "digit:F", "digit:F", "operator:AND", "digit:0", "digit:F")
        self.assertEqual(self.s.press("equals").primary, "F")

    def test_word_size_changes_wraparound(self):
        self.s.press("set_word:8", "digit:1", "digit:2", "digit:7", "operator:+", "digit:1")
        self.assertEqual(self.s.press("equals").primary, "-128")

    def test_decimal_point_is_ignored(self):
        self.s.press("digit:1", "decimal")
        self.assertEqual(self.s.controller.state.primary, "1")

    def test_leaving_programmer_resets(self):
        self.s.press("set_base:16", "digit:F")
        state = self.s.press("set_mode:STANDARD")
        self.assertEqual((state.primary, state.base, state.mode), ("0", 10, Mode.STANDARD))

    def test_not_prefix(self):
        self.s.press("prefix:NOT", "digit:0")
        self.assertEqual(self.s.press("equals").primary, "-1")


class History(unittest.TestCase):
    def test_history_add_recall_clear(self):
        s = Session()
        s.type("2+3"); s.press("equals")
        s.press("clear"); s.type("6*7"); s.press("equals")
        history = s.controller.state.history
        self.assertEqual([h.result for h in history], ["42", "5"])   # la más reciente primero

        state = s.press("history_recall:1")
        self.assertEqual((state.primary, state.secondary), ("5", "2 + 3 ="))
        self.assertEqual(len(state.steps), 1)

        self.assertEqual(s.press("history_clear").history, ())

    def test_history_restores_the_original_mode(self):
        s = Session()
        s.press("set_mode:PROGRAMMER", "set_base:16", "digit:F", "operator:+", "digit:1", "equals")
        s.press("set_mode:STANDARD")
        state = s.press("history_recall:0")
        self.assertEqual((state.mode, state.base, state.primary), (Mode.PROGRAMMER, 16, "10"))


class Observers(unittest.TestCase):
    def test_listeners_receive_every_change(self):
        s = Session()
        seen = []
        s.controller.subscribe(seen.append)
        s.press("digit:7", "digit:8")
        self.assertEqual([st.primary for st in seen], ["7", "78"])

    def test_unknown_command_raises(self):
        with self.assertRaises(KeyError):
            Session().press("fly_to_the_moon")


if __name__ == "__main__":
    unittest.main()
