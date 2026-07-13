# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
import math

from app_errors import unmanaged_diagnostic
from p03_iso_generator.apt_parser import csv_tokens
from p03_iso_generator.geometric_calculations import (
    build_point_from_plane as geometry_build_point_from_plane,
    ccw_tangent_vector as geometry_ccw_tangent_vector,
    cw_tangent_vector as geometry_cw_tangent_vector,
    project_point_to_plane as geometry_project_point_to_plane,
)
from p03_iso_generator.iso_writer import IsoWriter
from p03_iso_generator.machine_state import WriterState
from p01_machines_config.machine_enums import MotionMode


@dataclass
class HelicalMoveDefinition:
    """Definition normalisee d'un mouvement HELICAL CATIA."""

    center_x: float
    center_y: float
    center_z: float
    tangent_x: float
    tangent_y: float
    tangent_z: float
    axis_i: float
    axis_j: float
    axis_k: float
    pitch: float
    radius: float
    angle: float
    height: float
    round_count: float
    end_x: float
    end_y: float
    end_z: float
    raw_argument_text: str


@dataclass
class HelicalMoveSegment:
    """Segment ISO elementaire d'un HELICAL CATIA."""

    end_x: float
    end_y: float
    end_z: float


@dataclass
class HelicalMoveSolution:
    """Resultat geometrique d'un HELICAL pret a etre emis en ISO."""

    work_plane_name: str
    work_plane_code: str
    motion_code: str
    center_x: float
    center_y: float
    center_z: float
    segments: list[HelicalMoveSegment]


def emit_helical_not_supported(argument_text: str, iso_writer: IsoWriter, reason: str | None = None) -> None:
    """Centralise les messages de non-support pour HELICAL."""
    iso_writer.comment(unmanaged_diagnostic("HELICAL", argument_text, reason))


def _rotate_coordinates_around_z(position_x: float, position_y: float, position_z: float, angle_degrees: float) -> tuple[float, float, float]:
    """Applique une rotation aux coordonnees dans le plan XY."""
    angle_radians = math.radians(angle_degrees)
    rotated_x = position_x * math.cos(angle_radians) - position_y * math.sin(angle_radians)
    rotated_y = position_x * math.sin(angle_radians) + position_y * math.cos(angle_radians)
    return rotated_x, rotated_y, position_z


def _transform_helical_definition_to_current_c(definition: HelicalMoveDefinition, position_c: float) -> HelicalMoveDefinition:
    """Transforme les coordonnees/vecteurs APT d'une helice dans le repere ISO courant."""
    center_x, center_y, center_z = _rotate_coordinates_around_z(
        definition.center_x,
        definition.center_y,
        definition.center_z,
        -position_c,
    )
    tangent_x, tangent_y, tangent_z = _rotate_coordinates_around_z(
        definition.tangent_x,
        definition.tangent_y,
        definition.tangent_z,
        -position_c,
    )
    axis_i, axis_j, axis_k = _rotate_coordinates_around_z(
        definition.axis_i,
        definition.axis_j,
        definition.axis_k,
        -position_c,
    )
    end_x, end_y, end_z = _rotate_coordinates_around_z(
        definition.end_x,
        definition.end_y,
        definition.end_z,
        -position_c,
    )

    return HelicalMoveDefinition(
        center_x=center_x,
        center_y=center_y,
        center_z=center_z,
        tangent_x=tangent_x,
        tangent_y=tangent_y,
        tangent_z=tangent_z,
        axis_i=axis_i,
        axis_j=axis_j,
        axis_k=axis_k,
        pitch=definition.pitch,
        radius=definition.radius,
        angle=definition.angle,
        height=definition.height,
        round_count=definition.round_count,
        end_x=end_x,
        end_y=end_y,
        end_z=end_z,
        raw_argument_text=definition.raw_argument_text,
    )


def _constant_coordinate_from_plane(work_plane: str, point_x: float, point_y: float, point_z: float) -> float:
    """Retourne la coordonnee hors plan d'un point 3D."""
    if work_plane == "XY":
        return point_z
    if work_plane == "XZ":
        return point_y
    return point_x


def _rotation_sign_for_motion(work_plane: str, motion_code: str, iso_writer: IsoWriter) -> float:
    """Retourne le signe de rotation 2D correspondant au code ISO dans le plan courant."""
    if work_plane == "XZ":
        return 1.0 if motion_code == iso_writer.machine.circular_move_CW_code else -1.0
    return -1.0 if motion_code == iso_writer.machine.circular_move_CW_code else 1.0


