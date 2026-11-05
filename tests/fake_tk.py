"""Un "tkinter de mentira" para probar la interfaz SIN pantalla (ni tkinter instalado).

Registra qué texto se inserta en los `Text` y acepta cualquier llamada a un
método (pack, grid, bind, configure...). Así los tests detectan errores de
nombres, imports y flujos sin abrir una ventana de verdad.
"""
import sys
import types


class Widget:
    def __init__(self, parent=None, *args, **options):
        self.parent = parent
        self.options = dict(options)
        self.buffer = []          # texto insertado (solo lo usa Text)
        self.bound = {}

    def configure(self, **options):
        self.options.update(options)

    config = configure

    def cget(self, key):
        return self.options.get(key)

    def bind(self, sequence, func=None, add=None):
        self.bound[sequence] = func

    def tag_bind(self, tag, sequence, func=None, add=None):
        self.bound[(tag, sequence)] = func

    def winfo_width(self):
        return 100

    def winfo_height(self):
        return 40

    # Text
    def insert(self, index, text, *tags):
        self.buffer.append(text)

    def delete(self, *args):
        self.buffer.clear()

    def get_text(self):
        return "".join(self.buffer)

    def __getattr__(self, name):          # pack, grid, columnconfigure, tkraise, ...
        return lambda *a, **k: 0


class Tk(Widget):
    def mainloop(self):
        pass


class Font(Widget):
    pass


def install():
    tk = types.ModuleType("tkinter")
    for name in ("Frame", "Label", "Text", "Canvas", "Button", "Scrollbar", "Entry"):
        setattr(tk, name, type(name, (Widget,), {}))
    tk.Tk = Tk
    tk.Widget = Widget

    font = types.ModuleType("tkinter.font")
    font.Font = Font
    ttk = types.ModuleType("tkinter.ttk")
    ttk.Scrollbar = type("Scrollbar", (Widget,), {})

    tk.font, tk.ttk = font, ttk
    sys.modules.update({"tkinter": tk, "tkinter.font": font, "tkinter.ttk": ttk})
