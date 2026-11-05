# services/ — lo que la calculadora recuerda

**Responsabilidad:** guardar datos entre cálculo y cálculo. Son clases de Python "puras":
no importan tkinter y no saben cómo se dibuja nada.

| Archivo | Qué hace |
|---|---|
| `history.py` | `HistoryService` guarda hasta 100 `HistoryEntry` (la más reciente primero). Cada entrada incluye el texto original, el resultado, los pasos y el contexto (modo, base, ángulos) para poder recuperarla fielmente. |
| `memory.py` | `MemoryService` implementa `MS` (guardar), `M+`, `M−`, `MR` (leer) y `MC` (borrar). |

> Equivalente web: la capa de repositorios / base de datos. Hoy viven en memoria; si quisieras guardarlos
> en disco (JSON), solo tendrías que cambiar estas dos clases.
