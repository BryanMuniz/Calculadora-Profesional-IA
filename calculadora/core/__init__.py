"""Núcleo matemático: no sabe nada de ventanas ni de botones."""
from .context import AngleMode, EvalContext
from .engine import EvaluationResult, calculate
from .errors import CalcError, MathCalcError, SyntaxCalcError
from .steps import Step

__all__ = [
    "AngleMode", "EvalContext", "EvaluationResult", "calculate",
    "CalcError", "MathCalcError", "SyntaxCalcError", "Step",
]
