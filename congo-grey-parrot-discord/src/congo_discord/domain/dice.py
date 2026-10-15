from __future__ import annotations

import random
import re
from dataclasses import dataclass

_TOKEN = re.compile(r"([+-]?)(?:(\d*)d(\d+)|(\d+))", re.IGNORECASE)
_MAX_DICE = 40
_MAX_SIDES = 1000


@dataclass(frozen=True)
class RollResult:
    expression: str
    total: int
    detail: str


def _rng(source: random.Random | None) -> random.Random:
    return source or random.Random()


def roll_expression(expression: str, source: random.Random | None = None) -> RollResult:
    text = expression.replace(" ", "")
    matches = list(_TOKEN.finditer(text))
    if not text or not matches or "".join(match.group(0) for match in matches) != text:
        raise ValueError("Use uma expressão como 1d20+5 ou 2d6+1d4.")
    rng = _rng(source)
    total = 0
    parts: list[str] = []
    for match in matches:
        sign = -1 if match.group(1) == "-" else 1
        if match.group(3):
            count = int(match.group(2) or "1")
            sides = int(match.group(3))
            if count < 1 or count > _MAX_DICE or sides < 2 or sides > _MAX_SIDES:
                raise ValueError("Cada grupo aceita de 1 a 40 dados, com 2 a 1000 faces.")
            rolls = [rng.randint(1, sides) for _ in range(count)]
            subtotal = sign * sum(rolls)
            total += subtotal
            shown = "+".join(str(item) for item in rolls)
            parts.append(f"{'-' if sign < 0 else ''}{count}d{sides} ({shown})")
        else:
            flat = sign * int(match.group(4))
            total += flat
            parts.append(str(flat))
    return RollResult(text, total, " ".join(parts))


def roll_pair(expression: str, source: random.Random | None = None) -> tuple[RollResult, RollResult]:
    rng = _rng(source)
    return roll_expression(expression, rng), roll_expression(expression, rng)


def roll_percent(skill: int, source: random.Random | None = None) -> RollResult:
    if skill < 1 or skill > 100:
        raise ValueError("A perícia fica entre 1 e 100.")
    rolled = _rng(source).randint(1, 100)
    if rolled == 1 or rolled <= max(1, skill // 5):
        label = "sucesso decisivo"
    elif rolled <= skill:
        label = "sucesso"
    elif rolled >= 96:
        label = "falha grave"
    else:
        label = "falha"
    return RollResult(f"1d100 contra {skill}", rolled, label)


def roll_pool(count: int, faces: int, success_from: int, source: random.Random | None = None) -> RollResult:
    if count < 1 or count > _MAX_DICE or faces < 2 or faces > _MAX_SIDES:
        raise ValueError("O grupo aceita de 1 a 40 dados, com 2 a 1000 faces.")
    if success_from < 1 or success_from > faces:
        raise ValueError("O número de sucesso precisa caber nas faces do dado.")
    rolls = [_rng(source).randint(1, faces) for _ in range(count)]
    successes = sum(1 for item in rolls if item >= success_from)
    shown = ", ".join(str(item) for item in rolls)
    return RollResult(f"{count}d{faces} a partir de {success_from}", successes, shown)
