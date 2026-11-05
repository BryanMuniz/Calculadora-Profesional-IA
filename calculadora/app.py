"""Raíz de composición: aquí se crean y se conectan las piezas (como el `index.js`)."""
from __future__ import annotations

from .controller import CalculatorController
from .services import HistoryService, MemoryService


def run() -> None:
    # Se importa aquí para poder usar el núcleo y los tests aunque no haya tkinter instalado.
    from .ui.app import CalculatorApp

    controller = CalculatorController(history=HistoryService(), memory=MemoryService())
    CalculatorApp(controller).mainloop()
