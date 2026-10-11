from __future__ import annotations

from dataclasses import dataclass

from congo_grey_parrot.core.errors import AppError


@dataclass
class TranscribeOptions:
    model: str = "tiny"
    language: str | None = None
    task: str = "transcribe"
    device: str = "cpu"
    beam_size: int = 5
    temperature: float = 0.0
    condition_on_previous_text: bool = True
    word_timestamps: bool = True
    initial_prompt: str | None = None
    clip_start: float | None = None
    clip_end: float | None = None
    highlight_words: bool = False
    max_line_width: int | None = None
    max_line_count: int | None = None
    max_words_per_line: int | None = None


def validate_options(options: TranscribeOptions) -> None:
    if options.task not in {"transcribe", "translate"}:
        raise AppError("Tarefa desconhecida.")
    english_only = options.model.endswith(".en")
    if options.task == "translate" and (options.model == "turbo" or english_only):
        raise AppError(
            "A tradução de fala para inglês precisa de um modelo multilíngue. "
            "O turbo e os modelos .en não fazem essa tarefa."
        )
    if english_only and options.language not in {None, "en"}:
        raise AppError("Este modelo reconhece só inglês. Escolha inglês ou outro modelo.")
    if (
        options.clip_start is not None
        and options.clip_end is not None
        and options.clip_end <= options.clip_start
    ):
        raise AppError("O fim do trecho precisa ser maior que o início.")
    if options.beam_size < 1:
        raise AppError("O feixe de busca precisa ser pelo menos 1.")
