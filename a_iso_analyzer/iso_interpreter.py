# -*- coding: utf-8 -*-

import math
import re
from enum import Enum


def _normalize_gm_code(code):
    """Normalise un code G/M numérique (ex: G00 -> G0, M06 -> M6)."""
    normalized_code = code.strip().upper()
    match = re.fullmatch(r'([A-Z]+)0*(\d+)', normalized_code)
    if not match:
        return normalized_code
    prefix, number = match.groups()
    return f"{prefix}{int(number)}"


def _build_gm_code_pattern(code):
    """Construit un regex tolérant les zéros à gauche sur la partie numérique."""
    normalized_code = _normalize_gm_code(code)
    match = re.fullmatch(r'([A-Z]+)(\d+)', normalized_code)
    if not match:
        return re.compile(rf'(?<![A-Za-z]){re.escape(normalized_code)}(?=\D|$)')
    prefix, number = match.groups()
    return re.compile(rf'(?<![A-Za-z]){prefix}0*{number}(?=\D|$)')

def _build_work_plane_map(xy_code, xz_code, yz_code):
    """Associe les codes plan de travail du JSON aux plans XY/XZ/YZ internes."""
    return {
        _normalize_gm_code(xy_code): WorkPlaneType.XY,
        _normalize_gm_code(xz_code): WorkPlaneType.XZ,
        _normalize_gm_code(yz_code): WorkPlaneType.YZ,
    }


