# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from d_iso_generator.parameters_enums import FeedrateUnit, MotionMode, SpindleDirection, SpindleUnit, ToolType


@dataclass
class MachineState:
    """L'etat courant de la machine tel que "vu" par le post-processeur."""

    motion_mode: MotionMode = MotionMode.RAPID
    channel_identifier: Optional[int] = None

    feedrate_value: Optional[float] = None
    feedrate_unit: Optional[FeedrateUnit] = None
    spindle_speed: Optional[float] = None
    spindle_unit: Optional[SpindleUnit] = None
    spindle_direction: Optional[SpindleDirection] = None
    spindle_on: bool = False
    
    tool_number: Optional[int] = None
    tool_type: Optional[ToolType] = None
    coolant_on: bool = False

    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0

    indirv_x: Optional[float] = None
    indirv_y: Optional[float] = None
    indirv_z: Optional[float] = None

    bloc_number: int = 0
    line_number: int = 0
