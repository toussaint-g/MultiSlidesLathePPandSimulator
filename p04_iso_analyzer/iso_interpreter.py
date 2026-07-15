# -*- coding: utf-8 -*-

import math
import re
from enum import Enum
from app_errors import ErrorCategory, error_message
from p01_machines_config.machine_parameters import JsonDict, MachineParameters, normalize_gm_code


def _build_gm_code_pattern(code):
    """Construit un regex tolerant les zeros a gauche sur la partie numerique."""
    normalized_code = normalize_gm_code(code)
    match = re.fullmatch(r'([A-Z]+)(\d+)', normalized_code)
    if not match:
        return re.compile(rf'(?<![A-Za-z]){re.escape(normalized_code)}(?=\D|$)')
    prefix, number = match.groups()
    return re.compile(rf'(?<![A-Za-z]){prefix}0*{number}(?=\D|$)')

def _build_work_plane_map(xy_code, xz_code, yz_code):
    """Associe les codes plan de travail du JSON aux plans XY/XZ/YZ internes."""
    return {
        normalize_gm_code(xy_code): WorkPlaneType.XY,
        normalize_gm_code(xz_code): WorkPlaneType.XZ,
        normalize_gm_code(yz_code): WorkPlaneType.YZ,
    }


class IsoInterpreter:
    """Classe qui permet d'analyser et comprendre le GCode"""

    def __init__(self, machine_config: JsonDict, channel_name: str):
        self.machine = MachineParameters.from_config(machine_config, channel_name)
        self.work_plane_by_code = _build_work_plane_map(
            self.machine.xy_work_plane_code,
            self.machine.xz_work_plane_code,
            self.machine.yz_work_plane_code,
        )

    def _get_tool_change_point_position(self, position_c: float) -> tuple[float, float, float]:
        """Retourne le point de changement outil selon l'angle C courant."""
        return self.machine.get_tool_change_point_for_c_axis(position_c)

    def analyze(self, path):
        """Cette methode vient extraire les donnees utiles de chaque ligne du GCode et les stocker dans une liste d'objet"""

        # Liste qui va stocker les objets ligne avec les donnees utiles pour le rapport
        lines = []

        obj_modal = Modal(machine_parameters=self.machine)
        obj_mathematical_functions = MathematicalFunctions(
            x_diameter=self.machine.x_diameter,
            calculation_tolerance=self.machine.calculation_tolerance,
        )
        # Ouverture du fichier GCode
        with open(path, 'r') as gcode_file:

            # Expressions regulieres pour extraire les donnees des lignes de GCode
            # Nombre CNC robuste : 10 | -10 | +10 | 10.5 | .5 | - .5 | 10,5 | 1e-3 | -2.3E+4
            NUM = r'[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][-+]?\d+)?'
            pattern_x        = re.compile(rf'(?<![A-Za-z])X({NUM})')
            pattern_y        = re.compile(rf'(?<![A-Za-z])Y({NUM})')
            pattern_z        = re.compile(rf'(?<![A-Za-z])Z({NUM})')
            pattern_c        = re.compile(rf'(?<![A-Za-z])C({NUM})')
            pattern_radius   = re.compile(rf'(?<![A-Za-z])R({NUM})')
            pattern_i        = re.compile(rf'(?<![A-Za-z])I({NUM})')
            pattern_j        = re.compile(rf'(?<![A-Za-z])J({NUM})')
            pattern_k        = re.compile(rf'(?<![A-Za-z])K({NUM})')
            pattern_feedrate = re.compile(rf'(?<![A-Za-z])F({NUM})')
            # Pattern pour extraire les info
            pattern_tool = re.compile(r'(?<![A-Za-z])T(\d{2})(\d{2})(?!\d)') # T suivi de 2 chiffres pour le numero d'outil et 2 chiffres pour le correcteur d'outil, sans chiffre apres
            pattern_rapid_move = _build_gm_code_pattern(self.machine.rapid_move_code)
            pattern_linear_move = _build_gm_code_pattern(self.machine.linear_move_code)
            pattern_circular_move_cw = _build_gm_code_pattern(self.machine.circular_move_CW_code)
            pattern_circular_move_ccw = _build_gm_code_pattern(self.machine.circular_move_CCW_code)
            pattern_timer = _build_gm_code_pattern(self.machine.timer_code)

            # Lecture du fichier ligne par ligne
            for line in gcode_file:
                # Nettoyage de la ligne : suppression des commentaires et des espaces superflus
                line = re.sub(r'\(.*?\)', '', line)
                line = re.sub(r'\s+', '', line)

                match_x = pattern_x.search(line)
                match_y = pattern_y.search(line)
                match_z = pattern_z.search(line)
                match_c = pattern_c.search(line)
                match_radius = pattern_radius.search(line)
                match_i = pattern_i.search(line)
                match_j = pattern_j.search(line)
                match_k = pattern_k.search(line)
                match_feedrate = pattern_feedrate.search(line)
                match_tool = pattern_tool.search(line)
                match_move_rapid = pattern_rapid_move.search(line)
                match_move_linear = pattern_linear_move.search(line)
                match_move_cw = pattern_circular_move_cw.search(line)
                match_move_ccw = pattern_circular_move_ccw.search(line)
                match_timer = pattern_timer.search(line)
                arc_center_x = None
                arc_center_y = None
                arc_center_z = None

                # Recuperation des coordonnees de position et du rayon
                if match_x and not match_timer:
                    if self.machine.x_diameter:
                        position_x = float(match_x.group(1)) / 2
                    else:
                        position_x = float(match_x.group(1))
                else:
                    # En modal, une coordonnee absente reutilise la derniere valeur connue.
                    position_x = obj_modal.position_x

                if match_y:
                    position_y = float(match_y.group(1))
                else:
                    position_y = obj_modal.position_y

                if match_z:
                    position_z = float(match_z.group(1))
                else:
                    position_z = obj_modal.position_z

                if match_c:
                    position_c = float(match_c.group(1))
                else:
                    position_c = obj_modal.position_c
                
                radius = obj_modal.radius
                
                # Recuperation de l'avance, de l'outil et du correcteur d'outil
                if match_feedrate:
                    feedrate = float(match_feedrate.group(1))
                else:
                    feedrate = obj_modal.feedrate

                if match_tool:
                    tool = int(match_tool.group(1))
                    tool_offset = int(match_tool.group(2))
                    # Lors d'un changement d'outil, l'analyse repart du point de changement outil
                    # et du plan de travail declare sur l'outil dans la config machine.
                    work_plane = self.work_plane_by_code[self.machine.get_tool_work_plane_code(tool)]
                    tool_change_x, tool_change_y, tool_change_z = self._get_tool_change_point_position(position_c)
                    position_x = tool_change_x
                    position_y = tool_change_y
                    position_z = tool_change_z
                    if obj_modal.tool == 0:
                        obj_modal.position_x = position_x
                        obj_modal.position_y = position_y
                        obj_modal.position_z = position_z
                else:
                    tool = obj_modal.tool
                    tool_offset = obj_modal.tool_offset
                    work_plane = obj_modal.work_plane

                # Recuperation du type de mouvement et du mode (absolu/incremental)
                if match_move_rapid:
                    move = self.machine.rapid_move_code
                elif match_move_linear:
                    move = self.machine.linear_move_code
                elif match_move_cw:
                    move = self.machine.circular_move_CW_code
                elif match_move_ccw:
                    move = self.machine.circular_move_CCW_code
                else:
                    move = obj_modal.gcode_group01

                if move in (self.machine.circular_move_CW_code, self.machine.circular_move_CCW_code):
                    if match_radius:
                        raise ValueError(error_message(
                            ErrorCategory.GEOMETRY,
                            "arc G2/G3 avec R non supporte, utiliser IJK",
                        ))
                    if work_plane == WorkPlaneType.XY:
                        if not match_i or not match_j:
                            raise ValueError(error_message(
                                ErrorCategory.GEOMETRY,
                                "arc G2/G3 en plan XY sans offsets I/J",
                            ))
                        i_value = float(match_i.group(1))
                        j_value = float(match_j.group(1))
                        k_value = 0.0
                    elif work_plane == WorkPlaneType.XZ:
                        if not match_i or not match_k:
                            raise ValueError(error_message(
                                ErrorCategory.GEOMETRY,
                                "arc G2/G3 en plan XZ sans offsets I/K",
                            ))
                        i_value = float(match_i.group(1))
                        j_value = 0.0
                        k_value = float(match_k.group(1))
                    elif work_plane == WorkPlaneType.YZ:
                        if not match_j or not match_k:
                            raise ValueError(error_message(
                                ErrorCategory.GEOMETRY,
                                "arc G2/G3 en plan YZ sans offsets J/K",
                            ))
                        i_value = 0.0
                        j_value = float(match_j.group(1))
                        k_value = float(match_k.group(1))
                    else:
                        raise ValueError(error_message(
                            ErrorCategory.GEOMETRY,
                            "arc G2/G3 sans plan de travail actif",
                        ))

                    arc_center_x = obj_modal.position_x + i_value
                    arc_center_y = obj_modal.position_y + j_value
                    arc_center_z = obj_modal.position_z + k_value
                    radius = math.sqrt(i_value ** 2 + j_value ** 2 + k_value ** 2)

                # Calcul des distances suivant le type de mouvement
                if move == self.machine.rapid_move_code:
                    distance = obj_mathematical_functions.linear_distance_3D(
                            obj_modal.position_x,
                            obj_modal.position_y,
                            obj_modal.position_z,
                            position_x,
                            position_y,
                            position_z,
                        )
                    distance_in_material = 0.0
                    move_type = MoveType.RAPID_MOVE
                elif move == self.machine.linear_move_code:
                    distance = obj_mathematical_functions.linear_distance_3D(
                            obj_modal.position_x,
                            obj_modal.position_y,
                            obj_modal.position_z,
                            position_x,
                            position_y,
                            position_z,
                        )
                    distance_in_material = distance
                    move_type = MoveType.LINEAR_MOVE
                else:
                    # Pour un arc, le centre vient obligatoirement des offsets IJK.
                    distance = obj_mathematical_functions.circular_distance_3D(
                            obj_modal.position_x,
                            obj_modal.position_y,
                            obj_modal.position_z,
                            position_x,
                            position_y,
                            position_z,
                            arc_center_x,
                            arc_center_y,
                            arc_center_z,
                            radius,
                            move == self.machine.circular_move_CW_code,
                            work_plane,
                        )
                    distance_in_material = distance
                    if move == self.machine.circular_move_CW_code:
                        move_type = MoveType.CIRCULAR_MOVE_CW
                    else:
                        move_type = MoveType.CIRCULAR_MOVE_CCW

                # Recuperation des differents temps
                # Calcul du temps de mouvement et du temps productif
                if move == self.machine.rapid_move_code:
                    time = obj_mathematical_functions.mouvement_time(distance, self.machine.rapidfeedrate)
                    productive_time = 0.0
                else:
                    time = obj_mathematical_functions.mouvement_time(distance, feedrate)
                    productive_time = time

                # Si changement d'outil, on ajoute le temps de changement d'outil
                if match_tool:
                    time = time + (self.machine.change_tool_time / 60)

                # Creation de l'objet ligne et ajout a la liste
                obj_line = Line(
                    line,
                    tool,
                    tool_offset,
                    distance,
                    distance_in_material,
                    time,
                    productive_time,
                    move_type,
                    radius,
                    feedrate,
                    position_x,
                    position_y,
                    position_z,
                    position_c,
                    work_plane,
                    arc_center_x,
                    arc_center_y,
                    arc_center_z)
                
                lines.append(obj_line)

                # La ligne est maintenant analysee : on propage les valeurs modales
                # pour qu'elles servent de reference a la ligne suivante.
                obj_modal.position_x = position_x
                obj_modal.position_y = position_y
                obj_modal.position_z = position_z
                obj_modal.position_c = position_c
                obj_modal.radius = radius
                obj_modal.feedrate = feedrate
                obj_modal.tool = tool
                obj_modal.tool_offset = tool_offset
                obj_modal.gcode_group01 = move
                obj_modal.work_plane = work_plane

        return lines


