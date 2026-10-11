from __future__ import annotations

from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.transcript import Segment, Transcript, WordTiming
from congo_grey_parrot.models.catalog import installed_whisper_names
from congo_grey_parrot.transcription.options import TranscribeOptions, validate_options


class TranscriptionService:
    def __init__(self, model_dir: Path, roots=None):
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.roots = roots or (lambda: [self.model_dir])
        self._model = None
        self._key: tuple[str, str] | None = None

    def engine_name(self) -> str:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return ""
        return "faster-whisper"

    def unload(self) -> None:
        self._model = None
        self._key = None

    def preload(self, model_name: str, device: str, progress, cancel) -> None:
        self._load(model_name, device, progress, cancel, allow_download=True)

    def transcribe_file(self, path: Path, options: TranscribeOptions, progress, cancel) -> Transcript:
        validate_options(options)
        if not path.is_file():
            raise AppError("Arquivo de áudio ou vídeo não encontrado.")
        if self.engine_name() == "":
            raise AppError(
                "O motor faster-whisper não está instalado. "
                "No ambiente do Desktop, execute: pip install faster-whisper"
            )
        if cancel is not None and cancel.is_set():
            raise AppError("Operação cancelada.")
        model = self._load(options.model, options.device, progress, cancel, allow_download=False)
        progress(20, f"Transcrevendo {path.name}")
        kwargs = {
            "language": options.language,
            "task": options.task,
            "beam_size": options.beam_size,
            "temperature": options.temperature,
            "condition_on_previous_text": options.condition_on_previous_text,
            "word_timestamps": options.word_timestamps,
            "initial_prompt": options.initial_prompt or None,
        }
        if options.clip_start is not None or options.clip_end is not None:
            start = 0 if options.clip_start is None else options.clip_start
            kwargs["clip_timestamps"] = f"{start}" if options.clip_end is None else f"{start},{options.clip_end}"
        segments_iter, info = model.transcribe(str(path), **kwargs)
        segments: list[Segment] = []
        for index, segment in enumerate(segments_iter, start=1):
            if cancel is not None and cancel.is_set():
                raise AppError("Operação cancelada.")
            words = []
            for word in segment.words or []:
                probability = None if word.probability is None else float(word.probability)
                words.append(WordTiming(word.word, float(word.start), float(word.end), probability))
            segments.append(Segment(float(segment.start), float(segment.end), segment.text.strip(), tuple(words)))
            progress(min(95, 20 + index), f"Trecho {index}")
        text = " ".join(item.text for item in segments if item.text).strip()
        language = options.language or getattr(info, "language", "") or ""
        progress(100, "Transcrição pronta")
        return Transcript(
            text=text,
            language=str(language),
            task=options.task,
            model=options.model,
            segments=tuple(segments),
            source_name=path.name,
        )

    def _load(self, model_name: str, device: str, progress, cancel, allow_download: bool):
        if cancel is not None and cancel.is_set():
            raise AppError("Operação cancelada.")
        key = (model_name, device)
        if self._model is not None and self._key == key:
            return self._model
        progress(8, f"Carregando modelo {model_name}")
        from faster_whisper import WhisperModel

        if allow_download:
            root = self.model_dir
        else:
            root = self._root_for(model_name)
            if root is None:
                raise AppError(
                    f"O modelo {model_name} não está neste computador. "
                    "Baixe em Modelos e vozes e escolha a pasta. A transcrição não baixa nada sozinha."
                )
        compute_type = "int8" if device == "cpu" else "float16"
        try:
            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(root),
                local_files_only=not allow_download,
            )
        except Exception as exc:
            if not allow_download:
                raise AppError(
                    f"O modelo {model_name} não está neste computador. "
                    "Baixe em Modelos e vozes. A transcrição não baixa nada sozinha."
                ) from exc
            raise AppError(f"Não foi possível carregar o modelo {model_name}. {exc}") from exc
        self._model = model
        self._key = key
        progress(18, "Modelo pronto")
        return model

    def _root_for(self, model_name: str) -> Path | None:
        for root in self.roots():
            if model_name in installed_whisper_names(root):
                return root
        return None
