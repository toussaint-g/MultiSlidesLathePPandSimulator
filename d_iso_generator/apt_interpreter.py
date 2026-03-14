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


def _build_work_plane_map(xy_code, xz_code, yz_code):
    """Associe les codes plan de travail du JSON aux plans XY/XZ/YZ internes."""
    return {
        _normalize_gm_code(xy_code): WorkPlaneType.XY,
        _normalize_gm_code(xz_code): WorkPlaneType.XZ,
        _normalize_gm_code(yz_code): WorkPlaneType.YZ,
    }


class AptInterpreter:
    """Classe qui permet d'analyser et comprendre le GCode"""

    def __init__(self, machine_config, channel_name):
        try:
            self.machine_config = machine_config
            self.channel_name = channel_name
            # self.calculation_tolerance = self.machine_config["calculationtolerance"]
            # self.rapid_move_code = _normalize_gm_code(self.machine_config["machineinformations"]["rapidmove"])
            # self.linear_move_code = _normalize_gm_code(self.machine_config["machineinformations"]["linearmove"])
            # self.circular_move_CW_code = _normalize_gm_code(self.machine_config["machineinformations"]["circularmoveCW"])
            # self.circular_move_CWW_code = _normalize_gm_code(self.machine_config["machineinformations"]["circularmoveCCW"])
            # self.timer_code = _normalize_gm_code(self.machine_config["machineinformations"]["timer"])
            # self.toolchange_code = _normalize_gm_code(self.machine_config["machineinformations"]["toolchange"])
            # self.rapidfeedrate = self.machine_config["machineinformations"]["rapidfeedrate"]
            # self.change_tool_time = self.machine_config["machineinformations"]["changetooltime"]
            # self.x_diameter = self.machine_config["machineinformations"]["xdiameter"]
            # self.home_tool_x = self.machine_config["channelslist"][self.channel_name]["hometool"]["x"]
            # if self.x_diameter:
            #     self.home_tool_x = self.home_tool_x / 2
            # self.home_tool_y = self.machine_config["channelslist"][self.channel_name]["hometool"]["y"]
            # self.home_tool_z = self.machine_config["channelslist"][self.channel_name]["hometool"]["z"]
            # self.xy_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xyworkplane"])
            # self.xz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xzworkplane"])
            # self.yz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["yzworkplane"])
            # self.work_plane_by_code = _build_work_plane_map(self.xy_work_plane_code,self.xz_work_plane_code,self.yz_work_plane_code)
            # self.default_work_plane = _normalize_gm_code(self.machine_config["machineinformations"]["defaultworkplane"])
            # self.activate_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingBP"])
            # self.disable_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingBP"])
            # self.activate_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingCOP"])
            # self.disable_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingCOP"])
        except KeyError:
            raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")
        except ValueError:
            raise ValueError("MachineConfigError: code plan de travail invalide dans le fichier JSON")


    def analyze(self, path):
        """Cette méthode vient extraire les données utiles de chaque ligne de l'APT et les stocker dans une liste d'objet"""

        # Liste qui va stocker les objets ligne avec les données utiles pour le rapport
        lines = []
        # Variables pour gérer l'indexation de l'axe C (BP et COP)
        c_axis_indexing_on = False

        obj_modal = Modal(self.machine_config, self.channel_name)
        # obj_mathematical_functions = MathematicalFunctions(self.calculation_tolerance, self.x_diameter)

        # Ouverture du fichier APT
        with open(path, 'r') as apt_file:

            # Expressions régulières pour extraire les mots majeurs avec texte
            pattern_partno = re.compile(r'^PARTNO/(.+)$')
            pattern_part_ope = re.compile(r'^PART_OPE/(.+)$')
            pattern_program = re.compile(r'^PROGRAM/(.+)$')
            pattern_machine = re.compile(r'^MACHINE/(.+)$')
            pattern_catprocess = re.compile(r'^CATPROCESS/(.+)$')
            pattern_catproduct = re.compile(r'^CATPRODUCT/(.+)$')
            pattern_op_name = re.compile(r'^OP_NAME/(.+)$')
            pattern_tprint = re.compile(r'^TPRINT/(.+)$')
            pattern_pprint = re.compile(r'^PPRINT/(.+)$')
            # Expressions régulières pour extraire les mots majeurs sans paramètres
            pattern_end = re.compile(r'^END$')# TODO: Voir si besoin et voir pour extraire






            # Expressions régulières pour extraire les mots majeurs avec paramètres
            pattern_startop = re.compile(r'^START_OP/(.+)$')
            pattern_endop = re.compile(r'^END_OP/(.+)$')
            pattern_toolpathtype = re.compile(r'^TOOLPATH_TYPE/(.+)$')
            pattern_tlaxis = re.compile(r'^TLAXIS/(.+)$')# TODO: Voir si besoin
            pattern_tdata = re.compile(r'^TDATA/(.+)$')# TODO: Voir si besoin
            pattern_spindl = re.compile(r'^SPINDL/(.+)$')# TODO: Voir si besoin
            # Expression régulière pour extraire les coordonnées et les paramètres de mouvement
            pattern_goto = re.compile(r'(?<![A-Za-z])GOTO(\d+)')
            pattern_indirv = re.compile(r'(?<![A-Za-z])INDIRV(\d+)')
            pattern_tlon_gofwd = re.compile(r'(?<![A-Za-z])TLON_GO_FWD(\d+)')





            # Lecture du fichier ligne par ligne
            for line in apt_file:
                #line = re.sub(r'\s+', '', line) # Suppression des espaces
                #line = re.sub(r'\t+', '', line) # Suppression des tabs

                # Extraction données de l'en-tête de l'APT
                match_partno = pattern_partno.search(line)
                match_part_ope = pattern_part_ope.search(line)
                match_program = pattern_program.search(line)
                match_machine = pattern_machine.search(line)
                match_catprocess = pattern_catprocess.search(line)
                match_catproduct = pattern_catproduct.search(line)
                match_op_name = pattern_op_name.search(line)
                match_tprint = pattern_tprint.search(line)
                match_pprint = pattern_pprint.search(line)

                if match_partno:
                    partno = match_partno.group(1)
                else:
                    partno = obj_modal.partno

                if match_part_ope:
                    part_ope = match_part_ope.group(1)
                else:
                    part_ope = obj_modal.part_ope

                if match_program:
                    program = match_program.group(1)
                else:
                    program = obj_modal.program

                if match_machine:
                    machine = match_machine.group(1)
                else:
                    machine = obj_modal.machine

                if match_catprocess:
                    catprocess = match_catprocess.group(1)
                else:
                    catprocess = obj_modal.catprocess

                if match_catproduct:
                    catproduct = match_catproduct.group(1)
                else:
                    catproduct = obj_modal.catproduct

                if match_op_name:
                    op_name = match_op_name.group(1)
                else:
                    op_name = obj_modal.op_name

                if match_tprint:
                    tprint = match_tprint.group(1)
                else:
                    tprint = obj_modal.tprint

                if match_pprint:
                    pprint = match_pprint.group(1)
                else:
                    pprint = obj_modal.pprint









                # Création de l'objet ligne et ajout à la liste
                obj_line = Line(
                    line, 
                    partno,
                    part_ope,
                    program,
                    machine,
                    catprocess, 
                    catproduct, 
                    op_name, 
                    tprint, 
                    pprint
                    )
                
                lines.append(obj_line)

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
            # self.gcode_group01 = _normalize_gm_code(self.machine_config["machineinformations"]["rapidmove"])
            # self.feedrate = self.machine_config["machineinformations"]["rapidfeedrate"]
            # self.x_diameter = self.machine_config["machineinformations"]["xdiameter"]
            # self.home_tool_x = self.machine_config["channelslist"][self.channel_name]["hometool"]["x"]
            # if self.x_diameter:
            #     self.home_tool_x = self.home_tool_x / 2
            # self.home_tool_y = self.machine_config["channelslist"][self.channel_name]["hometool"]["y"]
            # self.home_tool_z = self.machine_config["channelslist"][self.channel_name]["hometool"]["z"]
            # self.xy_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xyworkplane"])
            # self.xz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["xzworkplane"])
            # self.yz_work_plane_code = _normalize_gm_code(self.machine_config["machineinformations"]["yzworkplane"])
            # self.work_plane_by_code = _build_work_plane_map(self.xy_work_plane_code, self.xz_work_plane_code, self.yz_work_plane_code)
            # self.default_work_plane = _normalize_gm_code(self.machine_config["machineinformations"]["defaultworkplane"])
            # self.activate_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingBP"])
            # self.disable_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingBP"])
            # self.activate_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingCOP"])
            # self.disable_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingCOP"])
        except KeyError:
            raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")
        except ValueError:
            raise ValueError("MachineConfigError: code plan de travail invalide dans le fichier JSON")

        # self.tool = 0
        # self.tool_offset = 0
        # self.radius = 0.0
        # self.position_x = self.home_tool_x
        # self.position_y = self.home_tool_y
        # self.position_z = self.home_tool_z
        # self.position_c = 0.0
        # self.work_plane = self.work_plane_by_code[self.default_work_plane]

        self.partno = None
        self.part_ope = None
        self.program = None
        self.machine = None
        self.catprocess = None
        self.catproduct = None
        self.op_name = None
        self.tprint = None
        self.pprint = None





class Line:
    """Classe qui permet de mémoriser le contenu utile au rapport des lignes du G-Code"""

    def __init__(self,
                 apt_line,
                 partno,
                 part_ope,
                 program,
                 machine,
                 catprocess,
                 catproduct, 
                 op_name, 
                 tprint, 
                 pprint
                 ):
        
        
        
        self.apt_line = apt_line
        self.partno = partno
        self.part_ope = part_ope
        self.program = program
        self.machine = machine
        self.catprocess = catprocess
        self.catproduct = catproduct
        self.op_name = op_name
        self.tprint = tprint
        self.pprint = pprint

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