class MathematicalFunctions:
    """Classe qui permet d'analyser et comprendre le GCode"""

    def __init__(self, x_diameter, calculation_tolerance=0.0):
        self.x_diameter = x_diameter
        self.calculation_tolerance = calculation_tolerance

    def linear_distance_3D(self, start_point_x, start_point_y, start_point_z, end_point_x, end_point_y, end_point_z):
        """Cette methode retourne la distance entre les points"""

        distance = math.sqrt(
            (end_point_x - start_point_x) ** 2
            + (end_point_y - start_point_y) ** 2
            + (end_point_z - start_point_z) ** 2
        )
        return distance

    def circular_distance_3D(
        self,
        start_point_x,
        start_point_y,
        start_point_z,
        end_point_x,
        end_point_y,
        end_point_z,
        center_x,
        center_y,
        center_z,
        radius,
        direction_cw,
        work_plane,
    ):
        """Classe qui permet de calculer la longueur d'un arc. Il tient egalement compte d'un eventuel mouvement sur le 3eme axe (3d)"""

        if center_x is None or center_y is None or center_z is None:
            raise ValueError(error_message(
                ErrorCategory.GEOMETRY,
                "centre IJK absent pour calculer la longueur d'arc",
            ))

        tolerance = abs(self.calculation_tolerance)
        if radius <= tolerance:
            raise ValueError(error_message(
                ErrorCategory.GEOMETRY,
                "rayon d'arc nul",
            ))

        if work_plane == WorkPlaneType.XY:
            start_u, start_v = start_point_x, start_point_y
            end_u, end_v = end_point_x, end_point_y
            center_u, center_v = center_x, center_y
            helical_delta = end_point_z - start_point_z
        elif work_plane == WorkPlaneType.XZ:
            start_u, start_v = start_point_x, start_point_z
            end_u, end_v = end_point_x, end_point_z
            center_u, center_v = center_x, center_z
            helical_delta = end_point_y - start_point_y
        elif work_plane == WorkPlaneType.YZ:
            start_u, start_v = start_point_y, start_point_z
            end_u, end_v = end_point_y, end_point_z
            center_u, center_v = center_y, center_z
            helical_delta = end_point_x - start_point_x
        else:
            raise ValueError(error_message(
                ErrorCategory.GEOMETRY,
                "plan de travail absent pour calculer la longueur d'arc",
            ))

        angle1 = math.atan2(start_v - center_v, start_u - center_u)
        angle2 = math.atan2(end_v - center_v, end_u - center_u)
        angle_tolerance = 1e-12
        if direction_cw:
            angle = angle1 - angle2
            if angle <= angle_tolerance:
                angle += 2 * math.pi
        else:
            angle = angle2 - angle1
            if angle <= angle_tolerance:
                angle += 2 * math.pi

        # Calcul de la longueur de l'arc
        arc_length = radius * angle

        # Calcul distance 3d si helicoidal
        arc_length_3d = math.sqrt((arc_length ** 2) + (abs(helical_delta) ** 2))

        return arc_length_3d

    def mouvement_time(self, distance, feedrate):
        """Cette methode retourne la duree pour parcourir une certaine distance"""
        if feedrate == 0:
            raise ValueError(error_message(
                ErrorCategory.FEEDRATE,
                "avance nulle, impossible de calculer le temps de mouvement",
            ))
        return distance / feedrate


