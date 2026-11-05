# ui/ — la interfaz gráfica (Tkinter)

**Responsabilidad:** dibujar el `CalculatorState` y enviar clics/teclas al controlador. **No contiene lógica de calculadora.**

| Archivo | Qué hace |
|---|---|
| `app.py` | `CalculatorApp`: ventana principal. Construye los widgets, se suscribe al controlador y dibuja cada nuevo estado en `_render`. |
| `theme.py` | Colores, tipografías y `ButtonStyle` de cada tipo de tecla. **Cambia aquí el aspecto de toda la app.** |
| `keypads.py` | Las teclas de cada modo como **datos** (`KeySpec`). No usa tkinter. |
| `bindings.py` | Teclado físico → comandos (`translate_key` es una función pura y testeable). |
| `widgets/` | Componentes reutilizables (ver abajo). |

## Widgets (`widgets/`)

| Widget | Para qué sirve |
|---|---|
| `FlatButton` | Botón plano con hover y clic (basado en `Label`, para verse igual en Windows, macOS y Linux). |
| `Keypad` | Cuadrícula de teclas generada desde una lista de `KeySpec`. |
| `Display` | Pantalla: vista previa, número grande (la letra se achica si el texto crece), memoria y modo. |
| `StepsPanel` | Panel "Paso a paso" (un `Text` de solo lectura con estilos por etiquetas). |
| `HistoryPanel` | Historial clicable. |
| `ProgrammerPanel` | Valor en HEX/DEC/OCT/BIN y tamaño de palabra. |
| `ToggleGroup` | Botones tipo pestaña (modos, ángulos, QWORD/DWORD…). |

## Ideas de Tkinter que conviene tener presentes

- `widget.pack()` y `widget.grid()` colocan elementos (como flexbox / CSS grid). No mezcles ambos dentro del mismo contenedor.
- `columnconfigure(col, weight=1)` hace que una columna se estire al redimensionar (como `flex: 1`).
- `widget.bind("<Button-1>", f)` es el `addEventListener("click", f)` de Tkinter.
- Los paneles "Paso a paso" e "Historial" están **apilados** en la misma celda; `tkraise()` trae uno al frente (pestañas).
- Evitamos nombres como `self._options` en clases que heredan de widgets: Tkinter ya usa algunos nombres privados internamente.
