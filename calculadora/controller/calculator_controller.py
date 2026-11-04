"""El controlador: traduce "se presionó un botón" en "cambió el estado".

Flujo completo (parecido a Flux/Redux):

    Botón o tecla ──dispatch(comando, argumento)──▶ Controller
        │                                              │ modifica búfer / servicios
        │                                              ▼
        └──────────── render(state) ◀──── notifica a los suscriptores

La interfaz solo hace dos cosas: llamar a `dispatch(...)` y dibujar el `state`
que recibe. Nada de lógica de calculadora vive en los widgets.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Union

from ..core import AngleMode, CalcError, EvalContext, EvaluationResult, calculate
from ..core.formatting import NumberFormatter, all_bases
from ..services import HistoryEntry, HistoryService, MemoryService
from .expression_buffer import ExpressionBuffer
from .state import CalculatorState, Mode

Number = Union[int, float]
Listener = Callable[[CalculatorState], None]


class CalculatorController:
    def __init__(self, history: Optional[HistoryService] = None,
                 memory: Optional[MemoryService] = None) -> None:
        self._history = history if history is not None else HistoryService()
        self._memory = memory if memory is not None else MemoryService()
        self._buffer = ExpressionBuffer()
        self._mode = Mode.STANDARD
        self._angle = AngleMode.DEG
        self._base = 10
        self._word_bits = 64
        self._evaluated = False          # ¿acabamos de presionar "="?
        self._error: Optional[str] = None
        self._listeners: List[Listener] = []

        # Tabla de comandos: nombre → método. (Como un "router" de eventos.)
        self._handlers: Dict[str, Callable[[str], None]] = {
            "digit": self._digit, "decimal": self._decimal, "operator": self._operator,
            "prefix": self._prefix, "constant": self._constant, "function": self._function,
            "open_paren": self._open_paren, "close_paren": self._close_paren,
            "postfix": self._postfix, "sqrt": self._sqrt, "cbrt": self._cbrt,
            "abs": self._abs, "reciprocal": self._reciprocal, "negate": self._negate,
            "power10": self._power10, "equals": self._equals, "clear": self._clear,
            "clear_entry": self._clear_entry, "backspace": self._backspace,
            "mem_clear": self._mem_clear, "mem_recall": self._mem_recall,
            "mem_add": self._mem_add, "mem_sub": self._mem_sub, "mem_store": self._mem_store,
            "set_mode": self._set_mode, "set_angle": self._set_angle,
            "set_base": self._set_base, "set_word": self._set_word,
            "history_recall": self._history_recall, "history_clear": self._history_clear,
        }

    # ═══════════════════ API pública ═══════════════════
    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def dispatch(self, command: str, arg: str = "") -> None:
        handler = self._handlers.get(command)
        if handler is None:
            raise KeyError(f"Comando desconocido: {command}")
        self._error = None
        handler(arg)
        self._notify()

    @property
    def state(self) -> CalculatorState:
        return self._snapshot()

    @property
    def context(self) -> EvalContext:
        return EvalContext(
            angle_mode=self._angle,
            base=self._base if self._mode is Mode.PROGRAMMER else 10,
            word_bits=self._word_bits,
            integer_mode=self._mode is Mode.PROGRAMMER,
        )

    # ═══════════════════ estado ═══════════════════
    def _notify(self) -> None:
        state = self._snapshot()
        for listener in self._listeners:
            listener(state)

    def _preview(self) -> Optional[EvaluationResult]:
        """Calcula el búfer "en silencio": si es inválido devuelve None."""
        text = self._buffer.for_evaluation()
        if not text:
            return None
        try:
            return calculate(text, self.context)
        except CalcError:
            return None

    def _snapshot(self) -> CalculatorState:
        ctx = self.context
        fmt = NumberFormatter(ctx)
        preview = self._preview()

        if self._error:
            primary, secondary = self._error, self._buffer.text
        elif self._evaluated and preview:
            primary, secondary = preview.text, f"{self._buffer.text} ="
        else:
            primary = self._buffer.text or "0"
            secondary = f"= {preview.text}" if preview and preview.steps else ""

        value = preview.value if preview else 0
        base_views = all_bases(int(value), ctx.word_bits) if self._mode is Mode.PROGRAMMER else {}
        memory = self._memory.value

        return CalculatorState(
            mode=self._mode, primary=primary, secondary=secondary, is_error=bool(self._error),
            expression=self._buffer.text,
            steps=preview.steps if preview else (),
            steps_expression=preview.expression if preview else "",
            steps_result=preview.text if preview else "",
            history=self._history.all(),
            memory_text=fmt.format(memory) if memory is not None else "",
            angle_mode=self._angle, base=self._base, word_bits=self._word_bits,
            base_views=base_views,
        )

    # ═══════════════════ ayudas internas ═══════════════════
    @staticmethod
    def _as_operand_text(text: str) -> str:
        return f"({text})" if text.startswith("-") else text

    def _start_operand(self) -> None:
        """Se va a escribir un operando nuevo: si venimos de "=", se empieza de cero."""
        if self._evaluated:
            self._buffer.clear()
            self._evaluated = False

    def _continue_from_result(self) -> None:
        """Se va a operar sobre el resultado anterior: se usa como punto de partida."""
        if self._evaluated:
            preview = self._preview()
            text = preview.text if preview else self._buffer.text
            self._buffer.set(self._as_operand_text(text))
            self._evaluated = False

    def _current_value(self) -> Optional[Number]:
        if self._buffer.is_empty:
            return 0
        preview = self._preview()
        if preview is None:
            self._error = "La expresión todavía no es válida"
            return None
        return preview.value

    # ═══════════════════ comandos de escritura ═══════════════════
    def _digit(self, digit: str) -> None:
        if int(digit, 16) >= self._base:
            return  # dígito inválido para la base actual (ej. "9" en octal)
        self._start_operand()
        self._buffer.add_digit(digit)

    def _decimal(self, _: str) -> None:
        if self._mode is Mode.PROGRAMMER:
            return
        self._start_operand()
        self._buffer.add_decimal_point()

    def _operator(self, symbol: str) -> None:
        self._continue_from_result()
        text = self._buffer.text
        if not text:
            if symbol == "−":
                self._buffer.append("−")      # signo negativo al inicio
            else:
                self._buffer.set("0")         # "+ 5" se interpreta como "0 + 5"
                self._buffer.add_operator(symbol)
        elif text.endswith("("):
            if symbol == "−":
                self._buffer.append("−")
        elif not text.endswith("−"):
            self._buffer.add_operator(symbol)

    def _prefix(self, symbol: str) -> None:       # NOT
        self._start_operand()
        self._buffer.append(f"{symbol} ")

    def _constant(self, symbol: str) -> None:
        self._start_operand()
        self._buffer.append(symbol)

    def _function(self, name: str) -> None:
        self._start_operand()
        self._buffer.add_function(name)

    def _open_paren(self, _: str) -> None:
        self._start_operand()
        self._buffer.add_open_paren()

    def _close_paren(self, _: str) -> None:
        if not self._evaluated:
            self._buffer.add_close_paren()

    def _postfix(self, suffix: str) -> None:       # !  %  ^2  ^3
        self._continue_from_result()
        if suffix.startswith("^"):
            self._buffer.add_power_suffix(suffix)
        elif self._buffer.last_operand_span():
            self._buffer.append(suffix)

    def _wrap(self, prefix: str, suffix: str, insert_if_empty: bool) -> None:
        self._continue_from_result()
        if not self._buffer.wrap_last_operand(prefix, suffix) and insert_if_empty:
            self._buffer.append(prefix)

    def _sqrt(self, _: str) -> None: self._wrap("√(", ")", True)
    def _cbrt(self, _: str) -> None: self._wrap("∛(", ")", True)
    def _abs(self, _: str) -> None: self._wrap("abs(", ")", True)
    def _reciprocal(self, _: str) -> None:
        self._continue_from_result()
        self._buffer.reciprocal_last_operand()

    def _negate(self, _: str) -> None:
        self._continue_from_result()
        self._buffer.negate_last_operand()

    def _power10(self, _: str) -> None:
        self._start_operand()
        self._buffer.append("10")
        self._buffer.add_operator("^")

    # ═══════════════════ borrar y calcular ═══════════════════
    def _equals(self, _: str) -> None:
        text = self._buffer.for_evaluation()
        if not text:
            return
        try:
            result = calculate(text, self.context)
        except CalcError as exc:
            self._error = exc.message
            return
        self._buffer.set(text)  # muestra la expresión con los paréntesis ya cerrados
        self._evaluated = True
        self._history.add(HistoryEntry(
            source_text=text, expression=result.expression, result=result.text,
            steps=result.steps, mode=self._mode.name, ctx=self.context,
        ))

    def _clear(self, _: str) -> None:
        self._buffer.clear()
        self._evaluated = False

    def _clear_entry(self, _: str) -> None:
        self._evaluated = False
        self._buffer.clear_entry()

    def _backspace(self, _: str) -> None:
        self._evaluated = False  # la expresión sigue en el búfer: se puede editar
        self._buffer.backspace()

    # ═══════════════════ memoria ═══════════════════
    def _mem_clear(self, _: str) -> None:
        self._memory.clear()

    def _mem_store(self, _: str) -> None:
        value = self._current_value()
        if value is not None:
            self._memory.store(value)

    def _mem_add(self, _: str) -> None:
        value = self._current_value()
        if value is not None:
            self._memory.add(value)

    def _mem_sub(self, _: str) -> None:
        value = self._current_value()
        if value is not None:
            self._memory.subtract(value)

    def _mem_recall(self, _: str) -> None:
        if not self._memory.has_value:
            return
        self._start_operand()
        text = NumberFormatter(self.context).format(self._memory.value)
        self._buffer.append(self._as_operand_text(text))

    # ═══════════════════ opciones ═══════════════════
    def _set_mode(self, name: str) -> None:
        new_mode = Mode[name]
        if new_mode is self._mode:
            return
        crossing_programmer = (new_mode is Mode.PROGRAMMER) != (self._mode is Mode.PROGRAMMER)
        self._mode = new_mode
        if crossing_programmer:  # el programador usa otro tipo de números: se empieza limpio
            self._buffer.clear()
            self._evaluated = False
            self._base = 10

    def _set_angle(self, name: str) -> None:
        self._angle = AngleMode[name]

    def _set_base(self, base: str) -> None:
        new_base = int(base)
        if new_base == self._base:
            return
        preview = self._preview()                  # valor actual, en la base anterior
        self._base = new_base
        if preview is None:
            self._buffer.clear()
        else:                                       # convierte lo que hay en pantalla
            self._buffer.set(NumberFormatter(self.context).format(preview.value))
        self._evaluated = False

    def _set_word(self, bits: str) -> None:
        self._word_bits = int(bits)

    # ═══════════════════ historial ═══════════════════
    def _history_recall(self, index: str) -> None:
        entry = self._history.get(int(index))
        self._mode = Mode[entry.mode]
        self._angle = entry.ctx.angle_mode
        self._word_bits = entry.ctx.word_bits
        self._base = entry.ctx.base
        self._buffer.set(entry.source_text)
        self._evaluated = True

    def _history_clear(self, _: str) -> None:
        self._history.clear()
