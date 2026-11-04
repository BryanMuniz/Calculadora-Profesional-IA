# controller/ — de "presioné un botón" a "cambió el estado"

**Responsabilidad:** toda la lógica de *entrada*: qué hace cada botón, cómo se edita la expresión y cuándo se calcula.
Conecta la interfaz con `core/` y `services/`, pero no dibuja nada.

## Flujo

```
UI ──dispatch("operator", "+")──▶ CalculatorController ──▶ notifica ──▶ UI.render(state)
```

| Archivo | Qué hace |
|---|---|
| `calculator_controller.py` | Tabla de comandos (`digit`, `operator`, `equals`, `mem_store`, `set_mode`...). Cada llamada a `dispatch` modifica el búfer/servicios y avisa a los suscriptores con un `CalculatorState` nuevo. |
| `expression_buffer.py` | El texto que se va escribiendo y sus reglas: reemplazar operador, borrar un token completo, envolver el último número (`√(…)`), `±`, `x²` encadenado, cerrar paréntesis... |
| `state.py` | `CalculatorState` (la "foto" inmutable que recibe la UI) y el enum `Mode`. |

## Comportamientos que imitan a Windows

- Un operador tras `=` continúa desde el resultado; un dígito tras `=` empieza una cuenta nueva.
- Dos operadores seguidos: el segundo **reemplaza** al primero.
- `=` cierra solo los paréntesis abiertos.
- `CE` borra el último número; `C` todo; `⌫` borra un token entero (un operador o `sin(`).
- Cambiar de base en modo programador **convierte** el valor que hay en pantalla.

## Cómo probarlo sin interfaz

```python
from calculadora.controller import CalculatorController
c = CalculatorController()
c.dispatch("digit", "2"); c.dispatch("operator", "+"); c.dispatch("digit", "3")
print(c.state.primary, c.state.secondary)   # "2 + 3"  "= 5"
```