class IsoInterpreter:
    """Classe qui permet d'analyser et comprendre le GCode"""

    def __init__(self, machine_config, channel_name):
        try:
            self.machine_config = machine_config
            self.channel_name = channel_name
            self.calculation_tolerance = self.machine_config["calculationtolerance"]
            # machineinformations
            self.rapidfeedrate = self.machine_config["machineinformations"]["rapidfeedrate"]
            self.change_tool_time = self.machine_config["machineinformations"]["changetooltime"]
            self.x_diameter = self.machine_config["machineinformations"]["xdiameter"]
            self.rapid_move_code = _normalize_gm_code(self.machine_config["machineinformations"]["rapidmove"])
            self.linear_move_code = _normalize_gm_code(self.machine_config["machineinformations"]["linearmove"])
            self.circular_move_CW_code = _normalize_gm_code(self.machine_config["machineinformations"]["circularmoveCW"])
            self.circular_move_CWW_code = _normalize_gm_code(self.machine_config["machineinformations"]["circularmoveCCW"])
            self.timer_code = _normalize_gm_code(self.machine_config["machineinformations"]["timer"])
            self.toolchange_code = _normalize_gm_code(self.machine_config["machineinformations"]["toolchange"])
            self.toolname_prefix = self.machine_config["machineinformations"]["toolnameprefix"]
            self.xy_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xyworkplane"])
            self.xz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xzworkplane"])
            self.yz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["yzworkplane"])
            self.work_plane_by_code = _build_work_plane_map(self.xy_work_plane_code,self.xz_work_plane_code,self.yz_work_plane_code)
            self.default_work_plane = _normalize_gm_code(self.machine_config["machineinformations"]["defaultworkplane"])
            # channelslist
            self.home_tool_x = self.machine_config["channelslist"][self.channel_name]["hometool"]["x"]
            if self.x_diameter:
                self.home_tool_x = self.home_tool_x / 2
            self.home_tool_y = self.machine_config["channelslist"][self.channel_name]["hometool"]["y"]
            self.home_tool_z = self.machine_config["channelslist"][self.channel_name]["hometool"]["z"]
        except KeyError:
            raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")
        except ValueError:
            raise ValueError("MachineConfigError: code plan de travail invalide dans le fichier JSON")


    def analyze(self, path):
        """Cette méthode vient extraire les données utiles de chaque ligne du GCode et les stocker dans une liste d'objet"""

        # Liste qui va stocker les objets ligne avec les données utiles pour le rapport
        lines = []

        obj_modal = Modal(self.machine_config, self.channel_name)
        obj_mathematical_functions = MathematicalFunctions(self.calculation_tolerance, self.x_diameter)

        # Ouverture du fichier GCode
        with open(path, 'r') as gcode_file:

            # Expressions régulières pour extraire les données des lignes de GCode
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
            pattern_tool = re.compile(r'(?<![A-Za-z])T(\d{2})(\d{2})(?!\d)') # T suivi de 2 chiffres pour le numéro d'outil et 2 chiffres pour le correcteur d'outil, sans chiffre après
            pattern_rapid_move = _build_gm_code_pattern(self.rapid_move_code)
            pattern_linear_move = _build_gm_code_pattern(self.linear_move_code)
            pattern_circular_move_cw = _build_gm_code_pattern(self.circular_move_CW_code)
            pattern_circular_move_ccw = _build_gm_code_pattern(self.circular_move_CWW_code)
            pattern_timer = _build_gm_code_pattern(self.timer_code)
            pattern_toolchange = _build_gm_code_pattern(self.toolchange_code)
            pattern_work_plane_xy = _build_gm_code_pattern(self.xy_work_plane_code)
            pattern_work_plane_xz = _build_gm_code_pattern(self.xz_work_plane_code)
            pattern_work_plane_yz = _build_gm_code_pattern(self.yz_work_plane_code)

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
                match_m6 = pattern_toolchange.search(line)
                match_work_plane_xy = pattern_work_plane_xy.search(line)
                match_work_plane_xz = pattern_work_plane_xz.search(line)
                match_work_plane_yz = pattern_work_plane_yz.search(line)

                # Récupération des coordonnées de position et du rayon
                if match_x and not match_timer:
                    if self.x_diameter:
                        position_x = float(match_x.group(1)) / 2
                    else:
                        position_x = float(match_x.group(1))
                else:
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
                
                # R dans les mouvements circulaires : si R est présent on le prend,
                # sinon on le calcule à partir des IJK ou on prend le dernier R utilisé (stocké dans les données modales)
                if match_radius:
                    radius = float(match_radius.group(1))
                else:
                    radius = obj_modal.radius

                # Calcul du rayon pour les mouvements circulaires et détermination du plan de travail
                work_plane = obj_modal.work_plane
                if match_i and match_j:
                    radius = math.sqrt((float(match_i.group(1))) ** 2 + (float(match_j.group(1))) ** 2)
                    work_plane = self.work_plane_by_code[self.xy_work_plane_code]
                elif match_i and match_k:
                    radius = math.sqrt((float(match_i.group(1))) ** 2 + (float(match_k.group(1))) ** 2)
                    work_plane = self.work_plane_by_code[self.xz_work_plane_code]
                elif match_j and match_k:
                    radius = math.sqrt((float(match_j.group(1))) ** 2 + (float(match_k.group(1))) ** 2)
                    work_plane = self.work_plane_by_code[self.yz_work_plane_code]
                
                # Récupération de l'avance, de l'outil et du correcteur d'outil
                if match_feedrate:
                    feedrate = float(match_feedrate.group(1))
                else:
                    feedrate = obj_modal.feedrate

                if match_tool:
                    tool = int(match_tool.group(1))
                    tool_offset = int(match_tool.group(2))
                    position_x = self.home_tool_x
                    position_y = self.home_tool_y
                    position_z = self.home_tool_z
                    work_plane = self.work_plane_by_code[self.default_work_plane]
                else:
                    tool = obj_modal.tool
                    tool_offset = obj_modal.tool_offset

                # Récupération du type de mouvement et du mode (absolu/incrémental)
                if match_move_rapid:
                    move = self.rapid_move_code
                elif match_move_linear:
                    move = self.linear_move_code
                elif match_move_cw:
                    move = self.circular_move_CW_code
                elif match_move_ccw:
                    move = self.circular_move_CWW_code
                else:
                    move = obj_modal.gcode_group01

                # Calcul des distances suivant le type de mouvement
                if move == self.rapid_move_code:
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
                elif move == self.linear_move_code:
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
                    distance = obj_mathematical_functions.circular_distance_3D(
                            obj_modal.position_x,
                            obj_modal.position_y,
                            obj_modal.position_z,
                            position_x,
                            position_y,
                            position_z,
                            radius,
                        )
                    distance_in_material = distance
                    if move == self.circular_move_CW_code:
                        move_type = MoveType.CIRCULAR_MOVE_CW
                    else:
                        move_type = MoveType.CIRCULAR_MOVE_CCW

                # Récupération du plan de travail
                if match_work_plane_xy:
                    work_plane = self.work_plane_by_code[self.xy_work_plane_code]
                elif match_work_plane_xz:
                    work_plane = self.work_plane_by_code[self.xz_work_plane_code]
                elif match_work_plane_yz:
                    work_plane = self.work_plane_by_code[self.yz_work_plane_code]

                # Récupération des différents temps
                # Calcul du temps de mouvement et du temps productif
                if move == self.rapid_move_code:
                    time = obj_mathematical_functions.mouvement_time(distance, self.rapidfeedrate)
                    productive_time = 0.0
                else:
                    time = obj_mathematical_functions.mouvement_time(distance, feedrate)
                    productive_time = time

                # Si changement d'outil, on ajoute le temps de changement d'outil
                if match_m6:
                    time = time + (self.change_tool_time / 60)

                # Création de l'objet ligne et ajout à la liste
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
                    work_plane)
                
                lines.append(obj_line)

                # Mise à jour des données modales
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
        """Cette méthode retourne la distance entre les points"""

        distance = math.sqrt(
            (end_point_x - start_point_x) ** 2
            + (end_point_y - start_point_y) ** 2
            + (end_point_z - start_point_z) ** 2
        )
        return distance

    def circular_distance_3D(self, start_point_x, start_point_y, start_point_z, end_point_x, end_point_y, end_point_z, radius):
        """Classe qui permet de calculer la longueur d'un arc. Il tient également compte d'un éventuel mouvement sur le 3ème axe (3d)"""

        # Milieu du segment reliant start et end
        mx = (start_point_x + end_point_x) / 2
        my = (start_point_y + end_point_y) / 2

        # Distance entre start et end
        d = math.dist((start_point_x, start_point_y), (end_point_x, end_point_y))

        if d > 2 * radius:
            raise ValueError("Le rayon est trop petit pour passer par les deux points !!")

        # Distance entre le milieu et le centre du cercle
        h = math.sqrt(radius**2 - (d / 2) ** 2)

        # Calcul du vecteur perpendiculaire au segment start-end
        dx = end_point_x - start_point_x
        dy = end_point_y - start_point_y
        perp_dx = -dy
        perp_dy = dx

        # Normalisation du vecteur
        norm = math.sqrt(perp_dx**2 + perp_dy**2)

        if norm != 0:
            perp_dx = perp_dx / norm
            perp_dy = perp_dy / norm

        # Deux solutions pour le centre du cercle
        cx1 = mx + h * perp_dx
        cy1 = my + h * perp_dy

        # Choisir le bon cercle
        cx, cy = cx1, cy1

        # Calcul de l'angle entre start et end en passant par le centre
        angle1 = math.atan2(start_point_y - cy, start_point_x - cx)
        angle2 = math.atan2(end_point_y - cy, end_point_x - cx)
        angle = abs(angle2 - angle1)

        # Si l'angle dépasse 180°, on prend l'arc le plus court
        if angle > math.pi:
            angle = 2 * math.pi - angle

        # Calcul de la longueur de l'arc
        arc_length = radius * angle

        # Calcul distance 3d si hélicoïdal
        arc_length_3d = math.sqrt((arc_length ** 2) + (abs(end_point_z - start_point_z) ** 2))

        return arc_length_3d

    def mouvement_time(self, distance, feedrate):
        """Cette méthode retourne la durée pour parcourir une certaine distance"""
        try:
            return distance / feedrate
        except ZeroDivisionError:
            print("Error: Division par 0 !")
            return 0
    
    def calculate_coordinates_from_c_axis(self, position_x, position_y, position_c):
        """ Calcul des coordonnées X et Y en fonction de C"""
        if self.x_diameter:
            position_x_for_c_axis = ((position_x / 2) * math.cos(math.radians(position_c)) - position_y * math.sin(math.radians(position_c))) * 2
            position_y_for_c_axis = (position_x / 2) * math.sin(math.radians(position_c)) + position_y * math.cos(math.radians(position_c))
        else:
            position_x_for_c_axis = position_x * math.cos(math.radians(position_c)) - position_y * math.sin(math.radians(position_c))
            position_y_for_c_axis = position_x * math.sin(math.radians(position_c)) + position_y * math.cos(math.radians(position_c))
        return (position_x_for_c_axis, position_y_for_c_axis)


