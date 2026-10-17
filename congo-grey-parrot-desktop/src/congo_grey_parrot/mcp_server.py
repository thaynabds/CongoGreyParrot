from __future__ import annotations

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

from runtime import make_server, serve  # noqa: E402


def local_path(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    home = Path.home().resolve()
    if path != home and home not in path.parents:
        raise AppError("O caminho precisa ficar dentro da sua pasta pessoal.")
    return path


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
    def transcrever_arquivo(caminho: str, idioma: str = "pt", modelo: str = "base") -> str:
        """Transcreve um áudio local. O arquivo precisa estar na pasta pessoal."""
        path = local_path(caminho)
        language = idioma.strip() or None
        options = TranscribeOptions(
            model=modelo.strip() or "base",
            language=language,
            device="cpu",
            task="transcribe",
            word_timestamps=False,
        )
        service = TranscriptionService(app_data_dir() / "whisper")
        transcript = service.transcribe_file(path, options, lambda _pct, _msg: None, threading.Event())
        return transcript.text or "Não encontrei fala nesse arquivo."

    @server.tool()
    def falar_texto(texto: str, caminho_wav: str, voz: str = "") -> str:
        """Gera um WAV com Piper, se houver voz instalada, ou com espeak-ng."""
        dest = local_path(caminho_wav)
        model = None
        config = None
        if voz.strip():
            model = local_path(voz)
            config = Path(str(model) + ".json")
        else:
            installed = scan_installed_voices(app_data_dir() / "vozes")
            if installed:
                model = installed[0].model_path
                config = installed[0].config_path
        engine = SpeechService().synthesize(texto, dest, model_path=model, config_path=config)
        return f"{engine}: {dest}"

    @server.tool()
    def traduzir_texto(texto: str, origem: str, destino: str) -> str:
        """Traduz texto com o motor instalado. Códigos curtos, por exemplo pt e en."""
        return TranslationService().translate(texto, origem.strip(), destino.strip())

    return server


def main() -> None:
    serve(build_server(), default_port=8765)


if __name__ == "__main__":
    main()
