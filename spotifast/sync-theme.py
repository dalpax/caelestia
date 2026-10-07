#!/usr/bin/env python3
"""Render Caelestia's current colour scheme as a Spotifast palette."""

import json
import os
from pathlib import Path
import re
import tempfile


def xdg_path(variable, fallback):
    return Path(os.environ.get(variable, Path.home() / fallback))


scheme_path = xdg_path("XDG_STATE_HOME", ".local/state") / "caelestia/scheme.json"
theme_dir = xdg_path("XDG_CONFIG_HOME", ".config") / "spotifast/themes"
theme_path = theme_dir / "Caelestia.json"


def render(scheme):
    colours = scheme["colours"]

    def colour(name):
        value = colours[name]
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
            raise ValueError(f"Invalid Caelestia colour: {name}")
        return f"#{value.lower()}"

    if scheme["mode"] not in ("dark", "light"):
        raise ValueError("Invalid Caelestia mode")

    return {
        "base": scheme["mode"],
        "colors": {
            "window": colour("background"),
            "panel": colour("surfaceContainer"),
            "surface": colour("surfaceContainerHigh"),
            "surface_hover": colour("surfaceContainerHighest"),
            "surface_active": colour("surfaceVariant"),
            "outline": colour("outlineVariant"),
            "text": colour("onSurface"),
            "secondary": colour("onSurfaceVariant"),
            "dim": colour("outline"),
            "accent": colour("primary"),
            "accent_hover": colour("primaryDim") if "primaryDim" in colours else colour("primaryFixed"),
            "on_accent": colour("onPrimary"),
            "danger": colour("error"),
            "warning": colour("tertiary"),
            "shadow": colour("shadow"),
        },
    }


def main():
    palette = render(json.loads(scheme_path.read_text(encoding="utf-8")))
    content = json.dumps(palette, indent=2) + "\n"
    theme_dir.mkdir(parents=True, exist_ok=True)
    if theme_path.exists() and theme_path.read_text(encoding="utf-8") == content:
        return
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=theme_dir,
                                     prefix=".Caelestia-", suffix=".json", delete=False) as stream:
        temp_path = Path(stream.name)
        stream.write(content)
    try:
        temp_path.replace(theme_path)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
