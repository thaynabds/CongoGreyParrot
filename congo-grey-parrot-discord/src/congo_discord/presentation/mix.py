from __future__ import annotations

import discord

from congo_discord.domain.audio_pcm import mix_s16le


class LayeredSource(discord.AudioSource):
    def __init__(self, background: discord.AudioSource, effect: discord.AudioSource):
        self.background = background
        self.effect: discord.AudioSource | None = effect

    def read(self) -> bytes:
        base = self.background.read()
        if not base:
            return b""
        if self.effect is None:
            return base
        extra = self.effect.read()
        if not extra:
            self.effect = None
            return base
        return mix_s16le(base, extra)

    def is_opus(self) -> bool:
        return False
