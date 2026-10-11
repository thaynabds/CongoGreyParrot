from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.files.naming import prepare_output

AUDIO_CODECS = {
    ".wav": ["-vn", "-c:a", "pcm_s16le"],
    ".mp3": ["-vn", "-c:a", "libmp3lame"],
    ".ogg": ["-vn", "-c:a", "libvorbis"],
    ".flac": ["-vn", "-c:a", "flac"],
    ".m4a": ["-vn", "-c:a", "aac"],
    ".aac": ["-vn", "-c:a", "aac"],
}

VIDEO_CODECS = {
    ".mp4": ["-c:v", "libx264", "-c:a", "aac"],
    ".mkv": ["-c:v", "libx264", "-c:a", "aac"],
    ".webm": ["-c:v", "libvpx-vp9", "-c:a", "libopus"],
    ".mov": ["-c:v", "libx264", "-c:a", "aac"],
    ".avi": ["-c:v", "mpeg4", "-c:a", "mp3"],
}


def ffmpeg_hint() -> str:
    return (
        "O FFmpeg não está instalado. No Ubuntu, Debian ou Linux Mint: sudo apt install ffmpeg. "
        "No Windows, o instalador está em https://ffmpeg.org/download.html"
    )


def find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def escape_filter_path(path: Path) -> str:
    text = path.resolve().as_posix().replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'")
    return text


def build_convert_command(
    ffmpeg: str,
    source: Path,
    target: Path,
    bitrate_k: int | None = None,
) -> list[str]:
    if not source.is_file():
        raise AppError("Arquivo de origem não encontrado.")
    suffix = target.suffix.lower()
    if suffix in AUDIO_CODECS:
        codec = list(AUDIO_CODECS[suffix])
    elif suffix in VIDEO_CODECS:
        codec = list(VIDEO_CODECS[suffix])
    else:
        raise AppError("Formato de saída não suportado por este conversor.")
    command = [ffmpeg, "-y", "-i", str(source), *codec]
    if bitrate_k and bitrate_k > 0 and suffix in AUDIO_CODECS:
        command.extend(["-b:a", f"{int(bitrate_k)}k"])
    if bitrate_k and bitrate_k > 0 and suffix in VIDEO_CODECS:
        command.extend(["-b:v", f"{int(bitrate_k)}k"])
    command.append(str(target))
    return command


def build_burn_command(ffmpeg: str, video: Path, subtitle: Path, target: Path) -> list[str]:
    if not video.is_file():
        raise AppError("Vídeo não encontrado.")
    if not subtitle.is_file():
        raise AppError("Legenda não encontrada.")
    escaped = escape_filter_path(subtitle)
    return [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vf",
        f"subtitles='{escaped}'",
        "-c:a",
        "copy",
        str(target),
    ]


def run_command(command: list[str]) -> None:
    if not command or (shutil.which(command[0]) is None and not Path(command[0]).is_file()):
        raise AppError(ffmpeg_hint())
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        tail = detail[-1200:] if detail else "O FFmpeg encerrou com erro."
        raise AppError(tail)


class FfmpegService:
    def convert(self, source: Path, target: Path, bitrate_k: int | None = None) -> Path:
        binary = find_ffmpeg()
        if not binary:
            raise AppError(ffmpeg_hint())
        destination = prepare_output(target)
        run_command(build_convert_command(binary, source, destination, bitrate_k))
        return destination

    def burn_subtitles(self, video: Path, subtitle: Path, target: Path) -> Path:
        binary = find_ffmpeg()
        if not binary:
            raise AppError(ffmpeg_hint())
        destination = prepare_output(target)
        run_command(build_burn_command(binary, video, subtitle, destination))
        return destination
