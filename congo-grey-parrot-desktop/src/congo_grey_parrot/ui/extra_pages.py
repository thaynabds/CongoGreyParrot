from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
        QPlainTextEdit,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
)

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.documents.service import read_document
from congo_grey_parrot.files.naming import suggest_name
from congo_grey_parrot.models.catalog import WHISPER_MODELS, installed_whisper_names
from congo_grey_parrot.ui.dialogs import MEDIA_FILTER, PLAIN_FILTER, ask_directory, ask_open, ask_save, confirm, info, warn
from congo_grey_parrot.ui.color_filter import FILTERS
from congo_grey_parrot.ui.theme import THEMES, apply_theme


def _header(layout: QVBoxLayout, title: str, hint: str) -> None:
    heading = QLabel(title)
    heading.setStyleSheet("font-weight: 700;")
    note = QLabel(hint)
    note.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(note)


class ConvertPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.source: Path | None = None
        layout = QVBoxLayout(self)
        _header(layout, "Converter mídia", "O arquivo original permanece. Você escolhe o nome e a pasta do resultado.")
        self.source_label = QLabel("Nenhum arquivo selecionado.")
        self.source_label.setWordWrap(True)
        pick = QPushButton("Escolher arquivo")
        pick.clicked.connect(self._pick)
        self.format = QComboBox()
        self.format.addItems(["wav", "mp3", "m4a", "ogg", "flac", "mp4", "mkv", "webm", "mov"])
        self.bitrate = QSpinBox()
        self.bitrate.setRange(0, 2000)
        self.bitrate.setSuffix(" kbps (0 = padrão do FFmpeg)")
        form = QFormLayout()
        form.addRow("Formato", self.format)
        form.addRow("Taxa", self.bitrate)
        run = QPushButton("Converter e salvar")
        run.setObjectName("primary")
        run.clicked.connect(self._run)
        layout.addWidget(self.source_label)
        layout.addWidget(pick)
        layout.addLayout(form)
        layout.addWidget(run)
        layout.addStretch(1)

    def _pick(self) -> None:
        path = ask_open(self, "Mídia (*.mp3 *.wav *.m4a *.aac *.ogg *.flac *.mp4 *.mkv *.mov *.webm *.avi)")
        if path:
            self.source = path
            self.source_label.setText(str(path))

    def _run(self) -> None:
        if self.source is None:
            warn(self, "Escolha um arquivo.")
            return
        suffix = "." + self.format.currentText()
        target = ask_save(
            self,
            str(self.session.output_dir() / suggest_name(self.source.name, suffix)),
            MEDIA_FILTER,
        )
        if target is None:
            return
        source = self.source
        bitrate = self.bitrate.value() or None

        def job(progress, cancel):
            progress(15, "Convertendo")
            if cancel.is_set():
                raise AppError("Operação cancelada.")
            saved = self.session.media.convert(source, target, bitrate)
            progress(100, "Convertido")
            return saved

        self.session.tasks.start("Converter", job, self._done, lambda message: warn(self, message))

    def _done(self, saved: Path) -> None:
        self.session.remember("conversão", self.source.name if self.source else "", saved)
        info(self, f"Arquivo salvo em {saved}")


class DocumentsPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.source_name = "documento"
        layout = QVBoxLayout(self)
        _header(layout, "Documentos", "Abra TXT, Markdown, DOCX ou PDF com texto selecionável. PDF de imagem não é lido.")
        self.editor = QPlainTextEdit()
        row = QHBoxLayout()
        open_button = QPushButton("Abrir")
        open_button.clicked.connect(self._open)
        save_button = QPushButton("Salvar")
        save_button.setObjectName("primary")
        save_button.clicked.connect(self._save)
        read_button = QPushButton("Ler em voz alta")
        read_button.clicked.connect(self._read)
        row.addWidget(open_button)
        row.addWidget(save_button)
        row.addWidget(read_button)
        layout.addWidget(self.editor, 1)
        layout.addLayout(row)

    def _open(self) -> None:
        path = ask_open(self, "Documento (*.txt *.md *.docx *.pdf)")
        if path is None:
            return
        try:
            self.editor.setPlainText(read_document(path))
        except AppError as exc:
            warn(self, str(exc))
            return
        self.source_name = path.name

    def _save(self) -> None:
        path = ask_save(self, str(self.session.output_dir() / suggest_name(self.source_name, ".txt")), PLAIN_FILTER)
        if path is None:
            return
        try:
            saved = self.session.exporter.export_text(path, self.editor.toPlainText(), self.source_name)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("documento", self.source_name, saved)

    def _read(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            warn(self, "Não há texto para ler.")
            return
        self.session.bus.open_speech_text.emit(text)


class LibraryPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        layout = QVBoxLayout(self)
        _header(layout, "Biblioteca", "Arquivos da pasta de saída. Salvar cópia grava o arquivo em outro lugar.")
        self.list = QListWidget()
        row = QHBoxLayout()
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)
        copy = QPushButton("Salvar cópia")
        copy.clicked.connect(self._copy)
        folder = QPushButton("Abrir pasta")
        folder.clicked.connect(self._open_folder)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete)
        for button in (refresh, copy, folder, delete):
            row.addWidget(button)
        layout.addWidget(self.list, 1)
        layout.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        folder = self.session.output_dir()
        files = [path for path in folder.iterdir() if path.is_file()]
        for path in sorted(files, key=lambda item: item.stat().st_mtime, reverse=True):
            self.list.addItem(str(path))

    def _current(self) -> Path | None:
        item = self.list.currentItem()
        if item is None:
            return None
        return Path(item.text())

    def _copy(self) -> None:
        source = self._current()
        if source is None:
            warn(self, "Selecione um arquivo.")
            return
        target = ask_save(self, str(source), "Arquivo (*)")
        if target is None:
            return
        try:
            saved = self.session.exporter.copy_file(source, target)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("cópia", source.name, saved)

    def _open_folder(self) -> None:
        path = self.session.output_dir()
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
            return
        command = ["xdg-open", str(path)] if sys.platform != "darwin" else ["open", str(path)]
        subprocess.run(command, check=False)

    def _delete(self) -> None:
        source = self._current()
        if source is None:
            return
        if not confirm(self, f"Excluir {source.name}?"):
            return
        source.unlink(missing_ok=True)
        self.refresh()


class ModelsPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        layout = QVBoxLayout(self)
        _header(
            layout,
            "Modelos e vozes",
            "Nada grande é baixado sem confirmação. Antes do download, você escolhe a pasta. A licença de cada voz está no MODEL_CARD da pasta rhasspy/piper-voices.",
        )
        self.whisper = QListWidget()
        self.voices = QListWidget()
        self.installed = QListWidget()
        download = QPushButton("Baixar modelo de transcrição")
        download.clicked.connect(self._download_model)
        voice_button = QPushButton("Baixar voz selecionada")
        voice_button.clicked.connect(self._download_voice)
        use_voice = QPushButton("Usar voz instalada")
        use_voice.clicked.connect(self._use_voice)
        remove = QPushButton("Remover voz")
        remove.clicked.connect(self._remove_voice)
        clear_models = QPushButton("Apagar cache de transcrição")
        clear_models.clicked.connect(self._clear_models)
        layout.addWidget(QLabel("Modelos Whisper"))
        layout.addWidget(self.whisper, 1)
        layout.addWidget(download)
        layout.addWidget(QLabel("Catálogo de vozes"))
        layout.addWidget(self.voices, 1)
        layout.addWidget(voice_button)
        layout.addWidget(QLabel("Vozes neste computador"))
        layout.addWidget(self.installed, 1)
        row = QHBoxLayout()
        row.addWidget(use_voice)
        row.addWidget(remove)
        row.addWidget(clear_models)
        layout.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        present = set()
        for root in self.session.models.whisper_roots():
            present.update(installed_whisper_names(root))
        self.whisper.clear()
        for model in WHISPER_MODELS:
            state = "instalado" if model.name in present else "não instalado"
            translate = "traduz para inglês" if model.translates_to_english else "não traduz"
            self.whisper.addItem(f"{model.name} | {model.profile} | {translate} | {state} | {model.note}")
            self.whisper.item(self.whisper.count() - 1).setData(Qt.ItemDataRole.UserRole, model.name)
        self.voices.clear()
        for entry in self.session.models.catalog():
            self.voices.addItem(f"{entry.language_label} | {entry.name} | {entry.quality} | {entry.id}")
            self.voices.item(self.voices.count() - 1).setData(Qt.ItemDataRole.UserRole, entry.id)
        self.installed.clear()
        for voice in self.session.models.installed():
            self.installed.addItem(voice.voice_id)
            self.installed.item(self.installed.count() - 1).setData(Qt.ItemDataRole.UserRole, str(voice.folder))

    def _download_model(self) -> None:
        item = self.whisper.currentItem()
        if item is None:
            warn(self, "Selecione um modelo.")
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        folder = ask_directory(self, str(self.session.models.whisper_root))
        if folder is None:
            return
        if not confirm(self, f"Baixar o modelo {name} em {folder}?"):
            return
        self.session.remember_place("whisper_places", folder)
        self.session.transcription.model_dir = folder
        device = "cpu"

        def job(progress, cancel):
            self.session.transcription.preload(name, device, progress, cancel)
            return name

        self.session.tasks.start(
            f"Modelo {name}",
            job,
            lambda _name: self._model_done(name),
            lambda message: warn(self, message),
        )

    def _model_done(self, name: str) -> None:
        self.session.db.set_setting("whisper_model", name)
        self.refresh()
        info(self, f"Modelo {name} pronto para uso offline, na pasta que você escolheu.")

    def _download_voice(self) -> None:
        item = self.voices.currentItem()
        if item is None:
            warn(self, "Selecione uma voz.")
            return
        voice_id = item.data(Qt.ItemDataRole.UserRole)
        entry = next(entry for entry in self.session.models.catalog() if entry.id == voice_id)
        folder = ask_directory(self, str(self.session.models.voice_root))
        if folder is None:
            return
        if not confirm(self, f"Baixar a voz {entry.id} em {folder}?"):
            return
        self.session.remember_place("voice_places", folder)

        def job(progress, cancel):
            return self.session.models.download_voice(entry, progress, cancel, destination=folder)

        self.session.tasks.start(
            f"Voz {voice_id}",
            job,
            self._voice_done,
            lambda message: warn(self, message),
        )

    def _voice_done(self, folder) -> None:
        voice_id = Path(folder).name
        self.session.db.set_setting("piper_voice", str(Path(folder) / f"{voice_id}.onnx"))
        self.refresh()
        info(self, "Voz instalada. Abra Texto para voz e atualize a lista.")

    def _use_voice(self) -> None:
        item = self.installed.currentItem()
        if item is None:
            warn(self, "Selecione uma voz instalada.")
            return
        voice_id = item.text()
        folder = Path(item.data(Qt.ItemDataRole.UserRole))
        model = folder / f"{voice_id}.onnx"
        self.session.db.set_setting("piper_voice", str(model))
        info(self, "Esta voz será a preferida em Texto para voz.")

    def _remove_voice(self) -> None:
        item = self.installed.currentItem()
        if item is None:
            return
        if not confirm(self, f"Remover a voz {item.text()}?"):
            return
        try:
            self.session.models.remove_voice(Path(item.data(Qt.ItemDataRole.UserRole)))
        except AppError as exc:
            warn(self, str(exc))
            return
        self.refresh()

    def _clear_models(self) -> None:
        if not confirm(self, "Apagar os modelos de transcrição já baixados?"):
            return
        self.session.transcription.unload()
        self.session.models.clear_whisper_cache()
        self.refresh()


class HistoryPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        layout = QVBoxLayout(self)
        _header(layout, "Histórico", "Registro local das exportações. Limpar não apaga os arquivos.")
        self.list = QListWidget()
        clear = QPushButton("Limpar histórico")
        clear.clicked.connect(self._clear)
        layout.addWidget(self.list, 1)
        layout.addWidget(clear)
        session.bus.history_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for row in self.session.db.list_history():
            self.list.addItem(
                f"{row['created_at']} | {row['kind']} | {row['source_name']} | {row['output_path']}"
            )

    def _clear(self) -> None:
        if confirm(self, "Limpar o histórico local?"):
            self.session.db.clear_history()
            self.refresh()


class SettingsPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        inner = QWidget()
        layout = QVBoxLayout(inner)
        _header(layout, "Configurações", "Tema, filtro de cor, tamanho da letra e pasta padrão dos arquivos salvos.")
        theme_box = QWidget()
        theme_layout = QVBoxLayout(theme_box)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_options = (
            ("light", "Claro"),
            ("dark", "Escuro"),
            ("high_contrast", "Alto contraste"),
            ("kuro", "Kuro"),
            ("pink_void", "PinkVoid"),
            ("red_void", "RedVoid"),
            ("yellow_void", "YellowVoid"),
        )
        themes = QButtonGroup(self)
        themes.setExclusive(True)
        current = session.db.get_setting("theme", "light")
        chosen = None
        fallback = None
        for mode, label in theme_options:
            button = QRadioButton(label)
            button.setAutoExclusive(False)
            themes.addButton(button)
            button.toggled.connect(lambda checked, name=mode: self._theme(checked, name))
            theme_layout.addWidget(button)
            if mode == "light":
                fallback = button
            if mode == current:
                chosen = button
        (chosen or fallback).setChecked(True)
        layout.addWidget(theme_box)
        layout.addWidget(QLabel("Filtro de cor"))
        filter_box = QWidget()
        filter_layout = QVBoxLayout(filter_box)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filters = QButtonGroup(self)
        filters.setExclusive(True)
        labels = (
            ("none", "Nenhum"),
            ("invert", "Inversão clássica"),
            ("smart_invert", "Inversão inteligente"),
            ("protanopia", "Protanopia"),
            ("deuteranopia", "Deuteranopia"),
            ("tritanopia", "Tritanopia"),
            ("grayscale", "Monocromia"),
        )
        stored_filter = session.db.get_setting("color_filter", "none") or "none"
        if stored_filter not in FILTERS:
            stored_filter = "none"
        for key, label in labels:
            button = QRadioButton(label)
            button.setAutoExclusive(False)
            filters.addButton(button)
            button.toggled.connect(lambda checked, name=key: self._filter(checked, name))
            filter_layout.addWidget(button)
            if key == stored_filter:
                button.setChecked(True)
        layout.addWidget(filter_box)
        note = QLabel(
            "A inversão inteligente troca as cores da interface e mantém fotos e vídeo. "
            "A inversão clássica, a monocromia e os filtros de protanopia, deuteranopia e tritanopia alteram a tela toda. "
            "Correção de daltonismo: Daltonizer do Android. "
            "Monocromia: Rec. ITU-R BT.709."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.scale = QSlider(Qt.Orientation.Horizontal)
        self.scale.setRange(90, 160)
        stored = float(session.db.get_setting("font_scale", "1") or "1")
        self.scale.setValue(int(stored * 100))
        self.scale.valueChanged.connect(self._scale)
        self.folder = QLabel(str(session.output_dir()))
        self.folder.setWordWrap(True)
        choose = QPushButton("Escolher pasta de saída")
        choose.clicked.connect(self._folder)
        about = QLabel(
            "Project Congo Grey Parrot. Transcrição com faster-whisper, compatível com as tarefas do Whisper. "
            "Leitura com Piper ou espeak-ng. Conversão com FFmpeg. "
            "Whisper: https://github.com/openai/whisper. "
            "Piper: https://github.com/OHF-Voice/piper1-gpl. "
            "Parolu, referência de leitura local: https://github.com/wbernard/parolu."
        )
        about.setWordWrap(True)
        layout.addWidget(QLabel("Tamanho da letra"))
        layout.addWidget(self.scale)
        layout.addWidget(self.folder)
        layout.addWidget(choose)
        layout.addWidget(about)
        layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.addWidget(scroll)

    def _theme(self, checked: bool, mode: str) -> None:
        if not checked or mode not in THEMES:
            return
        self.session.db.set_setting("theme", mode)
        self._apply()

    def _filter(self, checked: bool, name: str) -> None:
        if not checked or name not in FILTERS:
            return
        self.session.db.set_setting("color_filter", name)
        self._apply()

    def _scale(self, value: int) -> None:
        self.session.db.set_setting("font_scale", str(value / 100))
        self._apply()

    def _apply(self) -> None:
        from PySide6.QtWidgets import QApplication, QMainWindow

        mode = self.session.db.get_setting("theme", "light") or "light"
        scale = float(self.session.db.get_setting("font_scale", "1") or "1")
        color_filter = self.session.db.get_setting("color_filter", "none") or "none"
        host = self.window()
        root = host.centralWidget() if isinstance(host, QMainWindow) else None
        apply_theme(QApplication.instance(), mode, scale, color_filter, root)
        self.session.bus.theme_changed.emit(mode)

    def _folder(self) -> None:
        path = ask_directory(self, str(self.session.output_dir()))
        if path is None:
            return
        self.session.db.set_setting("output_dir", str(path))
        self.folder.setText(str(self.session.output_dir()))
