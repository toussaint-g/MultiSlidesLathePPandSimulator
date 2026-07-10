# -*- coding: utf-8 -*-

from __future__ import annotations


def format_float_to_iso(numeric_value: float, int_traitement: bool = True) -> str:
    """Formatte un nombre ISO avec un point final pour les entiers si int_traitement est True."""
    formatted_value = f"{numeric_value:.3f}".rstrip("0").rstrip(".")
    if int_traitement and "." not in formatted_value:
        return formatted_value + "."
    return formatted_value
