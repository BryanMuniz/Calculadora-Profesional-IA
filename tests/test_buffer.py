import unittest

from calculadora.controller import ExpressionBuffer


def buf(text=""):
    b = ExpressionBuffer()
    b.set(text)
    return b


class Editing(unittest.TestCase):
    def test_operator_replaces_previous_operator(self):
        b = buf("5")
        b.add_operator("+")
        b.add_operator("×")
        self.assertEqual(b.text, "5 × ")

    def test_decimal_point_only_once_per_number(self):
        b = buf("3")
        b.add_decimal_point(); b.add_decimal_point()
        self.assertEqual(b.text, "3.")
        b.add_operator("+"); b.add_decimal_point()
        self.assertEqual(b.text, "3. + 0.")

    def test_backspace_removes_whole_tokens(self):
        b = buf("5 + ")
        b.backspace(); self.assertEqual(b.text, "5")
        b = buf("2 × sin(")
        b.backspace(); self.assertEqual(b.text, "2 × ")
        b.backspace(); self.assertEqual(b.text, "2")
        b = buf("12")
        b.backspace(); self.assertEqual(b.text, "1")

    def test_close_paren_only_when_needed(self):
        b = buf("(2 + 3")
        b.add_close_paren(); self.assertEqual(b.text, "(2 + 3)")
        b.add_close_paren(); self.assertEqual(b.text, "(2 + 3)")   # ya no hay nada que cerrar

    def test_for_evaluation(self):
        self.assertEqual(buf("2 + 3 × (4 + ").for_evaluation(), "2 + 3 × (4)")
        self.assertEqual(buf("5 + ").for_evaluation(), "5")
        self.assertEqual(buf("").for_evaluation(), "")


class LastOperand(unittest.TestCase):
    def test_wrap_number_group_and_function(self):
        b = buf("2 + 9"); b.wrap_last_operand("√(", ")")
        self.assertEqual(b.text, "2 + √(9)")
        b = buf("2 × (3 + 4)"); b.wrap_last_operand("abs(", ")")
        self.assertEqual(b.text, "2 × abs((3 + 4))")
        b = buf("sin(30)"); b.wrap_last_operand("√(", ")")
        self.assertEqual(b.text, "√(sin(30))")

    def test_reciprocal_keeps_priority(self):
        b = buf("2 ^ 3"); b.reciprocal_last_operand()
        self.assertEqual(b.text, "2 ^ (1 ÷ (3))")
        b = buf("(3 + 4)"); b.reciprocal_last_operand()
        self.assertEqual(b.text, "(1 ÷ (3 + 4))")

    def test_chained_powers_are_protected(self):
        b = buf("5"); b.add_power_suffix("^2")
        self.assertEqual(b.text, "5^2")
        b.add_power_suffix("^3")
        self.assertEqual(b.text, "(5^2)^3")
        b = buf("2 + 5"); b.add_power_suffix("^2"); b.negate_last_operand()
        self.assertEqual(b.text, "2 + (−5^2)")      # ± afecta a 5^2 completo

    def test_no_operand_means_no_change(self):
        b = buf("5 + ")
        self.assertFalse(b.wrap_last_operand("√(", ")"))
        self.assertEqual(b.text, "5 + ")

    def test_negate_toggles(self):
        b = buf("2 + 5")
        b.negate_last_operand(); self.assertEqual(b.text, "2 + (−5)")
        b.negate_last_operand(); self.assertEqual(b.text, "2 + 5")

    def test_clear_entry(self):
        b = buf("2 + 345"); b.clear_entry()
        self.assertEqual(b.text, "2 + ")
        b = buf("2 + "); b.clear_entry()
        self.assertEqual(b.text, "")


if __name__ == "__main__":
    unittest.main()
