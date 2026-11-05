"""Fachada del núcleo: UNA función que une tokenizer → parser → evaluator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from .context import EvalContext
from .evaluator import Evaluator
from .formatting import NumberFormatter
from .parser import Parser
from .render import render
from .steps import Step
from .tokenizer import tokenize


@dataclass(frozen=True)
class EvaluationResult:
    value: Union[int, float]   # el valor numérico
    text: str                  # el valor ya formateado ("14", "FF", "0.3"...)
    expression: str            # la expresión normalizada ("2 + 3 × 4")
    steps: Tuple[Step, ...]    # pasos de la resolución


def calculate(text: str, ctx: Optional[EvalContext] = None) -> EvaluationResult:
    """Calcula `text`. Lanza `CalcError` si no es válido."""
    ctx = ctx or EvalContext()
    tokens = tokenize(text, ctx)
    tree = Parser(tokens).parse()
    evaluator = Evaluator(tree, ctx)
    value = evaluator.run()
    fmt = NumberFormatter(ctx)
    return EvaluationResult(value, fmt.format(value), render(tree, {}, fmt), tuple(evaluator.steps))
