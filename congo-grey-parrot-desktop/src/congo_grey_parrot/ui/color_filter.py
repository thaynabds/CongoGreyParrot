from __future__ import annotations

import re

FILTERS = (
    "none",
    "invert",
    "smart_invert",
    "protanopia",
    "deuteranopia",
    "tritanopia",
    "grayscale",
)

# 3x3, linha = canal de saída. Deslocamento em 0..1.
# Protanopia, deuteranopia e tritanopia: modo Correction do Daltonizer
# do Android, nível máximo. A matriz final foi obtida da fórmula
# lms2rgb * (simulacao * rgb2lms + correcao * (rgb2lms - simulacao * rgb2lms)).
# https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/Effects/Daltonizer.cpp
# Monocromia: luminância da Rec. ITU-R BT.709.
# https://www.itu.int/rec/R-REC-BT.709
_MATRICES = {
    "invert": (
        ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        (1.0, 1.0, 1.0),
    ),
    "protanopia": (
        (
            (0.46111, 0.53889, 0.0),
            (0.37754, 0.62246, 0.0),
            (0.30974, -0.30974, 1.0),
        ),
        (0.0, 0.0, 0.0),
    ),
    "deuteranopia": (
        (
            (-0.01672, 1.01672, 0.0),
            (0.07530, 0.92470, 0.0),
            (-0.36845, 0.36845, 1.0),
        ),
        (0.0, 0.0, 0.0),
    ),
    "tritanopia": (
        (
            (1.0, -1.15102, 1.15102),
            (0.0, 0.11263, 0.88737),
            (0.0, 0.14975, 0.85025),
        ),
        (0.0, 0.0, 0.0),
    ),
    "grayscale": (
        (
            (0.2126, 0.7152, 0.0722),
            (0.2126, 0.7152, 0.0722),
            (0.2126, 0.7152, 0.0722),
        ),
        (0.0, 0.0, 0.0),
    ),
}


def map_color(name: str, red: float, green: float, blue: float) -> tuple[float, float, float]:
    item = _MATRICES.get(name)
    if item is None:
        return (red, green, blue)
    matrix, offset = item
    channels = (red, green, blue)
    out = []
    for row, shift in zip(matrix, offset):
        value = row[0] * channels[0] + row[1] * channels[1] + row[2] * channels[2] + shift
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        out.append(value)
    return (out[0], out[1], out[2])


def invert_hex_colors(stylesheet: str) -> str:
    def repl(match: re.Match[str]) -> str:
        text = match.group(1)
        red = 255 - int(text[0:2], 16)
        green = 255 - int(text[2:4], 16)
        blue = 255 - int(text[4:6], 16)
        return f"#{red:02x}{green:02x}{blue:02x}"

    return re.sub(r"#([0-9A-Fa-f]{6})", repl, stylesheet)


def android_color_matrix(name: str) -> list[float] | None:
    item = _MATRICES.get(name)
    if item is None:
        return None
    matrix, offset = item
    values: list[float] = []
    for row, shift in zip(matrix, offset):
        values.extend((row[0], row[1], row[2], 0.0, shift * 255.0))
    values.extend((0.0, 0.0, 0.0, 1.0, 0.0))
    return values