class Modal:
    """Classe qui permet de mémoriser les fonctions modales du GCode"""

    def __init__(self, machine_config, channel_name):

        try:
            self.machine_config = machine_config
            self.channel_name = channel_name
            # machineinformations
            self.feedrate = self.machine_config["machineinformations"]["rapidfeedrate"]
            self.x_diameter = self.machine_config["machineinformations"]["xdiameter"]
            self.gcode_group01 = _normalize_gm_code(self.machine_config["machineinformations"]["rapidmove"])
            self.xy_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xyworkplane"])
            self.xz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xzworkplane"])
            self.yz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["yzworkplane"])
            self.work_plane_by_code = _build_work_plane_map(self.xy_work_plane_code, self.xz_work_plane_code, self.yz_work_plane_code)
            self.default_work_plane = _normalize_gm_code(self.machine_config["machineinformations"]["defaultworkplane"])
            # channelslist
            self.home_tool_x = self.machine_config["channelslist"][self.channel_name]["hometool"]["x"]
            if self.x_diameter:
                self.home_tool_x = self.home_tool_x / 2
            self.home_tool_y = self.machine_config["channelslist"][self.channel_name]["hometool"]["y"]
            self.home_tool_z = self.machine_config["channelslist"][self.channel_name]["hometool"]["z"]
        except KeyError:
            raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")
        except ValueError:
            raise ValueError("MachineConfigError: code plan de travail invalide dans le fichier JSON")

        self.tool = 0
        self.tool_offset = 0
        self.radius = 0.0
        self.position_x = self.home_tool_x
        self.position_y = self.home_tool_y
        self.position_z = self.home_tool_z
        self.position_c = 0.0
        self.work_plane = self.work_plane_by_code[self.default_work_plane]


class Line:
    """Classe qui permet de mémoriser le contenu utile au rapport des lignes du G-Code"""

    def __init__(self, g_code_line, tool_number, tool_offset, distance, distance_in_material, time, productive_time, 
                 move_type, radius, feedrate, endpoint_x, endpoint_y, endpoint_z, endpoint_c, work_plane):
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

class MoveType(Enum):
    """Enum pour mémoriser les types de mouvement par ligne"""
    ANY = -1
    RAPID_MOVE = 0
    LINEAR_MOVE = 1
    CIRCULAR_MOVE_CW = 2  # Sens horaire
    CIRCULAR_MOVE_CCW = 3  # Sens anti-horaire

class WorkPlaneType(Enum):
    """Enum pour mémoriser les types de plan de travail"""
    XY = [0.0, 0.0, 1.0]
    XZ = [0.0, 1.0, 0.0]
    YZ = [1.0, 0.0, 0.0]
