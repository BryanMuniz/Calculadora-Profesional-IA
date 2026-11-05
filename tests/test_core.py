import unittest

from calculadora.core import AngleMode, CalcError, EvalContext, calculate
from calculadora.core.formatting import all_bases, format_decimal, to_base, wrap_signed

DEG = EvalContext()
RAD = EvalContext(angle_mode=AngleMode.RAD)


def prog(base=10, bits=64):
    return EvalContext(base=base, word_bits=bits, integer_mode=True)


class BasicArithmetic(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(calculate("2 + 3 × 4").text, "14")
        self.assertEqual(calculate("(2 + 3) × 4").text, "20")
        self.assertEqual(calculate("10 − 2 − 3").text, "5")        # asociativa a la izquierda
        self.assertEqual(calculate("2^3^2").text, "512")           # asociativa a la derecha
        self.assertEqual(calculate("-2^2").text, "-4")
        self.assertEqual(calculate("2^-1").text, "0.5")

    def test_decimals_and_division(self):
        self.assertEqual(calculate("0.1 + 0.2").text, "0.3")
        self.assertEqual(calculate("10 ÷ 4").text, "2.5")
        self.assertEqual(calculate("10 ÷ 5").text, "2")
        self.assertEqual(calculate("1 ÷ 3").text, "0.333333333333333")

    def test_modulo_sign_follows_dividend(self):
        self.assertEqual(calculate("7 mod 3").text, "1")
        self.assertEqual(calculate("-7 mod 3").text, "-1")

    def test_implicit_multiplication(self):
        self.assertEqual(calculate("2(3 + 1)").text, "8")
        self.assertEqual(calculate("2π").text, "6.28318530717959")

    def test_percent(self):
        self.assertEqual(calculate("200 + 10%").text, "220")
        self.assertEqual(calculate("200 − 10%").text, "180")
        self.assertEqual(calculate("50%").text, "0.5")
        self.assertEqual(calculate("200 × 10%").text, "20")

    def test_factorial_and_power(self):
        self.assertEqual(calculate("5!").text, "120")
        self.assertEqual(calculate("2^10").text, "1024")
        self.assertEqual(calculate("2^100").text, "1.26765060022823e+30")


class Functions(unittest.TestCase):
    def test_degrees(self):
        self.assertEqual(calculate("sin(30)", DEG).text, "0.5")
        self.assertEqual(calculate("cos(90)", DEG).text, "0")
        self.assertEqual(calculate("sin(180)", DEG).text, "0")
        self.assertEqual(calculate("tan(45)", DEG).text, "1")
        self.assertEqual(calculate("asin(0.5)", DEG).text, "30")

    def test_radians(self):
        self.assertEqual(calculate("sin(π ÷ 2)", RAD).text, "1")
        self.assertEqual(calculate("cos(0)", RAD).text, "1")

    def test_roots_and_logs(self):
        self.assertEqual(calculate("√(16)").text, "4")
        self.assertEqual(calculate("∛(27)").text, "3")
        self.assertEqual(calculate("log(1000)").text, "3")
        self.assertEqual(calculate("ln(e)").text, "1")
        self.assertEqual(calculate("abs(-5)").text, "5")
        self.assertEqual(calculate("exp(0)").text, "1")


class Errors(unittest.TestCase):
    def assertError(self, text, ctx=None, contains=""):
        with self.assertRaises(CalcError) as cm:
            calculate(text, ctx)
        self.assertIn(contains.lower(), cm.exception.message.lower())

    def test_math_errors(self):
        self.assertError("5 ÷ 0", contains="cero")
        self.assertError("√(-1)", contains="negativo")
        self.assertError("ln(0)", contains="positivos")
        self.assertError("tan(90)", contains="tangente")
        self.assertError("(-1)!", contains="factorial")
        self.assertError("2.5!", contains="factorial")
        self.assertError("1000!", contains="rango")
        self.assertError("asin(2)", contains="entre -1 y 1")
        self.assertError("0^0", contains="indefinido")
        self.assertError("10^1000", contains="rango")

    def test_syntax_errors(self):
        self.assertError("(2 + 3", contains="paréntesis")
        self.assertError("2 + 3)", contains="paréntesis")
        self.assertError("2 +", contains="incompleta")
        self.assertError("", contains="operación")
        self.assertError("2 $ 3", contains="no reconocido")
        self.assertError("foo(3)", contains="desconocida")
        self.assertError("sin 30", contains="paréntesis")
        self.assertError("2 × × 3")


class StepByStep(unittest.TestCase):
    def test_priority_order(self):
        result = calculate("2 + 3 × 4 − (6 ÷ 2)^2")
        self.assertEqual(result.text, "5")
        self.assertEqual([s.title for s in result.steps],
                         ["División", "Potencia", "Multiplicación", "Suma", "Resta"])
        self.assertEqual(result.steps[0].operation, "6 ÷ 2 = 3")
        self.assertEqual(result.steps[2].expression, "2 + 12 − 9")
        self.assertEqual(result.steps[-1].expression, "5")

    def test_hint_mentions_parentheses(self):
        step = calculate("(2 + 3) × 4").steps[0]
        self.assertIn("paréntesis", step.hint)

    def test_percent_steps(self):
        result = calculate("200 + 10%")
        self.assertEqual(result.steps[0].operation, "10% de 200 = 20")
        self.assertEqual(result.steps[1].operation, "200 + 20 = 220")

    def test_plain_number_has_no_steps(self):
        self.assertEqual(calculate("42").steps, ())
        self.assertEqual(calculate("-5").steps, ())
        self.assertEqual(calculate("(5)").steps, ())

    def test_negative_operands_use_parentheses(self):
        result = calculate("3 × (0 − 4)")
        self.assertEqual(result.steps[-1].operation, "3 × (-4) = -12")

    def test_step_numbers_are_consecutive(self):
        steps = calculate("1 + 2 + 3 + 4 × 5").steps
        self.assertEqual([s.index for s in steps], list(range(1, len(steps) + 1)))


class ProgrammerMode(unittest.TestCase):
    def test_bitwise(self):
        self.assertEqual(calculate("FF AND 0F", prog(16)).text, "F")
        self.assertEqual(calculate("1010 OR 0101", prog(2)).text, "1111")
        self.assertEqual(calculate("6 XOR 3", prog()).text, "5")
        self.assertEqual(calculate("1 << 4", prog()).text, "16")
        self.assertEqual(calculate("256 >> 4", prog()).text, "16")
        self.assertEqual(calculate("NOT 0", prog(16)).text, "FFFFFFFFFFFFFFFF")
        self.assertEqual(calculate("NOT 0", prog()).text, "-1")
        self.assertEqual(calculate("6 NAND 3", prog()).text, "-3")

    def test_integer_division_truncates_toward_zero(self):
        self.assertEqual(calculate("7 ÷ 2", prog()).text, "3")
        self.assertEqual(calculate("-7 ÷ 2", prog()).text, "-3")

    def test_word_size_wraps_around(self):
        self.assertEqual(calculate("127 + 1", prog(10, 8)).text, "-128")
        self.assertEqual(calculate("7F + 1", prog(16, 8)).text, "80")
        self.assertEqual(calculate("FFFFFFFF + 1", prog(16, 32)).text, "0")

    def test_errors(self):
        with self.assertRaises(CalcError):
            calculate("1.5 + 1", prog())
        with self.assertRaises(CalcError):
            calculate("19", prog(8))        # el 9 no existe en octal
        with self.assertRaises(CalcError):
            calculate("5 ÷ 0", prog())

    def test_steps_use_the_active_base(self):
        step = calculate("A + 1", prog(16)).steps[0]
        self.assertEqual(step.operation, "A + 1 = B")


class Formatting(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(format_decimal(0.30000000000000004), "0.3")
        self.assertEqual(format_decimal(5.0), "5")
        self.assertEqual(format_decimal(-0.0), "0")
        self.assertEqual(wrap_signed(128, 8), -128)
        self.assertEqual(to_base(-1, 16, 16), "FFFF")
        self.assertEqual(to_base(10, 2, 8), "1010")
        views = all_bases(255, 64)
        self.assertEqual((views["HEX"], views["DEC"], views["BIN"]), ("FF", "255", "1111 1111"))


if __name__ == "__main__":
    unittest.main()
