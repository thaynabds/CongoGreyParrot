from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.files.naming import suggest_name
from congo_grey_parrot.models.catalog import installed_whisper_names
from congo_grey_parrot.speech.service import clamp_pitch, clamp_speed
from congo_grey_parrot.subtitles.codec import CaptionOptions
from congo_grey_parrot.transcription.languages import LANGUAGES
from congo_grey_parrot.transcription.options import TranscribeOptions
from congo_grey_parrot.ui.dialogs import (
    AUDIO_FILTER,
    PLAIN_FILTER,
    TEXT_FILTER,
    ask_open,
    ask_save,
    confirm,
    info,
    warn,
)
from congo_grey_parrot.ui.widgets import DropFrame, PlayerBar


def _header(layout: QVBoxLayout, title: str, hint: str) -> None:
    heading = QLabel(title)
    heading.setStyleSheet("font-weight: 700;")
    note = QLabel(hint)
    note.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(note)


class HomePage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        layout = QVBoxLayout(self)
        _header(
            layout,
            "Início",
            "Importe um arquivo ou escolha uma ferramenta. O resultado pode ser salvo na pasta que você escolher.",
        )
        self.drop = DropFrame("Arraste áudio, vídeo, texto ou legenda para esta área.")
        self.drop.files_dropped.connect(lambda paths: session.bus.import_files.emit(paths))
        layout.addWidget(self.drop)
        row = QHBoxLayout()
        for label, page in (
            ("Transcrever", "transcribe"),
            ("Ler em voz alta", "speech"),
            ("Traduzir", "translate"),
            ("Legendas", "subtitles"),
            ("Converter", "convert"),
            ("Documentos", "documents"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, name=page: session.bus.open_page.emit(name))
            row.addWidget(button)
        layout.addLayout(row)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        lines = ["Componentes neste computador:"]
        lines.append(self._line("Transcrição faster-whisper", bool(self.session.transcription.engine_name())))
        lines.append(self._line("Biblioteca Piper", "piper" in self.session.speech.available_engines()))
        lines.append(self._line("espeak-ng", "espeak-ng" in self.session.speech.available_engines()))
        from congo_grey_parrot.media.ffmpeg_service import find_ffmpeg

        lines.append(self._line("FFmpeg", find_ffmpeg() is not None))
        self.status.setText("\n".join(lines))

    @staticmethod
    def _line(name: str, present: bool) -> str:
        return f"{name}: {'disponível' if present else 'ausente'}"


class TranscribePage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.files: list[Path] = []
        self.transcript = None
        layout = QVBoxLayout(self)
        _header(
            layout,
            "Transcrever",
            "O Whisper transcreve no idioma da fala ou traduz a fala para inglês. O turbo não traduz.",
        )
        self.file_list = QListWidget()
        buttons = QHBoxLayout()
        add = QPushButton("Adicionar arquivos")
        add.clicked.connect(self._add)
        clear = QPushButton("Limpar lista")
        clear.clicked.connect(self._clear)
        buttons.addWidget(add)
        buttons.addWidget(clear)
        form = QFormLayout()
        self.model = QComboBox()
        for name in ("tiny", "base", "small", "medium", "large", "turbo", "tiny.en", "base.en", "small.en", "medium.en"):
            self.model.addItem(name)
        self.model.setCurrentText(session.db.get_setting("whisper_model", "tiny") or "tiny")
        self.language = QComboBox()
        self.language.addItem("Detectar automaticamente", "")
        for code, label in LANGUAGES:
            self.language.addItem(f"{label} ({code})", code)
        self.task = QComboBox()
        self.task.addItem("Transcrever", "transcribe")
        self.task.addItem("Traduzir fala para inglês", "translate")
        self.device = QComboBox()
        self.device.addItems(["cpu", "cuda"])
        self.words = QCheckBox("Marcação por palavra")
        self.words.setChecked(True)
        self.prompt = QLineEdit()
        self.clip_start = QDoubleSpinBox()
        self.clip_end = QDoubleSpinBox()
        for box in (self.clip_start, self.clip_end):
            box.setRange(0, 86_400)
            box.setDecimals(2)
        self.line_width = QDoubleSpinBox()
        self.line_width.setRange(0, 80)
        self.line_width.setDecimals(0)
        form.addRow("Modelo", self.model)
        form.addRow("Idioma", self.language)
        form.addRow("Tarefa", self.task)
        form.addRow("Dispositivo", self.device)
        form.addRow("", self.words)
        form.addRow("Prompt inicial", self.prompt)
        form.addRow("Início do trecho (s)", self.clip_start)
        form.addRow("Fim do trecho (s)", self.clip_end)
        form.addRow("Caracteres por linha (0 = sem limite)", self.line_width)
        self.run_button = QPushButton("Transcrever")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self._run)
        self.result = QPlainTextEdit()
        self.result.setPlaceholderText("O texto transcrito aparece aqui e pode ser editado.")
        save_row = QHBoxLayout()
        save_text = QPushButton("Salvar texto")
        save_text.clicked.connect(self._save_text)
        save_segments = QPushButton("Salvar segmentos")
        save_segments.clicked.connect(self._save_segments)
        to_subs = QPushButton("Abrir no editor de legendas")
        to_subs.clicked.connect(self._to_subs)
        to_speech = QPushButton("Ler este texto")
        to_speech.clicked.connect(self._to_speech)
        for button in (save_text, save_segments, to_subs, to_speech):
            save_row.addWidget(button)
        self.player = PlayerBar()
        layout.addWidget(self.file_list)
        layout.addLayout(buttons)
        layout.addLayout(form)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result, 1)
        layout.addLayout(save_row)
        layout.addWidget(self.player)

    def add_files(self, paths: list[str] | list[Path]) -> None:
        for raw in paths:
            path = Path(raw)
            if path not in self.files:
                self.files.append(path)
                self.file_list.addItem(str(path))
        if self.files:
            self.player.set_file(self.files[0])

    def _add(self) -> None:
        path = ask_open(self, "Mídia (*.mp3 *.wav *.m4a *.aac *.ogg *.flac *.mp4 *.mkv *.mov *.webm *.avi)")
        if path:
            self.add_files([path])

    def _clear(self) -> None:
        self.files.clear()
        self.file_list.clear()

    def _options(self) -> TranscribeOptions:
        language = self.language.currentData() or None
        width = int(self.line_width.value())
        return TranscribeOptions(
            model=self.model.currentText(),
            language=language,
            task=self.task.currentData(),
            device=self.device.currentText(),
            word_timestamps=self.words.isChecked(),
            initial_prompt=self.prompt.text().strip() or None,
            clip_start=self.clip_start.value() or None,
            clip_end=self.clip_end.value() or None,
            max_line_width=width or None,
            highlight_words=False,
        )

    def _run(self) -> None:
        if not self.files:
            warn(self, "Adicione pelo menos um arquivo.")
            return
        options = self._options()
        if options.task == "translate" and options.model in {"turbo"} or options.model.endswith(".en") and options.task == "translate":
            warn(self, "Escolha um modelo multilíngue. O turbo e os modelos .en não traduzem.")
            return
        installed = set()
        for root in self.session.models.whisper_roots():
            installed.update(installed_whisper_names(root))
        if options.model not in installed:
            warn(
                self,
                f"O modelo {options.model} não está neste computador. "
                "Abra Modelos e vozes, escolha a pasta e baixe antes de transcrever.",
            )
            return
        files = list(self.files)
        self.session.db.set_setting("whisper_model", options.model)

        def job(progress, cancel):
            results = []
            for index, path in enumerate(files, start=1):
                progress(int((index - 1) * 100 / len(files)), path.name)
                results.append(self.session.transcription.transcribe_file(path, options, progress, cancel))
            return results

        self.session.tasks.start("Transcrever", job, self._done, lambda message: warn(self, message))

    def _done(self, results) -> None:
        self.transcript = results[-1] if results else None
        if self.transcript is None:
            return
        self.result.setPlainText(self.transcript.text)
        info(self, "Transcrição pronta. Use Salvar texto ou Salvar segmentos para gravar o arquivo.")

    def _save_text(self) -> None:
        text = self.result.toPlainText()
        source = self.transcript.source_name if self.transcript else "transcricao"
        path = ask_save(self, str(self.session.output_dir() / suggest_name(source, ".txt")), PLAIN_FILTER)
        if path is None:
            return
        try:
            saved = self.session.exporter.export_text(path, text, source)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("transcrição", source, saved, "texto")

    def _save_segments(self) -> None:
        if self.transcript is None:
            warn(self, "Ainda não há trechos com tempo. Rode a transcrição antes.")
            return
        path = ask_save(
            self,
            str(self.session.output_dir() / suggest_name(self.transcript.source_name, ".srt")),
            TEXT_FILTER,
        )
        if path is None:
            return
        width = int(self.line_width.value()) or None
        try:
            saved = self.session.exporter.export_transcript(
                path,
                self.transcript,
                plain_text=self.result.toPlainText(),
                captions=CaptionOptions(max_line_width=width),
                title=self.transcript.source_name,
            )
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("transcrição", self.transcript.source_name, saved, saved.suffix)

    def _to_subs(self) -> None:
        if self.transcript is None:
            warn(self, "Não há transcrição para enviar.")
            return
        self.session.bus.open_subtitles.emit(self.transcript)

    def _to_speech(self) -> None:
        text = self.result.toPlainText().strip()
        if not text:
            warn(self, "Não há texto para ler.")
            return
        self.session.bus.open_speech_text.emit(text)


class SpeechPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.wav_path: Path | None = None
        layout = QVBoxLayout(self)
        _header(
            layout,
            "Texto para voz",
            "A leitura usa Piper quando houver voz instalada, ou espeak-ng se ele estiver no sistema. O áudio só vai para o disco quando você salvar.",
        )
        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("Digite, cole ou abra um texto.")
        row = QHBoxLayout()
        open_button = QPushButton("Abrir texto")
        open_button.clicked.connect(self._open)
        save_text = QPushButton("Salvar texto")
        save_text.clicked.connect(self._save_text)
        row.addWidget(open_button)
        row.addWidget(save_text)
        form = QFormLayout()
        self.voice = QComboBox()
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(50, 200)
        self.speed.setValue(100)
        self.pitch = QSlider(Qt.Orientation.Horizontal)
        self.pitch.setRange(50, 180)
        self.pitch.setValue(100)
        self.speed_label = QLabel("1,0x")
        self.pitch_label = QLabel("1,0x")
        self.speed.valueChanged.connect(lambda value: self.speed_label.setText(f"{value / 100:.1f}x".replace(".", ",")))
        self.pitch.valueChanged.connect(lambda value: self.pitch_label.setText(f"{value / 100:.1f}x".replace(".", ",")))
        speed_box = QHBoxLayout()
        speed_box.addWidget(self.speed)
        speed_box.addWidget(self.speed_label)
        pitch_box = QHBoxLayout()
        pitch_box.addWidget(self.pitch)
        pitch_box.addWidget(self.pitch_label)
        form.addRow("Voz", self.voice)
        form.addRow("Velocidade", speed_box)
        form.addRow("Tom", pitch_box)
        actions = QHBoxLayout()
        read = QPushButton("Ler")
        read.setObjectName("primary")
        read.clicked.connect(self._read)
        save_audio = QPushButton("Salvar áudio")
        save_audio.clicked.connect(self._save_audio)
        refresh = QPushButton("Atualizar vozes")
        refresh.clicked.connect(self.reload_voices)
        actions.addWidget(read)
        actions.addWidget(save_audio)
        actions.addWidget(refresh)
        self.player = PlayerBar()
        self.engine_label = QLabel("")
        layout.addWidget(self.text, 1)
        layout.addLayout(row)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.engine_label)
        layout.addWidget(self.player)
        self.reload_voices()

    def set_text(self, text: str) -> None:
        self.text.setPlainText(text)

    def reload_voices(self) -> None:
        current = self.voice.currentData()
        self.voice.clear()
        self.voice.addItem("Voz do sistema, se houver espeak-ng", "")
        for voice in self.session.models.installed():
            self.voice.addItem(voice.voice_id, str(voice.model_path))
        preferred = self.session.db.get_setting("piper_voice", "")
        index = self.voice.findData(preferred or current)
        if index >= 0:
            self.voice.setCurrentIndex(index)

    def _selected_model(self) -> tuple[Path | None, Path | None]:
        raw = self.voice.currentData() or ""
        if not raw:
            return None, None
        model = Path(raw)
        config = Path(str(model) + ".json")
        return model, config if config.is_file() else None

    def _open(self) -> None:
        path = ask_open(self, "Texto (*.txt *.md)")
        if path is None:
            return
        try:
            self.text.setPlainText(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            warn(self, "O arquivo não está em UTF-8.")

    def _save_text(self) -> None:
        path = ask_save(self, str(self.session.output_dir() / "texto.txt"), PLAIN_FILTER)
        if path is None:
            return
        try:
            saved = self.session.exporter.export_text(path, self.text.toPlainText(), "Texto")
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("texto", "texto", saved)

    def _read(self) -> None:
        model, config = self._selected_model()
        target = self.session.data_dir / "tmp" / "leitura.wav"
        speed = clamp_speed(self.speed.value() / 100)
        pitch = clamp_pitch(self.pitch.value() / 100)
        text = self.text.toPlainText()

        def job(progress, cancel):
            progress(10, "Gerando fala")
            engine = self.session.speech.synthesize(text, target, speed, pitch, model, config, cancel)
            progress(100, engine)
            return engine

        self.session.tasks.start("Texto para voz", job, self._read_done, lambda message: warn(self, message))

    def _read_done(self, engine: str) -> None:
        self.wav_path = self.session.data_dir / "tmp" / "leitura.wav"
        self.player.set_file(self.wav_path)
        self.player.toggle()
        self.engine_label.setText(f"Motor usado: {engine}. Salve o WAV se quiser guardar o áudio.")

    def _save_audio(self) -> None:
        if self.wav_path is None or not self.wav_path.is_file():
            warn(self, "Gere a leitura antes de salvar o áudio.")
            return
        path = ask_save(self, str(self.session.output_dir() / "leitura.wav"), AUDIO_FILTER)
        if path is None:
            return
        try:
            if path.suffix.lower() == ".wav":
                saved = self.session.exporter.copy_file(self.wav_path, path)
            else:
                saved = self.session.media.convert(self.wav_path, path)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("voz", "leitura", saved, self.engine_label.text())


class TranslatePage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        layout = QVBoxLayout(self)
        _header(
            layout,
            "Traduzir",
            "Tradução de fala para inglês fica em Transcrever. Esta tela traduz texto e não atribui o resultado ao Whisper.",
        )
        columns = QHBoxLayout()
        self.source = QPlainTextEdit()
        self.source.setPlaceholderText("Texto original")
        self.result = QPlainTextEdit()
        self.result.setPlaceholderText("Tradução")
        columns.addWidget(self.source, 1)
        columns.addWidget(self.result, 1)
        form = QFormLayout()
        self.source_lang = QLineEdit("pt")
        self.target_lang = QLineEdit("en")
        form.addRow("Origem", self.source_lang)
        form.addRow("Destino", self.target_lang)
        run = QPushButton("Traduzir texto")
        run.setObjectName("primary")
        run.clicked.connect(self._run)
        save = QPushButton("Salvar tradução")
        save.clicked.connect(self._save)
        speech = QPushButton("Ler tradução")
        speech.clicked.connect(self._speech)
        row = QHBoxLayout()
        row.addWidget(run)
        row.addWidget(save)
        row.addWidget(speech)
        self.note = QLabel(self._engine_note())
        self.note.setWordWrap(True)
        layout.addLayout(columns, 1)
        layout.addLayout(form)
        layout.addLayout(row)
        layout.addWidget(self.note)

    def _engine_note(self) -> str:
        name = self.session.translation.engine_name()
        if name:
            return f"Motor de texto: {name}."
        return "Motor de texto ausente. Você ainda pode editar a tradução manualmente e salvá-la."

    def _run(self) -> None:
        source = self.source_lang.text().strip()
        target = self.target_lang.text().strip()
        text = self.source.toPlainText()

        def job(progress, cancel):
            progress(30, "Traduzindo")
            if cancel.is_set():
                raise AppError("Operação cancelada.")
            return self.session.translation.translate(text, source, target)

        self.session.tasks.start("Traduzir", job, self.result.setPlainText, lambda message: warn(self, message))

    def _save(self) -> None:
        path = ask_save(self, str(self.session.output_dir() / "traducao.txt"), PLAIN_FILTER)
        if path is None:
            return
        try:
            saved = self.session.exporter.export_text(path, self.result.toPlainText(), "Tradução")
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("tradução", "texto", saved)

    def _speech(self) -> None:
        text = self.result.toPlainText().strip()
        if not text:
            warn(self, "Não há tradução para ler.")
            return
        self.session.bus.open_speech_text.emit(text)


class SubtitlePage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.source_name = "legenda"
        layout = QVBoxLayout(self)
        _header(layout, "Legendas", "Edite os tempos, salve SRT, VTT ou ASS, ou desenhe a legenda no vídeo com FFmpeg.")
        self.table = QListWidget()
        self.rows: list[tuple[str, str, str]] = []
        form = QFormLayout()
        self.start = QLineEdit("0")
        self.end = QLineEdit("1")
        self.line = QPlainTextEdit()
        self.line.setFixedHeight(70)
        form.addRow("Início", self.start)
        form.addRow("Fim", self.end)
        form.addRow("Texto", self.line)
        buttons = QHBoxLayout()
        for label, slot in (
            ("Importar", self._import),
            ("Adicionar trecho", self._add),
            ("Atualizar selecionado", self._update),
            ("Dividir", self._split),
            ("Unir com o próximo", self._merge),
            ("Deslocar +0,5 s", lambda: self._shift(0.5)),
            ("Deslocar -0,5 s", lambda: self._shift(-0.5)),
        ):
            button = QPushButton(label)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        save_row = QHBoxLayout()
        save = QPushButton("Salvar legenda")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        burn = QPushButton("Gravar legenda no vídeo")
        burn.clicked.connect(self._burn)
        save_row.addWidget(save)
        save_row.addWidget(burn)
        self.table.currentRowChanged.connect(self._select)
        layout.addWidget(self.table, 1)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addLayout(save_row)

    def load_transcript(self, transcript) -> None:
        self.source_name = transcript.source_name or "legenda"
        self.rows = [
            (f"{segment.start:.3f}", f"{segment.end:.3f}", segment.text)
            for segment in transcript.segments
        ]
        self._paint()

    def _paint(self) -> None:
        self.table.clear()
        for start, end, text in self.rows:
            self.table.addItem(f"{start} → {end}  {text.replace(chr(10), ' ')}")

    def _select(self, index: int) -> None:
        if index < 0 or index >= len(self.rows):
            return
        start, end, text = self.rows[index]
        self.start.setText(start)
        self.end.setText(end)
        self.line.setPlainText(text)

    def _add(self) -> None:
        self.rows.append((self.start.text(), self.end.text(), self.line.toPlainText()))
        self._paint()

    def _update(self) -> None:
        index = self.table.currentRow()
        if index < 0:
            warn(self, "Selecione um trecho.")
            return
        self.rows[index] = (self.start.text(), self.end.text(), self.line.toPlainText())
        self._paint()
        self.table.setCurrentRow(index)

    def _segments(self):
        from congo_grey_parrot.subtitles.codec import segments_from_table, transcript_from_segments

        segments = segments_from_table(self.rows)
        return transcript_from_segments(segments, self.source_name)

    def _split(self) -> None:
        self._transform("split")

    def _merge(self) -> None:
        self._transform("merge")

    def _shift(self, delta: float) -> None:
        self._transform("shift", delta)

    def _transform(self, kind: str, delta: float = 0) -> None:
        from congo_grey_parrot.subtitles.edit import merge_with_next, shift_segments, split_segment

        index = self.table.currentRow()
        try:
            transcript = self._segments()
            if kind == "split":
                segments = split_segment(transcript.segments, index)
            elif kind == "merge":
                segments = merge_with_next(transcript.segments, index)
            else:
                segments = shift_segments(transcript.segments, delta)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.rows = [(f"{item.start:.3f}", f"{item.end:.3f}", item.text) for item in segments]
        self._paint()

    def _import(self) -> None:
        path = ask_open(self, "Legenda (*.srt *.vtt *.json)")
        if path is None:
            return
        from congo_grey_parrot.subtitles.codec import parse_srt, parse_transcript_json, parse_vtt

        try:
            raw = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".srt":
                transcript = parse_srt(raw)
            elif path.suffix.lower() == ".vtt":
                transcript = parse_vtt(raw)
            else:
                transcript = parse_transcript_json(raw, path.name)
        except (AppError, UnicodeDecodeError) as exc:
            warn(self, str(exc) if isinstance(exc, AppError) else "O arquivo não está em UTF-8.")
            return
        self.load_transcript(transcript)

    def _save(self) -> None:
        try:
            transcript = self._segments()
        except AppError as exc:
            warn(self, str(exc))
            return
        path = ask_save(self, str(self.session.output_dir() / suggest_name(self.source_name, ".srt")), TEXT_FILTER)
        if path is None:
            return
        try:
            saved = self.session.exporter.export_transcript(path, transcript, title=self.source_name)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.session.remember("legenda", self.source_name, saved)

    def _burn(self) -> None:
        try:
            transcript = self._segments()
        except AppError as exc:
            warn(self, str(exc))
            return
        video = ask_open(self, "Vídeo (*.mp4 *.mkv *.mov *.webm *.avi)")
        if video is None:
            return
        output = ask_save(self, str(self.session.output_dir() / suggest_name(video.name, ".mp4")), "MP4 (*.mp4)")
        if output is None:
            return
        subtitle = self.session.data_dir / "tmp" / "queima.srt"
        try:
            self.session.exporter.export_transcript(subtitle, transcript)
        except AppError as exc:
            warn(self, str(exc))
            return

        def job(progress, cancel):
            progress(20, "Renderizando legenda")
            if cancel.is_set():
                raise AppError("Operação cancelada.")
            return self.session.media.burn_subtitles(video, subtitle, output)

        self.session.tasks.start(
            "Legenda no vídeo",
            job,
            lambda saved: self._burn_done(saved),
            lambda message: warn(self, message),
        )

    def _burn_done(self, saved: Path) -> None:
        self.session.remember("vídeo legendado", self.source_name, saved)
        info(self, f"Vídeo salvo em {saved}")
