from __future__ import annotations

from congo_grey_parrot.core.errors import AppError


class TranslationService:
    """Tradução de texto. A fala para inglês fica no motor Whisper, não aqui."""

    def engine_name(self) -> str:
        try:
            import argostranslate.translate  # noqa: F401
        except ImportError:
            return ""
        return "argos"

    def translate(self, text: str, source: str, target: str) -> str:
        body = text.strip()
        if not body:
            raise AppError("Não há texto para traduzir.")
        if not source or not target:
            raise AppError("Escolha o idioma de origem e o de destino.")
        if source == target:
            return body
        if self.engine_name() == "":
            raise AppError(
                "Não há motor de tradução de texto instalado. "
                "A tradução de fala para inglês está em Transcrever, com um modelo multilíngue. "
                "Para traduzir texto offline, instale argostranslate e o pacote do par de idiomas."
            )
        import argostranslate.translate

        try:
            return argostranslate.translate.translate(body, source, target)
        except Exception as exc:
            raise AppError(
                "O Argos não concluiu a tradução. Confira se o pacote desse par de idiomas está instalado. "
                f"{exc}"
            ) from exc
