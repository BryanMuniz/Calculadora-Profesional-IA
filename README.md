# Calculadora paso a paso (Python + Tkinter)

Una calculadora inspirada en la de Windows que **no solo da el resultado: te enseña cómo se llega a él**.
Escribes `2 + 3 × 4 − (6 ÷ 2)^2` y el panel lateral resuelve la expresión una operación a la vez, en el
orden correcto de prioridad, mostrando cómo va quedando la cuenta.

```
 1  División          6 ÷ 2 = 3          Queda: 2 + 3 × 4 − (3) ^ 2
 2  Potencia          3 ^ 2 = 9          Queda: 2 + 3 × 4 − 9
 3  Multiplicación    3 × 4 = 12         Queda: 2 + 12 − 9
 4  Suma              2 + 12 = 14        Queda: 14 − 9
 5  Resta             14 − 9 = 5         Queda: 5
```

## Características

| Modo | Qué incluye |
|---|---|
| **Estándar** | + − × ÷, `%` (como Windows: `200 + 10%` = 220), `√x`, `x²`, `1/x`, `±`, CE, C, ⌫, memoria (MC MR M+ M− MS) |
| **Científica** | Todo lo anterior + paréntesis, `π`, `e`, sin/cos/tan, sus inversas e hiperbólicas, log, ln, `xʸ`, `10ˣ`, `eˣ`, `n!`, `\|x\|`, `∛x`, `mod`, y ángulos en **DEG / RAD / GRAD** |
| **Programador** | Bases **HEX / DEC / OCT / BIN** (con el valor en las 4 a la vez), tamaño de palabra **QWORD / DWORD / WORD / BYTE**, AND OR XOR NOT NAND NOR, `<<` `>>`, `mod`, números con signo en complemento a dos |

Además: **vista previa en vivo** del resultado mientras escribes, **historial** (clic para recuperar un cálculo y ver sus pasos),
cierre automático de paréntesis, soporte completo de **teclado** y cero dependencias externas.

## Cómo ejecutarla

Necesitas **Python 3.9 o superior**. Tkinter viene incluido en Python para Windows y macOS.

```bash
python main.py            # o también:  python -m calculadora
```

> **Linux:** si aparece `No module named 'tkinter'`, instálalo con
> `sudo apt install python3-tk` (Debian/Ubuntu) o `sudo dnf install python3-tkinter` (Fedora).
>
> **Tipografías:** el tema usa *Segoe UI* y *Consolas*. Si tu sistema no las tiene, Tk usa otra automáticamente;
> puedes cambiarlas en `calculadora/ui/theme.py`.

##  Atajos de teclado

| Tecla | Acción | Tecla | Acción |
|---|---|---|---|
| `0-9` `.` | Dígitos y punto decimal | `Enter` / `=` | Calcular |
| `+ - * /` `^` | Operadores | `Backspace` | Borrar un token |
| `( )` | Paréntesis | `Delete` | CE (borra el último número) |
| `%` `!` | Porcentaje, factorial | `Esc` | C (borra todo) |
| `P` / `E` | π / e (modo Científica) | `Ctrl+C` | Copia el resultado |
| `A-F` | Dígitos hex (Programador en HEX) | `&` `\|` | AND / OR (Programador) |

## Estructura del proyecto

```
calculadora_paso_a_paso/
├── main.py                       ← punto de entrada
├── README.md                     ← este archivo
├── calculadora/
│   ├── app.py                    ← "raíz de composición": crea y conecta las piezas
│   ├── core/                     ← MATEMÁTICAS (sin ventanas)       → ver core/README.md
│   │   ├── tokenizer.py          │  texto  → tokens
│   │   ├── parser.py             │  tokens → árbol (AST) con prioridades
│   │   ├── evaluator.py          │  árbol  → valor + pasos
│   │   ├── operations.py         │  catálogo de operaciones y funciones
│   │   ├── formatting.py         │  números → texto (y bases 2/8/10/16)
│   │   ├── render.py             │  árbol  → texto ("2 + 12 − 9")
│   │   ├── engine.py             │  fachada: calculate(texto, contexto)
│   │   └── ast_nodes.py, steps.py, context.py, errors.py
│   ├── services/                 ←  DATOS QUE SE RECUERDAN             → ver services/README.md
│   │   ├── history.py            │  historial de cálculos
│   │   └── memory.py             │  memoria MC/MR/M+/M−/MS
│   ├── controller/               ←  LÓGICA DE ENTRADA                 → ver controller/README.md
│   │   ├── calculator_controller.py   botones → cambios de estado
│   │   ├── expression_buffer.py       reglas de edición del texto
│   │   └── state.py                   la "foto" del estado para la UI
│   └── ui/                       ←  INTERFAZ TKINTER                  → ver ui/README.md
│       ├── app.py                │  ventana principal
│       ├── theme.py              │  colores, fuentes, estilos
│       ├── keypads.py            │  distribución de teclas por modo (datos)
│       ├── bindings.py           │  teclado físico → comandos
│       └── widgets/              │  componentes reutilizables
└── tests/                        ←  77 pruebas automáticas
```