def _build_helical_segments(
    definition: HelicalMoveDefinition,
    work_plane: str,
    motion_code: str,
    start_x: float,
    start_y: float,
    start_z: float,
    center_u: float,
    center_v: float,
    radial_u: float,
    radial_v: float,
    tolerance: float,
    iso_writer: IsoWriter,
) -> list[HelicalMoveSegment]:
    """Decoupe une helice CATIA en arcs ISO de 360 deg maximum."""
    total_angle = abs(definition.angle)
    full_turn_count = int(total_angle // 360.0)
    remaining_angle = total_angle - full_turn_count * 360.0
    if remaining_angle <= tolerance:
        remaining_angle = 0.0

    signed_rotation = _rotation_sign_for_motion(work_plane, motion_code, iso_writer)
    start_constant = _constant_coordinate_from_plane(work_plane, start_x, start_y, start_z)
    end_constant = _constant_coordinate_from_plane(work_plane, definition.end_x, definition.end_y, definition.end_z)
    segments: list[HelicalMoveSegment] = []

    angle_done = 0.0
    for _ in range(full_turn_count):
        angle_done += 360.0
        progress = angle_done / total_angle
        constant_value = start_constant + (end_constant - start_constant) * progress
        end_x, end_y, end_z = geometry_build_point_from_plane(
            work_plane,
            center_u + radial_u,
            center_v + radial_v,
            constant_value,
        )
        segments.append(HelicalMoveSegment(end_x=end_x, end_y=end_y, end_z=end_z))

    if remaining_angle > 0.0:
        angle_done += remaining_angle
        angle_radians = math.radians(remaining_angle * signed_rotation)
        rotated_u = radial_u * math.cos(angle_radians) - radial_v * math.sin(angle_radians)
        rotated_v = radial_u * math.sin(angle_radians) + radial_v * math.cos(angle_radians)
        progress = angle_done / total_angle
        constant_value = start_constant + (end_constant - start_constant) * progress
        end_x, end_y, end_z = geometry_build_point_from_plane(
            work_plane,
            center_u + rotated_u,
            center_v + rotated_v,
            constant_value,
        )
        segments.append(HelicalMoveSegment(end_x=end_x, end_y=end_y, end_z=end_z))

    if segments:
        segments[-1] = HelicalMoveSegment(
            end_x=definition.end_x,
            end_y=definition.end_y,
            end_z=definition.end_z,
        )

    return segments


def parse_helical_definition(argument_text: str) -> HelicalMoveDefinition | None:
    """Parse HELICAL/CENTER,...,END,... et retourne une definition normalisee."""
    # Definition CATIA V5 prise en charge ici :
    # HELICAL/CENTER, Xc, Yc, Zc,
    # INDIRV, I, J, K,
    # AXIS, Ia, Ja, Ka,
    # PITCH, Pitch,
    # RADIUS, Rad,
    # ANGLE, Angle,
    # HEIGHT, Height,
    # ROUND, Round,
    # END, Xe, Ye, Ze
    tokens = csv_tokens(argument_text)
    if len(tokens) != 26:
        return None

    if (
        tokens[0].upper() != "CENTER"
        or tokens[4].upper() != "INDIRV"
        or tokens[8].upper() != "AXIS"
        or tokens[12].upper() != "PITCH"
        or tokens[14].upper() != "RADIUS"
        or tokens[16].upper() != "ANGLE"
        or tokens[18].upper() != "HEIGHT"
        or tokens[20].upper() != "ROUND"
        or tokens[22].upper() != "END"
    ):
        return None

    try:
        return HelicalMoveDefinition(
            center_x=float(tokens[1]),
            center_y=float(tokens[2]),
            center_z=float(tokens[3]),
            tangent_x=float(tokens[5]),
            tangent_y=float(tokens[6]),
            tangent_z=float(tokens[7]),
            axis_i=float(tokens[9]),
            axis_j=float(tokens[10]),
            axis_k=float(tokens[11]),
            pitch=float(tokens[13]),
            radius=float(tokens[15]),
            angle=float(tokens[17]),
            height=float(tokens[19]),
            round_count=float(tokens[21]),
            end_x=float(tokens[23]),
            end_y=float(tokens[24]),
            end_z=float(tokens[25]),
            raw_argument_text=argument_text,
        )
    except ValueError:
        return None


def solve_helical_definition(definition: HelicalMoveDefinition, state: WriterState, iso_writer: IsoWriter) -> HelicalMoveSolution | None:
    """Resout un HELICAL si son axe est aligne avec l'axe outil et un plan machine."""
    if not state.tool.number:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "outil courant absent")
        return None

    tolerance = float(iso_writer.machine.calculation_tolerance)
    if abs(definition.angle) <= tolerance:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "angle HELICAL nul")
        return None

    transformed_definition = _transform_helical_definition_to_current_c(definition, state.position_c)

    tool_config = iso_writer.machine.get_required_tool_config(state.tool.number)
    tool_axis_vector = tool_config.get("workplane")
    if not isinstance(tool_axis_vector, (list, tuple)) or len(tool_axis_vector) != 3:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "axe outil JSON invalide")
        return None

    axis_i = abs(transformed_definition.axis_i)
    axis_j = abs(transformed_definition.axis_j)
    axis_k = abs(transformed_definition.axis_k)
    tool_axis_i = abs(float(tool_axis_vector[0]))
    tool_axis_j = abs(float(tool_axis_vector[1]))
    tool_axis_k = abs(float(tool_axis_vector[2]))
    if (
        abs(axis_i - tool_axis_i) > tolerance
        or abs(axis_j - tool_axis_j) > tolerance
        or abs(axis_k - tool_axis_k) > tolerance
    ):
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "axe HELICAL different de l'axe outil")
        return None

    work_plane, work_plane_code = iso_writer.machine.get_tool_geometry_work_plane(state.tool.number)
    axis_matches_work_plane = (
        (work_plane == "XY" and axis_i <= tolerance and axis_j <= tolerance and abs(axis_k - 1.0) <= tolerance)
        or (work_plane == "XZ" and axis_i <= tolerance and abs(axis_j - 1.0) <= tolerance and axis_k <= tolerance)
        or (work_plane == "YZ" and abs(axis_i - 1.0) <= tolerance and axis_j <= tolerance and axis_k <= tolerance)
    )
    if not axis_matches_work_plane:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, f"axe HELICAL hors plan machine {work_plane_code}")
        return None

    start_u, start_v = geometry_project_point_to_plane(work_plane, state.position_x, state.position_y, state.position_z)
    center_u, center_v = geometry_project_point_to_plane(
        work_plane,
        transformed_definition.center_x,
        transformed_definition.center_y,
        transformed_definition.center_z,
    )
    end_u, end_v = geometry_project_point_to_plane(
        work_plane,
        transformed_definition.end_x,
        transformed_definition.end_y,
        transformed_definition.end_z,
    )

    start_radius = ((start_u - center_u) ** 2 + (start_v - center_v) ** 2) ** 0.5
    end_radius = ((end_u - center_u) ** 2 + (end_v - center_v) ** 2) ** 0.5
    if abs(start_radius - definition.radius) > tolerance or abs(end_radius - definition.radius) > tolerance:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "rayon HELICAL incoherent")
        return None

    radial_u = start_u - center_u
    radial_v = start_v - center_v
    if work_plane == "XY":
        tangent_u = transformed_definition.tangent_x
        tangent_v = transformed_definition.tangent_y
    elif work_plane == "XZ":
        tangent_u = transformed_definition.tangent_x
        tangent_v = transformed_definition.tangent_z
    else:
        tangent_u = transformed_definition.tangent_y
        tangent_v = transformed_definition.tangent_z

    cw_tangent_u, cw_tangent_v = geometry_cw_tangent_vector(work_plane, radial_u, radial_v)
    ccw_tangent_u, ccw_tangent_v = geometry_ccw_tangent_vector(work_plane, radial_u, radial_v)
    cw_alignment = cw_tangent_u * tangent_u + cw_tangent_v * tangent_v
    ccw_alignment = ccw_tangent_u * tangent_u + ccw_tangent_v * tangent_v
    motion_code = iso_writer.machine.circular_move_CW_code if cw_alignment >= ccw_alignment else iso_writer.machine.circular_move_CCW_code
    segments = _build_helical_segments(
        transformed_definition,
        work_plane,
        motion_code,
        state.position_x,
        state.position_y,
        state.position_z,
        center_u,
        center_v,
        radial_u,
        radial_v,
        tolerance,
        iso_writer,
    )
    if not segments:
        emit_helical_not_supported(definition.raw_argument_text, iso_writer, "segments HELICAL absents")
        return None

    return HelicalMoveSolution(
        work_plane_name=work_plane,
        work_plane_code=work_plane_code,
        motion_code=motion_code,
        center_x=transformed_definition.center_x,
        center_y=transformed_definition.center_y,
        center_z=transformed_definition.center_z,
        segments=segments,
    )


def emit_helical_move(solution: HelicalMoveSolution, state: WriterState, iso_writer: IsoWriter) -> None:
    """Emet un HELICAL sous forme d'arc ISO avec deplacement simultane sur l'axe hors plan."""
    state.motion_mode = MotionMode.WORKING

    for segment in solution.segments:
        state.position_x = segment.end_x
        state.position_y = segment.end_y
        state.position_z = segment.end_z

        iso_writer.circular_move(
            solution.work_plane_code,
            solution.motion_code,
            state.feedrate_value,
            state.feedrate_unit,
            solution.center_x,
            solution.center_y,
            solution.center_z,
            position_x=segment.end_x,
            position_y=segment.end_y,
            position_z=segment.end_z,
        )
