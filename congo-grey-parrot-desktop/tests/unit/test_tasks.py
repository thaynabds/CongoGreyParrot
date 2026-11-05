"""O TaskManager tem de entregar o resultado e o erro de volta à janela.

Antes da correção, o objeto de sinais e o worker só existiam como variáveis locais de start();
o Python podia coletá-los e o botão Transcrever terminava sem texto e sem erro.
"""
import gc
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from congo_grey_parrot.core.errors import AppError  # noqa: E402
from congo_grey_parrot.ui.tasks import TaskManager  # noqa: E402

app = QApplication.instance() or QApplication([])


def wait_for(box, seconds=10):
    end = time.time() + seconds
    while time.time() < end and not box:
        gc.collect()
        app.processEvents()
        time.sleep(0.01)


def slow(value):
    def job(progress, cancel):
        time.sleep(0.3)
        gc.collect()
        progress(50, "metade")
        return value
    return job


def test_result_reaches_the_window_even_after_garbage_collection():
    manager = TaskManager()
    got, errors = [], []
    manager.start("t1", slow(42), got.append, errors.append)
    gc.collect()
    wait_for(got)
    assert got == [42] and errors == []
    assert manager.items[0].state == "done"


def test_error_reaches_the_window():
    manager = TaskManager()
    got, errors = [], []

    def boom(progress, cancel):
        time.sleep(0.2)
        raise AppError("falhou de propósito")

    manager.start("t2", boom, got.append, errors.append)
    gc.collect()
    wait_for(errors)
    assert errors == ["falhou de propósito"] and got == []


def test_tasks_in_a_row_all_finish():
    manager = TaskManager()
    got = []
    for n in range(3):
        manager.start(f"t{n}", slow(n), got.append, lambda m: None)
    gc.collect()
    end = time.time() + 10
    while time.time() < end and len(got) < 3:
        gc.collect()
        app.processEvents()
        time.sleep(0.01)
    assert sorted(got) == [0, 1, 2]
