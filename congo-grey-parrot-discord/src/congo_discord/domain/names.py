from __future__ import annotations

import random

_STARTS = ("br", "cal", "dor", "el", "fen", "gar", "hal", "iv", "jor", "ka", "lor", "mir", "nor", "or", "pel", "quin", "rin", "sar", "tor", "ul")
_ENDS = ("a", "en", "ic", "len", "mir", "os", "ryn", "th", "us", "wen", "ya")
_PLACES = ("ponte", "porto", "vale", "torre", "bosque", "mercado", "cais", "forja")
_THINGS = ("lanterna", "chave", "mapa", "anel", "carta", "moeda", "corda", "flauta")


def fantasy_name(kind: str, source: random.Random | None = None) -> str:
    rng = source or random.Random()
    person = rng.choice(_STARTS).capitalize() + rng.choice(_ENDS)
    if kind == "taverna":
        return f"{rng.choice(_PLACES).capitalize()} {rng.choice(_THINGS)}"
    if kind == "boato":
        return f"Dizem que {person} escondeu um {rng.choice(_THINGS)} no {rng.choice(_PLACES)}."
    return person
