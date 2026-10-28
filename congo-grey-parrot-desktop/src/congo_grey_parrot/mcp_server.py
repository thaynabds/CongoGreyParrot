from __future__ import annotations

import re
import sys
import threading
from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.paths import app_data_dir
from congo_grey_parrot.models.catalog import installed_whisper_names, scan_installed_voices
from congo_grey_parrot.speech.service import SpeechService
from congo_grey_parrot.transcription.languages import LANGUAGES
from congo_grey_parrot.transcription.options import TranscribeOptions
from congo_grey_parrot.transcription.service import TranscriptionService
from congo_grey_parrot.translation.service import TranslationService

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import guarded_path, make_server, serve, user_errors  # noqa: E402

MEDIA_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mkv", ".mov", ".webm", ".avi"}


def local_path(raw: str, suffixes: set[str]) -> Path:
    try:
        return guarded_path(raw, suffixes)
    except ValueError as exc:
        raise AppError(str(exc)) from exc


def voice_path(raw: str) -> Path:
    """Voz Piper da pasta de vozes do programa ou de uma pasta comum da pasta pessoal."""
    voices = (app_data_dir() / "vozes").resolve()
    candidate = Path(raw).expanduser().resolve()
    if voices in candidate.parents and candidate.suffix.lower() == ".onnx":
        return candidate
    return local_path(raw, {".onnx"})


def build_server():
    server = make_server("Congo Grey Parrot Desktop")

    @server.tool()
    def listar_idiomas() -> str:
        """Lista os códigos de idioma que a transcrição aceita."""
        return "\n".join(f"{code} {label}" for code, label in LANGUAGES)

    @server.tool()
    def listar_modelos() -> str:
        """Lista os modelos Whisper já baixados neste computador."""
        names = installed_whisper_names(app_data_dir() / "whisper")
        if not names:
            return "Nenhum modelo Whisper nesta pasta."
        return "\n".join(names)

    @server.tool()
    @user_errors(AppError, ValueError)
    def transcrever_arquivo(caminho: str, idioma: str = "pt", modelo: str = "base") -> str:
        """Transcreve um áudio ou vídeo local da pasta pessoal, com um modelo já baixado."""
        path = local_path(caminho, MEDIA_SUFFIXES)
        name = modelo.strip() or "base"
        if not re.fullmatch(r"[a-z0-9][a-z0-9.\-]{0,40}", name):
            raise AppError("Informe o nome do modelo, por exemplo base ou small. Use listar_modelos.")
        language = idioma.strip() or None
        options = TranscribeOptions(
            model=name,
            language=language,
            device="cpu",
            task="transcribe",
            word_timestamps=False,
        )
        service = TranscriptionService(app_data_dir() / "whisper")
        transcript = service.transcribe_file(path, options, lambda _pct, _msg: None, threading.Event())
        return transcript.text or "Não encontrei fala nesse arquivo."

    @server.tool()
    @user_errors(AppError, ValueError)
    def falar_texto(texto: str, caminho_wav: str, voz: str = "") -> str:
        """Gera um WAV na pasta pessoal com Piper, se houver voz instalada, ou com espeak-ng."""
        dest = local_path(caminho_wav, {".wav"})
        model = None
        config = None
        if voz.strip():
            model = voice_path(voz)
            config = Path(str(model) + ".json")
        else:
            installed = scan_installed_voices(app_data_dir() / "vozes")
            if installed:
                model = installed[0].model_path
                config = installed[0].config_path
        engine = SpeechService().synthesize(texto, dest, model_path=model, config_path=config)
        return f"{engine}: {dest}"

    @server.tool()
    @user_errors(AppError, ValueError)
    def traduzir_texto(texto: str, origem: str, destino: str) -> str:
        """Traduz texto com o motor instalado. Códigos curtos, por exemplo pt e en."""
        return TranslationService().translate(texto, origem.strip(), destino.strip())

    return server


def main() -> None:
    serve(build_server(), default_port=8765)


if __name__ == "__main__":
    main()
