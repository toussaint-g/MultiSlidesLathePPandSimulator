# -*- coding: utf-8 -*-

# Librairie standard
import vtk
import numpy as np

from app_errors import ErrorCategory, error_message


class ToolPathBuilder:
    """Cette classe permet construire les trajectoires"""

    def __init__(self):
        pass

    @staticmethod
    def _build_plane_basis(plane_normal):
        """Construit une base orthonormee (u, v, n) depuis la normale du plan."""
        # plane_normal peut etre un WorkPlaneType (Enum) ou un vecteur [x, y, z].
        if hasattr(plane_normal, "value"):
            normal_values = plane_normal.value
        else:
            normal_values = plane_normal

        n = np.array(normal_values, dtype=float)
        norm_n = np.linalg.norm(n)
        if norm_n == 0:
            raise ValueError(error_message(
                ErrorCategory.GEOMETRY,
                "le vecteur normal du plan ne peut pas etre nul",
            ))
        n = n / norm_n

        # Choisir un axe de reference non colineaire a n.
        ref = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u = np.cross(n, ref)
        u = u / np.linalg.norm(u)
        v = np.cross(n, u)
        return u, v, n

    def build_line_points(self, start_point, end_point):
        """Retourne les points 3D necessaires pour representer une ligne."""
        return [
            (float(start_point[0]), float(start_point[1]), float(start_point[2])),
            (float(end_point[0]), float(end_point[1]), float(end_point[2])),
        ]

    def create_polyline(self, points_vtk: vtk.vtkPoints, lines_vtk: vtk.vtkCellArray, path_points):
        """Cree une polyline VTK a partir d'une liste de points 3D."""
        if len(path_points) < 2:
            return

        point_ids = []
        for point_x, point_y, point_z in path_points:
            point_ids.append(points_vtk.InsertNextPoint(point_x, point_y, point_z))

        polyline = vtk.vtkPolyLine()
        polyline.GetPointIds().SetNumberOfIds(len(point_ids))
        for i, point_id in enumerate(point_ids):
            polyline.GetPointIds().SetId(i, point_id)

        lines_vtk.InsertNextCell(polyline)

    def build_circle_points(self, start_point, end_point, center_point, resolution_cercle, direction_cw, work_plane):
        """Retourne les points 3D necessaires pour representer un cercle dans un plan donne."""

        # Le viewer trajectoire travaille en XYZ : ignorer une eventuelle 4e composante (axe C).
        np_start_point = np.array(start_point[:3], dtype=float)
        np_end_point = np.array(end_point[:3], dtype=float)
        np_center_point = np.array(center_point[:3], dtype=float)

        # Base du plan de projection.
        u, v, n = self._build_plane_basis(work_plane)

        # Coordonnees 2D dans le plan.
        s2 = np.array([np.dot(np_start_point, u), np.dot(np_start_point, v)])
        e2 = np.array([np.dot(np_end_point, u), np.dot(np_end_point, v)])
        center = np.array([np.dot(np_center_point, u), np.dot(np_center_point, v)])

        # Composante selon la normale (utile pour un deplacement helicoidal).
        sn = np.dot(np_start_point, n)
        en = np.dot(np_end_point, n)

        radius = np.linalg.norm(s2 - center)
        if radius == 0:
            raise ValueError(error_message(
                ErrorCategory.GEOMETRY,
                "centre d'arc identique au point de depart",
            ))

        def angle_from(center, point):
            vec = point - center
            return np.arctan2(vec[1], vec[0])

        angle_start = angle_from(center, s2)
        angle_end = angle_from(center, e2)
        same_point = np.linalg.norm(e2 - s2) <= 1e-9

        if direction_cw:
            if same_point:
                angle_end = angle_start - 2 * np.pi
            elif angle_end > angle_start:
                angle_end -= 2 * np.pi
        else:
            if same_point:
                angle_end = angle_start + 2 * np.pi
            elif angle_end < angle_start:
                angle_end += 2 * np.pi

        # Le nombre de segments est deduit de la longueur d'arc voulue et de la
        # resolution cible, puis on interpole aussi la composante hors-plan pour
        # supporter les arcs helicoidaux.
        arc_angle = abs(angle_end - angle_start)
        arc_length = radius * arc_angle

        num_segments = max(int(np.ceil(arc_length / resolution_cercle)), 1)
        angles = np.linspace(angle_start, angle_end, num_segments + 1)

        n_step = (en - sn) / num_segments
        path_points = []
        for i, theta in enumerate(angles):
            p2 = np.array(
                [
                    center[0] + radius * np.cos(theta),
                    center[1] + radius * np.sin(theta),
                ]
            )
            pn = sn + i * n_step
            # Retour au repere 3D global a partir de la base locale du plan.
            p3 = p2[0] * u + p2[1] * v + pn * n
            path_points.append((float(p3[0]), float(p3[1]), float(p3[2])))

        return path_points
