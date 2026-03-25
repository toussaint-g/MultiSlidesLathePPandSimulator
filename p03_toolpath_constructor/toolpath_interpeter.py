# -*- coding: utf-8 -*-

# Librairie standard
import math
import vtk

# Modules internes
from p01_iso_analyzer.iso_interpreter import MoveType
from p02_machines_config.machine_parameters import JsonDict, MachineParameters
from p03_toolpath_constructor.toolpath_builder import ToolPathBuilder


class ToolPathInterpreter:
    """Classe qui permet d'interpeter les datas"""

    def __init__(self, machine_config: JsonDict, channel_name: str, part_thickness):
        try:
            # Initialisation des variables
            self.machine = MachineParameters.from_config(machine_config, channel_name, home_x_mode="part")
            self.part_thickness = part_thickness
            # Data machine
            self.x_diameter = self.machine.x_diameter
            self.home_tool_x = self.machine.home_tool_x
            self.home_tool_y = self.machine.home_tool_y
            self.home_tool_z = self.machine.home_tool_z
            self.ipartvector = self.machine.ipartvector
            self.jpartvector = self.machine.jpartvector
            self.kpartvector = self.machine.kpartvector
            self.ipathvector = self.machine.ipathvector
            self.jpathvector = self.machine.jpathvector
            self.kpathvector = self.machine.kpathvector
        except KeyError:
            raise ValueError("MachineConfigError: une cle est absente dans le fichier JSON")

    @staticmethod
    def _extract_axis_sign(vector):
        """Retourne le signe de l'axe principal d'un vecteur base (ex: [-1,0,0] -> -1)."""
        if not isinstance(vector, list) or len(vector) != 3:
            raise ValueError("VectorFormatError: le vecteur doit contenir 3 composantes")

        non_zero_values = [value for value in vector if value != 0]
        if len(non_zero_values) != 1:
            raise ValueError("VectorFormatError: le vecteur doit avoir une seule composante non nulle")

        sign = non_zero_values[0]
        if sign not in (-1, 1):
            raise ValueError("VectorFormatError: la composante non nulle doit valoir -1 ou 1")
        return sign

    def get_polydata_symmetry_plane_vector(self):
        """Compare ipart/ipath et retourne ipart si inversion (symetrie necessaire)."""
        if self._extract_axis_sign(self.ipartvector) != self._extract_axis_sign(self.ipathvector):
            return {"name": "ipartvector", "vector": self.ipartvector}
        return None

    def analyze(self, list_datas, resolution_cercle):
        """Cette methode recupere les donnees utiles a la construction des trajectoires"""

        # Instanciation des classes
        obj_tool_path_builder = ToolPathBuilder()
        symmetry_plane_vector = self.get_polydata_symmetry_plane_vector()

        # Def structures points et lignes
        points_toolpath = vtk.vtkPoints()
        vertex_toolpath = vtk.vtkCellArray()
        c_values_toolpath = []
        move_type_values = []

        # Outil courant
        current_tool = 0

        # Acteurs
        actors = []
        obj_vtk_functions = VtkFunctions()

        current_polyline_points = []
        current_polyline_c_values = []
        current_move_group_type = None

        def build_c_values_for_path(path_points_count, previous_c, current_c):
            """Construit les valeurs C associees a une liste de points."""
            if path_points_count <= 0:
                return []
            if path_points_count == 1:
                return [float(current_c)]

            c_step = (current_c - previous_c) / (path_points_count - 1)
            return [float(previous_c + i * c_step) for i in range(path_points_count)]

        def flush_current_polyline():
            """Ecrit la polyligne courante dans les structures VTK."""
            nonlocal current_polyline_points, current_polyline_c_values, current_move_group_type
            if len(current_polyline_points) < 2 or current_move_group_type is None:
                current_polyline_points = []
                current_polyline_c_values = []
                current_move_group_type = None
                return

            obj_tool_path_builder.create_polyline(points_toolpath, vertex_toolpath, current_polyline_points)
            c_values_toolpath.extend(current_polyline_c_values)
            move_type_values.append(current_move_group_type)
            current_polyline_points = []
            current_polyline_c_values = []
            current_move_group_type = None

        def append_path_to_current_polyline(path_points, path_c_values, move_type_value):
            """Ajoute un segment a la polyligne courante ou force un flush si besoin."""
            nonlocal current_polyline_points, current_polyline_c_values, current_move_group_type
            if len(path_points) < 2:
                return

            if current_move_group_type != move_type_value:
                flush_current_polyline()

            if not current_polyline_points:
                current_polyline_points = list(path_points)
                current_polyline_c_values = list(path_c_values)
                current_move_group_type = move_type_value
                return

            if current_polyline_points[-1] == path_points[0]:
                current_polyline_points.extend(path_points[1:])
                current_polyline_c_values.extend(path_c_values[1:])
            else:
                current_polyline_points.extend(path_points)
                current_polyline_c_values.extend(path_c_values)

        def finalize_polydata_and_add_actors():
            """Construit le polydata, applique transformations puis cree l'acteur."""
            nonlocal actors
            flush_current_polyline()
            if current_tool == 0 or vertex_toolpath.GetNumberOfCells() == 0:
                return

            poly_data_toolpath = vtk.vtkPolyData()
            poly_data_toolpath.SetPoints(points_toolpath)
            poly_data_toolpath.SetLines(vertex_toolpath)

            poly_data_toolpath = obj_vtk_functions.add_c_angle_to_polydata(
                poly_data_toolpath,
                c_values_toolpath,
            )
            poly_data_toolpath = obj_vtk_functions.add_move_type_to_polydata(
                poly_data_toolpath,
                move_type_values,
            )
            poly_data_toolpath = obj_vtk_functions.apply_c_rotation_to_polydata(poly_data_toolpath)

            # Application symetrie polydata si necessaire
            if symmetry_plane_vector is not None:
                poly_data_toolpath = obj_vtk_functions.apply_symmetry_to_polydata(
                    poly_data_toolpath,
                    symmetry_plane_vector["vector"])

            # Application decalage en Z si epaisseur piece renseignee
            if self.part_thickness != 0:
                poly_data_toolpath = obj_vtk_functions.apply_z_offset_to_polydata(
                    poly_data_toolpath,
                    self.part_thickness)

            # Ajout de l'acteur
            actors = obj_vtk_functions.create_actor(
                poly_data_toolpath,
                actors,
                current_tool)

        # Initialisation previous point
        previous_point = [self.home_tool_x, self.home_tool_y, self.home_tool_z]

        # Lecture datas
        for current_line in list_datas:

            # Si num outil de la ligne courante <> 0 et le courant = 0
            if current_line.tool_number != 0 and current_tool == 0:

                # Val outil courant
                current_tool = current_line.tool_number

                # Def structures points et lignes
                points_toolpath = vtk.vtkPoints()
                vertex_toolpath = vtk.vtkCellArray()
                c_values_toolpath = []
                move_type_values = []
                current_polyline_points = []
                current_polyline_c_values = []
                current_move_group_type = None

            # Si nouvel outil
            if current_line.tool_number != current_tool and current_line.tool_number != 0:
                finalize_polydata_and_add_actors()

                # Redef structures points et lignes
                points_toolpath = vtk.vtkPoints()
                vertex_toolpath = vtk.vtkCellArray()
                c_values_toolpath = []
                move_type_values = []
                current_polyline_points = []
                current_polyline_c_values = []
                current_move_group_type = None

                # Val outil courant
                current_tool = current_line.tool_number

                # Initialisation du point hometool
                previous_point = [self.home_tool_x, self.home_tool_y, self.home_tool_z]

            # Si distance parcourue
            if current_line.distance != 0.0 or current_line.distance_in_material != 0.0 and current_line.tool_number != 0:

                # Point courant
                current_point = [current_line.endpoint_x, current_line.endpoint_y, current_line.endpoint_z, current_line.endpoint_c]

                # Si ligne en avance rapide
                if current_line.move_type == MoveType.RAPID_MOVE:
                    path_points = obj_tool_path_builder.build_line_points(previous_point, current_point)
                    previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                    path_c_values = build_c_values_for_path(len(path_points), previous_c, float(current_point[3]))
                    append_path_to_current_polyline(path_points, path_c_values, 0)

                # Si ligne en avance travail
                elif current_line.move_type == MoveType.LINEAR_MOVE:
                    path_points = obj_tool_path_builder.build_line_points(previous_point, current_point)
                    previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                    path_c_values = build_c_values_for_path(len(path_points), previous_c, float(current_point[3]))
                    append_path_to_current_polyline(path_points, path_c_values, 1)

                # Si cercle CW
                elif current_line.move_type == MoveType.CIRCULAR_MOVE_CW:
                    path_points = obj_tool_path_builder.build_circle_points(
                        previous_point,
                        current_point,
                        current_line.radius,
                        resolution_cercle,
                        True,
                        current_line.work_plane)
                    previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                    path_c_values = build_c_values_for_path(len(path_points), previous_c, float(current_point[3]))
                    append_path_to_current_polyline(path_points, path_c_values, 1)

                # Si cercle CCW
                elif current_line.move_type == MoveType.CIRCULAR_MOVE_CCW:
                    path_points = obj_tool_path_builder.build_circle_points(
                        previous_point,
                        current_point,
                        current_line.radius,
                        resolution_cercle,
                        False,
                        current_line.work_plane)
                    previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                    path_c_values = build_c_values_for_path(len(path_points), previous_c, float(current_point[3]))
                    append_path_to_current_polyline(path_points, path_c_values, 1)

                # Recup pt precedent
                previous_point = current_point

        finalize_polydata_and_add_actors()
        return actors


