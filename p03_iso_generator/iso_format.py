# -*- coding: utf-8 -*-

from __future__ import annotations


def format_float_to_iso(numeric_value: float) -> str:
    """Formatte un nombre ISO avec un point final pour les entiers."""
    formatted_value = f"{numeric_value:.3f}".rstrip("0").rstrip(".")
    if "." not in formatted_value:
        return formatted_value + "."
    return formatted_value