class Modal:
    """Classe qui permet de memoriser les fonctions modales du GCode"""

    def __init__(self, machine_parameters: MachineParameters):
        self.machine = machine_parameters
        self.feedrate = self.machine.rapidfeedrate
        self.gcode_group01 = self.machine.rapid_move_code

        self.tool = 0
        self.tool_offset = 0
        self.radius = 0.0
        self.position_x, self.position_y, self.position_z = self.machine.get_initial_tool_change_point()
        self.position_c = 0.0
        self.work_plane = None


class Line:
    """Classe qui permet de memoriser le contenu utile au rapport des lignes du G-Code"""

    def __init__(self, g_code_line, tool_number, tool_offset, distance, distance_in_material, time, productive_time,
                 move_type, radius, feedrate, endpoint_x, endpoint_y, endpoint_z, endpoint_c, work_plane,
                 arc_center_x=None, arc_center_y=None, arc_center_z=None):
        self.g_code_line = g_code_line
        self.tool_number = tool_number
        self.tool_offset = tool_offset
        self.distance = distance
        self.distance_in_material = distance_in_material
        self.time = time
        self.productive_time = productive_time
        self.move_type = move_type
        self.radius = radius
        self.feedrate = feedrate
        self.endpoint_x = endpoint_x
        self.endpoint_y = endpoint_y
        self.endpoint_z = endpoint_z
        self.endpoint_c = endpoint_c
        self.work_plane = work_plane
        self.arc_center_x = arc_center_x
        self.arc_center_y = arc_center_y
        self.arc_center_z = arc_center_z

class MoveType(Enum):
    """Enum pour memoriser les types de mouvement par ligne"""
    ANY = -1
    RAPID_MOVE = 0
    LINEAR_MOVE = 1
    CIRCULAR_MOVE_CW = 2  # Sens horaire
    CIRCULAR_MOVE_CCW = 3  # Sens anti-horaire

class WorkPlaneType(Enum):
    """Enum pour memoriser les types de plan de travail"""
    XY = [0.0, 0.0, 1.0]
    XZ = [0.0, 1.0, 0.0]
    YZ = [1.0, 0.0, 0.0]
