from __future__ import annotations

from congo_discord.domain.audio_pcm import pcm48_stereo_to_pcm16_mono, wav_bytes


class MeetingAudio:
    def __init__(self) -> None:
        self._mono: dict[str, bytearray] = {}

    def add(self, speaker: str, pcm48_stereo: bytes) -> None:
        mono = pcm48_stereo_to_pcm16_mono(pcm48_stereo)
        if not mono:
            return
        self._mono.setdefault(speaker, bytearray()).extend(mono)

    def flush(self, min_seconds: float = 3) -> list[tuple[str, bytes]]:
        need = int(min_seconds * 16000) * 2
        ready: list[tuple[str, bytes]] = []
        for speaker, data in list(self._mono.items()):
            if len(data) < need:
                continue
            ready.append((speaker, wav_bytes(bytes(data))))
            self._mono[speaker] = bytearray()
        return ready
