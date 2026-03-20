# -*- coding: utf-8 -*-

from enum import Enum


class FeedrateUnit(str, Enum):
    """Enum pour memoriser les unites d'avance autorisees."""
    MMPR = "MMPR"
    MMPM = "MMPM"


class MotionMode(str, Enum):
    """Enum pour memoriser les modes de mouvement autorises."""
    RAPID = "RAPID"
    WORKING = "WORKING"


class SpindleUnit(str, Enum):
    """Enum pour memoriser les unites de broche autorisees."""
    RPM = "RPM"
    SMM = "SMM"


class SpindleDirection(str, Enum):
    """Enum pour memoriser les sens de rotation de broche autorises."""
    CLW = "CLW"
    CCLW = "CCLW"

class ToolType(str, Enum):
    """Enum pour memoriser les types d'outil autorises."""
    TURN = "TURN"
    MILL = "MILL"
