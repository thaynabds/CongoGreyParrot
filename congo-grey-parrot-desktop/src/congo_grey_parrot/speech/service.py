from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

from congo_grey_parrot.core.errors import AppError


def clamp_speed(speed: float) -> float:
    return min(2.0, max(0.5, float(speed)))


def clamp_pitch(pitch: float) -> float:
    return min(1.8, max(0.5, float(pitch)))


def piper_length_scale(speed: float) -> float:
    return 0.8 / clamp_speed(speed)


def espeak_command(binary: str, wav_path: Path, speed: float, pitch: float) -> list[str]:
    words_per_minute = max(80, min(450, int(round(175 * clamp_speed(speed)))))
    pitch_value = max(0, min(99, int(round(50 * clamp_pitch(pitch)))))
    return [binary, "-w", str(wav_path), "-s", str(words_per_minute), "-p", str(pitch_value), "--stdin"]


class SpeechService:
    def available_engines(self) -> list[str]:
        engines = []
        try:
            import piper  # noqa: F401

            engines.append("piper")
        except ImportError:
            pass
        if shutil.which("espeak-ng"):
            engines.append("espeak-ng")
        return engines

    def synthesize(
        self,
        text: str,
        wav_path: Path,
        speed: float = 1.0,
        pitch: float = 1.0,
        model_path: Path | None = None,
        config_path: Path | None = None,
        cancel=None,
    ) -> str:
        body = text.strip()
        if not body:
            raise AppError("Digite ou abra um texto antes de gerar o áudio.")
        if cancel is not None and cancel.is_set():
            raise AppError("Operação cancelada.")
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        if model_path and model_path.is_file() and "piper" in self.available_engines():
            self._piper(body, wav_path, speed, pitch, model_path, config_path)
            return "piper"
        binary = shutil.which("espeak-ng")
        if binary:
            self._espeak(binary, body, wav_path, speed, pitch)
            return "espeak-ng"
        if model_path and model_path.is_file():
            raise AppError(
                "A voz está no disco, mas a biblioteca Piper não está instalada. "
                "Execute: pip install piper-tts"
            )
        raise AppError(
            "Nenhum motor de voz está disponível. Baixe uma voz Piper e instale piper-tts, "
            "ou instale o espeak-ng no sistema."
        )

    def _piper(self, text: str, wav_path: Path, speed: float, pitch: float, model: Path, config: Path | None) -> None:
        from piper import PiperVoice

        try:
            voice = PiperVoice.load(str(model))
        except TypeError:
            voice = PiperVoice.load(str(model), str(config) if config else None)
        factor = clamp_pitch(pitch)
        if abs(factor - 1.0) >= 0.01 and hasattr(voice, "config"):
            voice.config.sample_rate = int(round(voice.config.sample_rate * factor))
        with wave.open(str(wav_path), "wb") as wav_file:
            try:
                from piper import SynthesisConfig

                syn = SynthesisConfig(length_scale=piper_length_scale(speed))
                voice.synthesize_wav(text, wav_file, syn_config=syn)
            except TypeError:
                voice.synthesize_wav(text, wav_file)

    def _espeak(self, binary: str, text: str, wav_path: Path, speed: float, pitch: float) -> None:
        command = espeak_command(binary, wav_path, speed, pitch)
        completed = subprocess.run(command, input=text.encode("utf-8"), capture_output=True, check=False)
        if completed.returncode != 0 or not wav_path.is_file():
            detail = completed.stderr.decode("utf-8", errors="replace")[-800:]
            raise AppError(detail or "O espeak-ng não gerou o áudio.")
