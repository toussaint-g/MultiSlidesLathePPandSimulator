# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from typing import TypeAlias


JsonDict: TypeAlias = dict[str, object]


def normalize_gm_code(code):
    """Normalise un code G/M numerique (ex: G00 -> G0, M06 -> M6)."""
    normalized_code = code.strip().upper()
    prefix = ""
    number = ""
    for character in normalized_code:
        if character.isalpha() and number == "":
            prefix += character
        else:
            number += character
    if not prefix or not number.isdigit():
        return normalized_code
    return f"{prefix}{int(number)}"


@dataclass
class MachineParameters:
    """Regroupe les donnees utiles extraites du JSON machine pour un canal."""

    channel_name: str
    calculation_tolerance: float
    rapidfeedrate: float
    change_tool_time: float
    x_diameter: bool
    rapid_move_code: str
    linear_move_code: str
    circular_move_CW_code: str
    circular_move_CCW_code: str
    timer_code: str
    toolname_prefix: str
    spindle_speed_prefix: str
    program_prefix: str
    feedrate_prefix: str
    feedrate_per_minute: str
    feedrate_per_revolution: str
    coolant_start_code: str | None
    coolant_stop_code: str | None
    endprogram_code: str
    startandendfile_character: str
    block_prefix: str
    block_increment: int
    xy_work_plane_code: str
    xz_work_plane_code: str
    yz_work_plane_code: str
    default_work_plane: str | None
    home_tool_x: float
    home_tool_y: float
    home_tool_z: float
    channel_tools: list[JsonDict]
    ipartvector: list[float] | None
    jpartvector: list[float] | None
    kpartvector: list[float] | None
    ipathvector: list[float] | None
    jpathvector: list[float] | None
    kpathvector: list[float] | None

    @classmethod
    def from_machine_config(cls, machine_config: JsonDict, *, home_x_mode: str = "machine") -> "MachineParameters":
        """Construit les parametres a partir du premier canal disponible."""
        try:
            channel_name = next(iter(machine_config["channelslist"]))
        except StopIteration:
            raise ValueError("MachineConfigError: aucun canal n'est defini dans le fichier JSON")
        return cls.from_config(machine_config, channel_name, home_x_mode=home_x_mode)

    @classmethod
    def from_config(machine_parameters_builder, machine_config: JsonDict, channel_name: str, *, home_x_mode: str = "machine") -> "MachineParameters":
        """Construit les parametres machine/canal a partir du JSON charge."""
        try:
            machine_informations: JsonDict = machine_config["machineinformations"]  # type: ignore[assignment]
            channels_list: JsonDict = machine_config["channelslist"]  # type: ignore[assignment]
            channel_config: JsonDict = channels_list[channel_name]  # type: ignore[index]
            home_tool_x = channel_config["hometool"]["x"]
            x_diameter = machine_informations["xdiameter"]
            if x_diameter:
                if home_x_mode == "machine":
                    home_tool_x = home_tool_x * 2
                elif home_x_mode == "part":
                    home_tool_x = home_tool_x / 2

            coolant_start_code = machine_informations.get("coolantstart")
            coolant_stop_code = machine_informations.get("coolantstop")

            return machine_parameters_builder(
                channel_name=channel_name,
                calculation_tolerance=machine_config["calculationtolerance"],
                rapidfeedrate=machine_informations["rapidfeedrate"],
                change_tool_time=machine_informations["changetooltime"],
                x_diameter=x_diameter,
                rapid_move_code=normalize_gm_code(machine_informations["rapidmove"]),
                linear_move_code=normalize_gm_code(machine_informations["linearmove"]),
                circular_move_CW_code=normalize_gm_code(machine_informations["circularmoveCW"]),
                circular_move_CCW_code=normalize_gm_code(machine_informations["circularmoveCCW"]),
                timer_code=normalize_gm_code(machine_informations["timer"]),
                toolname_prefix=machine_informations["toolnameprefix"],
                spindle_speed_prefix=machine_informations["spindlespeedprefix"],
                program_prefix=machine_informations["programprefix"],
                feedrate_prefix=machine_informations["feedrateprefix"],
                feedrate_per_minute=normalize_gm_code(machine_informations["feedrateperminute"]),
                feedrate_per_revolution=normalize_gm_code(machine_informations["feedrateperrevolution"]),
                coolant_start_code=normalize_gm_code(coolant_start_code) if coolant_start_code else None,
                coolant_stop_code=normalize_gm_code(coolant_stop_code) if coolant_stop_code else None,
                endprogram_code=normalize_gm_code(machine_informations["endprogram"]),
                startandendfile_character=machine_informations["startandendfilecharacter"],
                block_prefix=machine_informations["blockprefix"],
                block_increment=machine_informations["blockincrement"],
                xy_work_plane_code=normalize_gm_code(machine_informations["xyworkplane"]),
                xz_work_plane_code=normalize_gm_code(machine_informations["xzworkplane"]),
                yz_work_plane_code=normalize_gm_code(machine_informations["yzworkplane"]),
                default_work_plane=normalize_gm_code(machine_informations["defaultworkplane"]) if machine_informations.get("defaultworkplane") else None,
                home_tool_x=home_tool_x,
                home_tool_y=channel_config["hometool"]["y"],
                home_tool_z=channel_config["hometool"]["z"],
                channel_tools=channel_config["listoftools"],
                ipartvector=machine_informations.get("ipartvector"),
                jpartvector=machine_informations.get("jpartvector"),
                kpartvector=machine_informations.get("kpartvector"),
                ipathvector=channel_config.get("ipathvector"),
                jpathvector=channel_config.get("jpathvector"),
                kpathvector=channel_config.get("kpathvector"),
            )
        except KeyError:
            raise ValueError("MachineConfigError: une cle est absente dans le fichier JSON")
