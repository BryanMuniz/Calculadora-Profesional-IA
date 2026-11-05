# core/ — el cerebro matemático

**Responsabilidad:** convertir un texto como `"2 + 3 × 4"` en un resultado **y** en la lista de pasos para llegar a él.
**No sabe nada** de ventanas, botones, historial ni memoria. Solo recibe texto y un `EvalContext`.

```python
from calculadora.core import calculate, EvalContext, AngleMode

result = calculate("sin(30) + 2^3", EvalContext(angle_mode=AngleMode.DEG))
result.text        # "8.5"
result.steps       # (Step(1, "Seno", "sin(30) = 0.5", ...), ...)
```

## Pipeline

```
texto ─▶ tokenizer ─▶ parser ─▶ evaluator ─▶ EvaluationResult
          (tokens)     (AST)     (valor + pasos)
```

| Archivo | Responsabilidad |
|---|---|
| `engine.py` | Fachada: `calculate(texto, ctx)` une todo el pipeline. **Es el único punto de entrada.** |
| `tokenizer.py` | Texto → lista de `Token`. Entiende `× ÷ − π √`, números hex en modo programador, etc. |
| `parser.py` | Tokens → árbol. Un método por nivel de prioridad (parser descendente recursivo). |
| `ast_nodes.py` | Las clases de nodo: `Number`, `Binary`, `Unary`, `Postfix`, `Function`, `Group`, `Constant`. |
| `evaluator.py` | Recorre el árbol resolviendo **una operación por vuelta** y registrando cada `Step`. |
| `operations.py` | Catálogo: qué hace cada operador y función (el único lugar con matemáticas). |
| `render.py` | Árbol (a medio resolver) → texto: `2 + 12 − 9`. |
| `formatting.py` | Números → texto; bases 2/8/10/16; complemento a dos. |
| `context.py` | `EvalContext`: ángulos, base, tamaño de palabra, modo entero. |
| `steps.py` | La dataclass `Step`. |
| `errors.py` | `CalcError` (y subclases): errores "normales" con mensaje legible. |

## Prioridad de operadores (de menor a mayor)

`OR NOR` < `XOR` < `AND NAND` < `<< >>` < `+ −` < `× ÷ mod` (y multiplicación implícita) < `− unario, NOT` < `^` < `! %`

Detalles: la potencia es asociativa a la derecha (`2^3^2 = 512`) y `-2^2 = -4`.
