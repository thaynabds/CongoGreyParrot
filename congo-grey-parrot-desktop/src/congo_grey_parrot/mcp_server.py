"""Servidor MCP do Desktop: a IA faz por aqui o que a pessoa faz nas páginas do programa.

Toda ferramenta trata os argumentos como vindos de alguém hostil (injeção de prompt num
documento, por exemplo): arquivos só na pasta pessoal e fora de pastas ocultas, tipos
fixos, tamanhos limitados, nada sobrescrito sem pedido e nada apagado sem confirmar=true.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from congo_grey_parrot.aiconector.runtime import guarded_dir, guarded_path, make_server, serve, user_errors
from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.paths import app_data_dir
from congo_grey_parrot.models.catalog import WHISPER_MODELS, installed_whisper_names
from congo_grey_parrot.resumo import resumir, resumo_texto
from congo_grey_parrot.transcription.languages import LANGUAGES
from congo_grey_parrot.transcription.options import TranscribeOptions

TEXT_SUFFIXES = {".txt", ".md", ".docx", ".pdf", ".srt", ".vtt"}
SAVE_TEXT_SUFFIXES = {".txt", ".md", ".docx", ".pdf"}
CAPTION_SUFFIXES = {".srt", ".vtt", ".ass", ".tsv", ".json", ".jsonl", ".txt", ".md", ".docx", ".pdf"}
SUBTITLE_IN_SUFFIXES = {".srt", ".vtt", ".ass", ".ssa"}
MAX_TEXT_FILE_BYTES = 20 * 1024 * 1024
MAX_MEDIA_BYTES = 4 * 1024 * 1024 * 1024
MAX_TEXT_CHARS = 200_000
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}
VIDEO_SUFFIXES = {".mp4", ".mkv", ".mov", ".webm", ".avi"}
MEDIA_SUFFIXES = AUDIO_SUFFIXES | VIDEO_SUFFIXES
WHISPER_NAMES = {item.name for item in WHISPER_MODELS}
_VOICE_ID = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]{0,80}")


def local_path(raw: str, suffixes: set[str]) -> Path:
    try:
        return guarded_path(raw, suffixes)
    except ValueError as exc:
        raise AppError(str(exc)) from exc


def output_path(raw: str, suffixes: set[str], overwrite: bool) -> Path:
    path = local_path(raw, suffixes)
    if path.exists() and not overwrite:
        raise AppError(f"{path.name} já existe. Peça outro nome ou chame com sobrescrever=true.")
    return path


def media_path(raw: str, suffixes: set[str] = MEDIA_SUFFIXES) -> Path:
    path = local_path(raw, suffixes)
    if not path.is_file():
        raise AppError(f"Não achei o arquivo: {path}")
    if path.stat().st_size > MAX_MEDIA_BYTES:
        raise AppError("O arquivo passa de 4 GB.")
    return path


def _db():
    from congo_grey_parrot.persistence.database import Database

    return Database(app_data_dir() / "app.sqlite3")


def _places(db, key: str) -> list[Path]:
    raw = db.get_setting(key, "") or ""
    return [Path(line.strip()) for line in raw.splitlines() if line.strip()]


def _models(db):
    from congo_grey_parrot.models.service import ModelService

    service = ModelService(app_data_dir() / "vozes", app_data_dir() / "whisper")
    service.extra_voices = _places(db, "voice_places")
    service.extra_whisper = _places(db, "whisper_places")
    return service


def _transcription(models):
    from congo_grey_parrot.transcription.service import TranscriptionService

    return TranscriptionService(models.whisper_root, roots=models.whisper_roots)


def _remember(kind: str, source: str, output: Path | str, detail: str = "") -> None:
    db = _db()
    try:
        db.add_history(kind, source, str(output), "ok", f"pela IA (MCP) {detail}".strip())
    finally:
        db.close()


def _model_name(raw: str, catalog_only: bool = False) -> str:
    """Nome curto do modelo. Para baixar, só os da lista oficial; para usar, também um já baixado (ex.: large-v3)."""
    name = (raw or "").strip() or "base"
    if name in WHISPER_NAMES:
        return name
    if not catalog_only and re.fullmatch(r"[a-z0-9][a-z0-9.\-]{0,40}", name):
        return name
    raise AppError("Modelo desconhecido. Use listar_modelos para ver os nomes.")


def _language(raw: str) -> str | None:
    code = (raw or "").strip()
    if not code or code == "auto":
        return None
    if code not in {item[0] for item in LANGUAGES}:
        raise AppError("Idioma desconhecido. Use listar_idiomas.")
    return code


def _transcribe(path: Path, idioma: str, modelo: str, task: str = "transcribe"):
    db = _db()
    try:
        models = _models(db)
    finally:
        db.close()
    options = TranscribeOptions(
        model=_model_name(modelo),
        language=_language(idioma),
        device="cpu",
        task=task,
        word_timestamps=False,
    )
    return _transcription(models).transcribe_file(path, options, lambda _pct, _msg: None, threading.Event())


def build_server():
    server = make_server("Congo Grey Parrot Desktop")

    # Transcrever e legendar -------------------------------------------------

    @server.tool()
    def listar_idiomas() -> str:
        """Lista os códigos de idioma que a transcrição aceita (use auto para detectar)."""
        return "\n".join(f"{code} {label}" for code, label in LANGUAGES)

    @server.tool()
    def listar_modelos() -> str:
        """Lista os modelos Whisper conhecidos e diz quais já estão baixados neste computador."""
        db = _db()
        try:
            models = _models(db)
        finally:
            db.close()
        installed = set()
        for root in models.whisper_roots():
            installed.update(installed_whisper_names(root))
        lines = []
        for item in WHISPER_MODELS:
            flag = "baixado" if item.name in installed else "não baixado"
            lines.append(f"{item.name} ({item.profile}, {flag}): {item.note}")
        return "\n".join(lines)

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def transcrever_arquivo(caminho: str, idioma: str = "pt", modelo: str = "base") -> str:
        """Transcreve um áudio ou vídeo local da pasta pessoal, com um modelo já baixado."""
        path = media_path(caminho)
        transcript = _transcribe(path, idioma, modelo)
        return transcript.text or "Não encontrei fala nesse arquivo."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def gerar_legenda(
        caminho: str,
        caminho_saida: str,
        idioma: str = "pt",
        modelo: str = "base",
        traduzir_para_ingles: bool = False,
        sobrescrever: bool = False,
    ) -> str:
        """Transcreve um áudio ou vídeo e salva legenda ou texto: SRT, VTT, ASS, TSV, JSON, JSONL, TXT, MD, DOCX ou PDF."""
        from congo_grey_parrot.files.export_service import ExportService

        source = media_path(caminho)
        target = output_path(caminho_saida, CAPTION_SUFFIXES, sobrescrever)
        task = "translate" if traduzir_para_ingles else "transcribe"
        transcript = _transcribe(source, idioma, modelo, task)
        saved = ExportService().export_transcript(target, transcript, title=source.stem)
        _remember("legenda", source.name, saved)
        return f"Legenda salva em {saved} ({len(transcript.segments)} trechos)."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def converter_legenda(caminho: str, caminho_saida: str, sobrescrever: bool = False) -> str:
        """Converte uma legenda SRT, VTT ou ASS para outro formato (SRT, VTT, ASS, TSV, JSON, TXT, MD, DOCX, PDF)."""
        from congo_grey_parrot.files.export_service import ExportService
        from congo_grey_parrot.subtitles.codec import load_subtitle_file

        source = local_path(caminho, SUBTITLE_IN_SUFFIXES)
        if not source.is_file() or source.stat().st_size > MAX_TEXT_FILE_BYTES:
            raise AppError("Não achei a legenda, ou ela passa de 20 MB.")
        target = output_path(caminho_saida, CAPTION_SUFFIXES, sobrescrever)
        saved = ExportService().export_transcript(target, load_subtitle_file(source), title=source.stem)
        _remember("legenda", source.name, saved, "conversão")
        return f"Legenda salva em {saved}."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def ajustar_tempo_legenda(caminho: str, segundos: float, caminho_saida: str, sobrescrever: bool = False) -> str:
        """Adianta (segundos negativos) ou atrasa (positivos) todas as falas de uma legenda e salva o resultado."""
        from congo_grey_parrot.files.export_service import ExportService
        from congo_grey_parrot.subtitles.codec import load_subtitle_file, transcript_from_segments
        from congo_grey_parrot.subtitles.edit import shift_segments

        delta = float(segundos)
        if not -86400 <= delta <= 86400:
            raise AppError("Use no máximo um dia de diferença.")
        source = local_path(caminho, SUBTITLE_IN_SUFFIXES)
        if not source.is_file() or source.stat().st_size > MAX_TEXT_FILE_BYTES:
            raise AppError("Não achei a legenda, ou ela passa de 20 MB.")
        target = output_path(caminho_saida, CAPTION_SUFFIXES, sobrescrever)
        original = load_subtitle_file(source)
        moved = transcript_from_segments(shift_segments(original.segments, delta), original.source_name)
        saved = ExportService().export_transcript(target, moved, title=source.stem)
        _remember("legenda", source.name, saved, f"tempo {delta:+.2f}s")
        return f"Legenda ajustada em {delta:+.2f} s e salva em {saved}."

    # Voz, tradução e resumo ---------------------------------------------------

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def falar_texto(texto: str, caminho_wav: str, voz: str = "", sobrescrever: bool = False) -> str:
        """Gera um WAV na pasta pessoal com uma voz Piper instalada (nome de listar_vozes) ou com espeak-ng."""
        from congo_grey_parrot.speech.service import SpeechService

        if not texto.strip():
            raise AppError("Escreva o texto.")
        if len(texto) > MAX_TEXT_CHARS:
            raise AppError("O texto passa de 200 mil caracteres.")
        dest = output_path(caminho_wav, {".wav"}, sobrescrever)
        model = config = None
        db = _db()
        try:
            installed = _models(db).installed()
        finally:
            db.close()
        if voz.strip():
            match = [item for item in installed if item.voice_id == voz.strip()]
            if not match:
                raise AppError("Essa voz não está instalada. Use listar_vozes ou baixar_voz.")
            model, config = match[0].model_path, match[0].config_path
        elif installed:
            model, config = installed[0].model_path, installed[0].config_path
        engine = SpeechService().synthesize(texto, dest, model_path=model, config_path=config)
        _remember("voz", "texto da IA", dest, engine)
        return f"{engine}: {dest}"

    @server.tool()
    @user_errors(AppError, ValueError)
    def traduzir_texto(texto: str, origem: str, destino: str) -> str:
        """Traduz texto com o motor instalado. Códigos curtos, por exemplo pt e en."""
        from congo_grey_parrot.translation.service import TranslationService

        if len(texto) > MAX_TEXT_CHARS:
            raise AppError("O texto passa de 200 mil caracteres.")
        return TranslationService().translate(texto, origem.strip(), destino.strip())

    @server.tool()
    def resumir_texto(texto: str, frases: int = 0) -> str:
        """Resume um texto: frases principais tiradas do próprio texto, decisões, tarefas e perguntas. Sem IA e sem internet."""
        return resumo_texto(resumir(texto[:MAX_TEXT_CHARS], _sentences(frases)))

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def resumir_arquivo(caminho: str, frases: int = 0) -> str:
        """Resume um TXT, MD, DOCX, PDF com texto, SRT ou VTT da pasta pessoal, fora de pastas ocultas."""
        path, text = _read_text(caminho)
        return resumo_texto(resumir(text, _sentences(frases)), f"Resumo de {path.name}")

    # Documentos e arquivos ----------------------------------------------------

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def ler_documento(caminho: str) -> str:
        """Lê o texto de um TXT, MD, DOCX, PDF, SRT ou VTT da pasta pessoal (até 200 mil caracteres)."""
        path, text = _read_text(caminho)
        cut = "" if len(text) <= MAX_TEXT_CHARS else "\n[cortado em 200 mil caracteres]"
        return f"{path.name}:\n{text[:MAX_TEXT_CHARS]}{cut}"

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def salvar_texto(caminho: str, texto: str, titulo: str = "", sobrescrever: bool = False) -> str:
        """Salva um texto como TXT, MD, DOCX ou PDF na pasta pessoal. Não sobrescreve sem sobrescrever=true."""
        from congo_grey_parrot.files.export_service import ExportService

        if len(texto) > MAX_TEXT_CHARS:
            raise AppError("O texto passa de 200 mil caracteres.")
        target = output_path(caminho, SAVE_TEXT_SUFFIXES, sobrescrever)
        saved = ExportService().export_text(target, texto, titulo.strip()[:200])
        _remember("documento", titulo.strip()[:80] or "texto da IA", saved)
        return f"Salvo em {saved}."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def converter_midia(origem: str, destino: str, bitrate_k: int = 0, sobrescrever: bool = False) -> str:
        """Converte áudio ou vídeo com o FFmpeg (por exemplo MP4 para MP3). Arquivos na pasta pessoal."""
        from congo_grey_parrot.media.ffmpeg_service import FfmpegService

        source = media_path(origem)
        target = output_path(destino, MEDIA_SUFFIXES, sobrescrever)
        if target == source:
            raise AppError("Escolha um destino diferente da origem.")
        rate = max(0, min(int(bitrate_k), 50_000)) or None
        saved = FfmpegService().convert(source, target, rate)
        _remember("conversão", source.name, saved)
        return f"Convertido em {saved}."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def gravar_legenda_no_video(video: str, legenda: str, destino: str, sobrescrever: bool = False) -> str:
        """Grava (queima) uma legenda SRT, VTT ou ASS dentro de um vídeo novo, com o FFmpeg."""
        from congo_grey_parrot.media.ffmpeg_service import FfmpegService

        source = media_path(video, VIDEO_SUFFIXES)
        caption = local_path(legenda, SUBTITLE_IN_SUFFIXES)
        if not caption.is_file():
            raise AppError(f"Não achei a legenda: {caption}")
        target = output_path(destino, VIDEO_SUFFIXES, sobrescrever)
        if target == source:
            raise AppError("Escolha um destino diferente do vídeo original.")
        saved = FfmpegService().burn_subtitles(source, caption, target)
        _remember("legenda no vídeo", source.name, saved)
        return f"Vídeo legendado em {saved}."

    @server.tool()
    def listar_saidas() -> str:
        """Lista os arquivos da pasta de saída do programa (a Biblioteca), do mais novo para o mais velho."""
        folder = _output_dir()
        files = sorted((item for item in folder.iterdir() if item.is_file()), key=lambda item: item.stat().st_mtime, reverse=True)
        if not files:
            return f"A pasta de saída está vazia: {folder}"
        return f"Pasta: {folder}\n" + "\n".join(str(item) for item in files[:200])

    # Modelos e vozes ----------------------------------------------------------

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def baixar_modelo(nome: str) -> str:
        """Baixa um modelo Whisper da lista oficial (use listar_modelos) para transcrever sem internet depois."""
        name = _model_name(nome, catalog_only=True)
        db = _db()
        try:
            service = _transcription(_models(db))
        finally:
            db.close()
        service.preload(name, "cpu", lambda _pct, _msg: None, threading.Event())
        _remember("modelo", name, app_data_dir() / "whisper")
        return f"Modelo {name} pronto para uso offline."

    @server.tool()
    def listar_vozes(idioma: str = "") -> str:
        """Lista as vozes Piper instaladas e as do catálogo que podem ser baixadas (filtre por idioma, ex.: pt)."""
        db = _db()
        try:
            models = _models(db)
        finally:
            db.close()
        installed = {item.voice_id for item in models.installed()}
        wanted = idioma.strip().lower()
        lines = ["Instaladas: " + (", ".join(sorted(installed)) or "nenhuma"), "Catálogo:"]
        for entry in models.catalog():
            if wanted and not entry.language.lower().startswith(wanted):
                continue
            flag = " (instalada)" if entry.id in installed else ""
            lines.append(f"{entry.id}: {entry.name}, {entry.language_label}, {entry.quality}{flag}")
        return "\n".join(lines[:400])

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def baixar_voz(id_voz: str) -> str:
        """Baixa uma voz Piper do catálogo do programa (use listar_vozes). Só baixa dos endereços do catálogo."""
        wanted = id_voz.strip()
        db = _db()
        try:
            models = _models(db)
        finally:
            db.close()
        match = [entry for entry in models.catalog() if entry.id == wanted]
        if not match:
            raise AppError("Essa voz não está no catálogo. Use listar_vozes.")
        folder = models.download_voice(match[0], lambda _pct, _msg: None, threading.Event())
        _remember("voz", wanted, folder, "baixada")
        return f"Voz {wanted} instalada em {folder}."

    @server.tool()
    @user_errors(AppError, ValueError, OSError)
    def remover_voz(id_voz: str, confirmar: bool = False) -> str:
        """Apaga uma voz instalada. Só apaga com confirmar=true, depois de perguntar à pessoa."""
        wanted = id_voz.strip()
        if not _VOICE_ID.fullmatch(wanted):
            raise AppError("Informe o nome da voz, como aparece em listar_vozes.")
        db = _db()
        try:
            models = _models(db)
        finally:
            db.close()
        match = [item for item in models.installed() if item.voice_id == wanted]
        if not match:
            raise AppError("Essa voz não está instalada.")
        if confirmar is not True:
            return f"Nada foi apagado. Pergunte à pessoa se quer mesmo remover a voz {wanted} e chame de novo com confirmar=true."
        models.remove_voice(match[0].folder)
        return f"Voz {wanted} removida."

    # Histórico e configurações -------------------------------------------------

    @server.tool()
    def listar_historico(limite: int = 50) -> str:
        """Mostra o histórico do programa: o que foi transcrito, convertido, salvo e quando."""
        count = max(1, min(_int(limite, 50), 500))
        db = _db()
        try:
            rows = db.list_history()[:count]
        finally:
            db.close()
        if not rows:
            return "O histórico está vazio."
        return "\n".join(
            f"{row['created_at']} · {row['kind']} · {row['source_name']} → {row['output_path']} ({row['status']}) {row['detail']}".rstrip()
            for row in rows
        )

    @server.tool()
    def limpar_historico(confirmar: bool = False) -> str:
        """Apaga todo o histórico. Só apaga com confirmar=true, depois de perguntar à pessoa. Os arquivos ficam."""
        if confirmar is not True:
            return "Nada foi apagado. Pergunte à pessoa se quer mesmo limpar o histórico e chame de novo com confirmar=true."
        db = _db()
        try:
            db.clear_history()
        finally:
            db.close()
        return "Histórico apagado. Os arquivos salvos continuam onde estavam."

    @server.tool()
    def ver_configuracoes() -> str:
        """Mostra tema, filtro de cor, tamanho da letra, pasta de saída e modelo padrão."""
        db = _db()
        try:
            values = {key: db.get_setting(key, default) for key, default in _SETTINGS_DEFAULTS.items()}
        finally:
            db.close()
        values["output_dir"] = str(_output_dir())
        return "\n".join(f"{key}: {value}" for key, value in values.items())

    @server.tool()
    @user_errors(AppError, ValueError)
    def alterar_configuracao(chave: str, valor: str) -> str:
        """Muda uma configuração: theme, color_filter, font_scale (0.8 a 2.0), output_dir (pasta pessoal) ou whisper_model."""
        key = chave.strip()
        value = _validate_setting(key, valor.strip())
        db = _db()
        try:
            db.set_setting(key, value)
        finally:
            db.close()
        return f"{key} agora é {value}. A janela aberta aplica na próxima vez que abrir a página de configurações ou reiniciar."

    return server


_SETTINGS_DEFAULTS = {
    "theme": "light",
    "color_filter": "none",
    "font_scale": "1",
    "whisper_model": "base",
}


def _validate_setting(key: str, value: str) -> str:
    if key == "theme":
        from congo_grey_parrot.ui.theme import THEMES

        if value not in THEMES:
            raise AppError("Tema desconhecido: " + ", ".join(THEMES))
        return value
    if key == "color_filter":
        from congo_grey_parrot.ui.color_filter import FILTERS

        if value not in FILTERS:
            raise AppError("Filtro desconhecido: " + ", ".join(FILTERS))
        return value
    if key == "font_scale":
        try:
            scale = float(value)
        except ValueError:
            raise AppError("Use um número, por exemplo 1.2.") from None
        if not 0.8 <= scale <= 2.0:
            raise AppError("Use um valor de 0.8 a 2.0.")
        return str(scale)
    if key == "output_dir":
        try:
            folder = guarded_dir(value)
        except ValueError as exc:
            raise AppError(str(exc)) from exc
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)
    if key == "whisper_model":
        return _model_name(value)
    raise AppError("Configuração desconhecida. Use theme, color_filter, font_scale, output_dir ou whisper_model.")


def _output_dir() -> Path:
    db = _db()
    try:
        raw = db.get_setting("output_dir")
    finally:
        db.close()
    path = Path(raw) if raw else app_data_dir() / "saidas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_text(raw: str) -> tuple[Path, str]:
    from congo_grey_parrot.documents.service import read_document

    path = local_path(raw, TEXT_SUFFIXES)
    if not path.is_file():
        raise AppError(f"Não achei o arquivo: {path}")
    if path.stat().st_size > MAX_TEXT_FILE_BYTES:
        raise AppError("O arquivo passa de 20 MB.")
    return path, read_document(path)


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sentences(value) -> int:
    return max(0, min(30, _int(value, 0)))


def self_entry() -> dict:
    """Como um cliente MCP abre este servidor: pelo Flatpak instalado ou pelo comando ao lado deste Python."""
    import os
    import shutil
    import sys

    flatpak_id = os.environ.get("FLATPAK_ID", "")
    if flatpak_id:
        return {"command": "flatpak", "args": ["run", "--command=congo-grey-parrot-mcp", flatpak_id]}
    beside = Path(sys.executable).with_name("congo-grey-parrot-mcp")
    if beside.is_file():
        return {"command": str(beside)}
    found = shutil.which("congo-grey-parrot-mcp")
    if found:
        return {"command": found}
    return {"command": sys.executable, "args": ["-m", "congo_grey_parrot.mcp_server"]}


def main() -> None:
    serve(build_server(), default_port=8765)


if __name__ == "__main__":
    main()
