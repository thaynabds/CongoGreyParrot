from __future__ import annotations

import threading
import uuid

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from congo_grey_parrot.core.errors import AppError


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int, str)


class Worker(QRunnable):
    def __init__(self, fn, signals: WorkerSignals, cancel: threading.Event):
        super().__init__()
        self.fn = fn
        self.signals = signals
        self.cancel = cancel

    def run(self) -> None:
        try:
            result = self.fn(self.signals.progress.emit, self.cancel)
            if self.cancel.is_set():
                self.signals.failed.emit("Operação cancelada.")
                return
            self.signals.finished.emit(result)
        except AppError as exc:
            self.signals.failed.emit(str(exc))
        except Exception as exc:
            self.signals.failed.emit(f"{type(exc).__name__}: {exc}")


class TaskItem:
    def __init__(self, title: str):
        self.id = uuid.uuid4().hex
        self.title = title
        self.progress = 0
        self.message = "Na fila"
        self.state = "running"
        self.cancel_event = threading.Event()


class TaskManager(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        self.items: list[TaskItem] = []
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(1)

    def start(self, title: str, fn, on_ok, on_err) -> TaskItem:
        item = TaskItem(title)
        signals = WorkerSignals()
        signals.progress.connect(lambda value, message, current=item: self._on_progress(current, value, message))
        signals.finished.connect(lambda result, current=item: self._on_ok(current, result, on_ok))
        signals.failed.connect(lambda message, current=item: self._on_err(current, message, on_err))
        self.items.insert(0, item)
        self.items = self.items[:40]
        self.updated.emit()
        self._pool.start(Worker(fn, signals, item.cancel_event))
        return item

    def cancel(self, task_id: str) -> None:
        for item in self.items:
            if item.id == task_id and item.state == "running":
                item.cancel_event.set()
                item.message = "Cancelamento pedido"
                self.updated.emit()

    def _on_progress(self, item: TaskItem, value: int, message: str) -> None:
        item.progress = max(0, min(100, int(value)))
        item.message = message
        self.updated.emit()

    def _on_ok(self, item: TaskItem, result, on_ok) -> None:
        item.state = "done"
        item.progress = 100
        item.message = "Concluído"
        self.updated.emit()
        on_ok(result)

    def _on_err(self, item: TaskItem, message: str, on_err) -> None:
        item.state = "canceled" if message == "Operação cancelada." else "error"
        item.message = message
        self.updated.emit()
        on_err(message)