## Arquitectura: separación de responsabilidades

```
        ┌────────────────────────── ui/ (Tkinter) ──────────────────────────┐
        │  clic / tecla                                  dibuja el state    │
        └─────┬───────────────────────────────────────────────▲─────────────┘
              │ dispatch("operator", "+")                     │ render(state)
        ┌─────▼───────────────────────────────────────────────┴─────────────┐
        │                     controller/  (CalculatorController)           │
        │        edita el búfer ── pide cálculos ── guarda historial        │
        └─────┬───────────────────────────────┬─────────────────────────────┘
              │ calculate(texto, ctx)         │ add / store / recall
        ┌─────▼────────────┐            ┌─────▼──────────┐
        │  core/ (mates)   │            │  services/     │
        └──────────────────┘            └────────────────┘
```

**Regla:** cada capa solo conoce a la que tiene debajo. `core/` no sabe que existe una ventana;
`ui/` no hace ni una suma. Por eso la lógica se prueba sin abrir ninguna pantalla.

## ¿Cómo funciona el "paso a paso"?

1. **Tokenizer** — convierte el texto en piezas: `2 + 3 × 4` → `[2] [+] [3] [×] [4]`.
2. **Parser** — arma un árbol que respeta la prioridad de operadores. Lo más fuerte queda más abajo:
   ```
          (+)
         /   \
       [2]   (×)
            /   \
          [3]   [4]
   ```
3. **Evaluator** — resuelve **una operación por vuelta**. Elige primero lo que está dentro de paréntesis,
   luego el operador más fuerte (`^` → `× ÷` → `+ −`) y, a igualdad, lo más a la izquierda.
   Cada operación se guarda como un `Step` (operación, cómo queda la expresión y una pista del *porqué*).
4. **UI** — el panel lateral solo dibuja esa lista de pasos.

## Guía rápida si vienes del desarrollo web

| Mundo web | En este proyecto |
|---|---|
| Backend / lógica de negocio | `core/` |
| Base de datos / repositorios | `services/` |
| Store (Redux) / controlador | `controller/` — `dispatch(comando)` y `subscribe(listener)` |
| `state` de React | `CalculatorState` (inmutable; la UI solo lo dibuja) |
| Componentes (`<Button/>`, `<Display/>`) | clases de `ui/widgets/` |
| Variables CSS / design tokens | `ui/theme.py` |
| `index.js` / composition root | `main.py` + `calculadora/app.py` |
| `addEventListener` | `widget.bind("<Evento>", función)` |
| `display: grid` / flexbox | `.grid()` / `.pack()` |
| Cambiar de ruta / pestaña | `tkraise()` sobre frames apilados |
| Event loop del navegador | `mainloop()` |
| Jest / Vitest | `unittest` (`python -m unittest`) |
| Un lexer + parser (como el de JS/JSON) | `tokenizer.py` + `parser.py` |

Diferencia importante: en Tkinter **no hay DOM ni CSS**: cada widget se crea con código y se coloca con
`pack` o `grid`. Por eso la apariencia está centralizada en `theme.py` y las teclas se describen como datos en `keypads.py`.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Cubren el núcleo (prioridades, errores, modo programador, pasos), el búfer de edición, el controlador
(secuencias de botones completas), los servicios, el teclado y una prueba de humo de la interfaz con un
Tkinter simulado (`tests/fake_tk.py`), que pulsa **todas** las teclas de los tres modos.

##  Cómo extender

| Quiero… | Qué edito |
|---|---|
| Una **función nueva** (ej. `cot`) | Una línea en `FUNCTIONS` de `core/operations.py` + un botón en `ui/keypads.py` |
| Un **operador nuevo** | Entrada en `BINARY` (`operations.py`), nivel en `parser.py` y rango en `evaluator.py` |
| Un **botón nuevo** | Una `KeySpec` en `ui/keypads.py` (y un comando en `CalculatorController` si hace algo nuevo) |
| Cambiar **colores o tipografías** | `ui/theme.py` |
| Un **modo nuevo** (ej. conversor) | Valor en `Mode`, layout en `LAYOUTS` y lo que haga falta en el controlador |

## Notas y límites

- Los números decimales usan `float` de Python, mostrados con **15 cifras significativas** (`0.1 + 0.2` → `0.3`).
  Windows usa más precisión interna; si necesitas exactitud absoluta, el cambio estaría confinado en `operations.py`.
- `=` con un operador colgando (`5 +`) ignora ese operador (no repite el operando como hace Windows).
- `±` envuelve el último número así: `5` → `(−5)`; al pulsarlo de nuevo vuelve a `5`.
- Los resultados que cambian de modo conservan su contexto: al recuperar un cálculo del historial se restaura el modo, la base y los ángulos con los que se hizo.