class VtkFunctions:
    """Classe qui regroupe des fonctions pour vtk"""

    def __init__(self):
        pass

    def apply_symmetry_to_polydata(self, polydata, plane_vector):
        """Applique une symetrie a un vtkPolyData selon le plan donne."""
        axis = [abs(value) for value in plane_vector]

        if axis == [1, 0, 0]:
            scale = (-1, 1, 1)
        elif axis == [0, 1, 0]:
            scale = (1, -1, 1)
        elif axis == [0, 0, 1]:
            scale = (1, 1, -1)
        else:
            raise ValueError("SymmetryError: vecteur de plan non supporte")

        transform = vtk.vtkTransform()
        transform.Scale(scale[0], scale[1], scale[2])

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(polydata)
        transform_filter.Update()

        output_polydata = vtk.vtkPolyData()
        output_polydata.DeepCopy(transform_filter.GetOutput())
        return output_polydata

    def add_c_angle_to_polydata(self, polydata, c_values, array_name="C_angle_deg"):
        """Ajoute un tableau PointData contenant l'angle C de chaque point."""
        output_polydata = vtk.vtkPolyData()
        output_polydata.DeepCopy(polydata)

        num_points = output_polydata.GetNumberOfPoints()
        if len(c_values) != num_points:
            raise ValueError("CDataError: nombre d'angles C different du nombre de points")

        c_array = vtk.vtkDoubleArray()
        c_array.SetName(array_name)
        c_array.SetNumberOfComponents(1)
        c_array.SetNumberOfTuples(num_points)

        for i, c_value in enumerate(c_values):
            c_array.SetValue(i, float(c_value))

        output_polydata.GetPointData().AddArray(c_array)
        return output_polydata

    def add_move_type_to_polydata(self, polydata, move_type_values, array_name="MoveType"):
        """Ajoute un tableau CellData contenant le type de mouvement de chaque segment."""
        output_polydata = vtk.vtkPolyData()
        output_polydata.DeepCopy(polydata)

        num_cells = output_polydata.GetNumberOfCells()
        if len(move_type_values) != num_cells:
            raise ValueError("MoveTypeDataError: nombre de types de mouvements different du nombre de cellules")

        move_type_array = vtk.vtkUnsignedCharArray()
        move_type_array.SetName(array_name)
        move_type_array.SetNumberOfComponents(1)
        move_type_array.SetNumberOfTuples(num_cells)

        for i, move_type_value in enumerate(move_type_values):
            move_type_array.SetValue(i, int(move_type_value))

        output_polydata.GetCellData().SetScalars(move_type_array)
        return output_polydata

    def apply_c_rotation_to_polydata(self, polydata, array_name="C_angle_deg"):
        """Applique une rotation XY point par point selon le tag C stocke en degres."""
        output_polydata = vtk.vtkPolyData()
        output_polydata.DeepCopy(polydata)

        num_points = output_polydata.GetNumberOfPoints()
        if num_points == 0:
            return output_polydata

        c_array = output_polydata.GetPointData().GetArray(array_name)
        if c_array is None:
            return output_polydata

        rotated_points = vtk.vtkPoints()
        rotated_points.SetNumberOfPoints(num_points)

        for i in range(num_points):
            x_value, y_value, z_value = output_polydata.GetPoint(i)
            c_value = c_array.GetValue(i)
            c_rad = math.radians(-c_value)
            x_rotated = x_value * math.cos(c_rad) - y_value * math.sin(c_rad)
            y_rotated = x_value * math.sin(c_rad) + y_value * math.cos(c_rad)
            rotated_points.SetPoint(i, x_rotated, y_rotated, z_value)

        output_polydata.SetPoints(rotated_points)
        return output_polydata

    def apply_z_offset_to_polydata(self, polydata, offset_z):
        """Applique un decalage de toutes les coordonnees selon Z."""
        transform = vtk.vtkTransform()
        transform.Translate(0, 0, offset_z)

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(polydata)
        transform_filter.Update()

        output_polydata = vtk.vtkPolyData()
        output_polydata.DeepCopy(transform_filter.GetOutput())
        return output_polydata

    def create_actor(self, toolpath_data, actors_list, current_tool):
        """Cette methode sert a creer un acteur de trajectoire pour un outil."""
        mapper_toolpath = vtk.vtkPolyDataMapper()
        mapper_toolpath.SetInputData(toolpath_data)
        mapper_toolpath.SetScalarModeToUseCellData()
        mapper_toolpath.SetColorModeToMapScalars()

        actor_toolpath = vtk.vtkActor()
        actor_toolpath.SetMapper(mapper_toolpath)
        actor_toolpath.tag = current_tool

        actors_list.append(actor_toolpath)
        return actors_list
