from __future__ import annotations

import array
import io
import wave


def pcm48_stereo_to_pcm16_mono(pcm: bytes) -> bytes:
    usable = pcm[: len(pcm) - (len(pcm) % 4)]
    if len(usable) < 12:
        return b""
    samples = array.array("h")
    samples.frombytes(usable)
    mono = array.array("h", (samples[index] for index in range(0, len(samples) - 1, 6)))
    return mono.tobytes()


def rms(pcm16: bytes) -> float:
    usable = pcm16[: len(pcm16) - (len(pcm16) % 2)]
    if not usable:
        return 0.0
    samples = array.array("h")
    samples.frombytes(usable)
    total = sum(sample * sample for sample in samples)
    return (total / len(samples)) ** 0.5


def wav_bytes(pcm16_mono: bytes, rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm16_mono)
    return buffer.getvalue()


def mix_s16le(background: bytes, effect: bytes) -> bytes:
    if not effect:
        return background
    width = min(len(background), len(effect))
    width -= width % 2
    if width <= 0:
        return background
    left = array.array("h")
    right = array.array("h")
    left.frombytes(background[:width])
    right.frombytes(effect[:width])
    mixed = array.array(
        "h",
        (max(-32768, min(32767, left[index] + right[index])) for index in range(len(left))),
    )
    return mixed.tobytes() + background[width:]
