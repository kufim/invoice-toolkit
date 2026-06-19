from __future__ import annotations

THEMES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "Default": ((17, 18, 20), (17, 18, 20)),
    "Indigo": ((23, 26, 46), (79, 70, 229)),
    "Emerald": ((9, 32, 27), (16, 150, 105)),
    "Crimson": ((34, 14, 18), (201, 52, 62)),
    "Ocean": ((8, 30, 48), (14, 116, 160)),
    "Amber": ((33, 24, 10), (202, 138, 24)),
}
ORDER = ["Default", "Indigo", "Emerald", "Crimson", "Ocean", "Amber"]
DEFAULT = "Default"


def _lighten(color, amount=0.90):
    return tuple(int(c + (255 - c) * amount) for c in color)


def palette(name: str) -> dict:
    header, accent = THEMES.get(name, THEMES[DEFAULT])
    return {"header": header, "accent": accent, "soft": _lighten(accent)}


def hex_color(color) -> str:
    return "#%02x%02x%02x" % color