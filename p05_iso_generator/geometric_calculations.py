# -*- coding: utf-8 -*-

import math


def line_circle_intersections_2d(line_start_u, line_start_v, line_end_u, line_end_v, center_u, center_v, radius):
    """Retourne les intersections entre une droite 2D et un cercle sous forme (t, u, v)."""
    delta_u = line_end_u - line_start_u
    delta_v = line_end_v - line_start_v
    offset_u = line_start_u - center_u
    offset_v = line_start_v - center_v
    quadratic_a = delta_u ** 2 + delta_v ** 2
    quadratic_b = 2 * (offset_u * delta_u + offset_v * delta_v)
    quadratic_c = offset_u ** 2 + offset_v ** 2 - radius ** 2
    discriminant = quadratic_b ** 2 - 4 * quadratic_a * quadratic_c
    if quadratic_a == 0 or discriminant < 0:
        return []
    if abs(discriminant) <= 1e-9:
        parameter_t = -quadratic_b / (2 * quadratic_a)
        return [(parameter_t, line_start_u + parameter_t * delta_u, line_start_v + parameter_t * delta_v)]
    sqrt_discriminant = math.sqrt(discriminant)
    parameter_t1 = (-quadratic_b - sqrt_discriminant) / (2 * quadratic_a)
    parameter_t2 = (-quadratic_b + sqrt_discriminant) / (2 * quadratic_a)
    return [
        (parameter_t1, line_start_u + parameter_t1 * delta_u, line_start_v + parameter_t1 * delta_v),
        (parameter_t2, line_start_u + parameter_t2 * delta_u, line_start_v + parameter_t2 * delta_v),
    ]


def project_point_to_plane(work_plane: str, point_x: float, point_y: float, point_z: float) -> tuple[float, float]:
    """Projette un point 3D dans le plan de travail pour les calculs 2D."""
    if work_plane == "XY":
        return point_x, point_y
    if work_plane == "XZ":
        return point_x, point_z
    return point_y, point_z


def build_point_from_plane(work_plane: str, plane_u: float, plane_v: float, constant_value: float) -> tuple[float, float, float]:
    """Reconstruit un point 3D a partir de coordonnees 2D dans le plan de travail."""
    if work_plane == "XY":
        return plane_u, plane_v, constant_value
    if work_plane == "XZ":
        return plane_u, constant_value, plane_v
    return constant_value, plane_u, plane_v


def cw_tangent_vector(work_plane: str, radial_u: float, radial_v: float) -> tuple[float, float]:
    """Retourne la tangente de depart d'un G2 dans le plan considere."""
    if work_plane == "XZ":
        return -radial_v, radial_u
    return radial_v, -radial_u


def ccw_tangent_vector(work_plane: str, radial_u: float, radial_v: float) -> tuple[float, float]:
    """Retourne la tangente de depart d'un G3 dans le plan considere."""
    if work_plane == "XZ":
        return radial_v, -radial_u
    return -radial_v, radial_u
