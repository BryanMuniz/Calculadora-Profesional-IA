"""Servicios: datos que la calculadora recuerda (historial y memoria)."""
from .history import HistoryEntry, HistoryService
from .memory import MemoryService

__all__ = ["HistoryEntry", "HistoryService", "MemoryService"]
