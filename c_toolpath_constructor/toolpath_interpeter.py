# -*- coding: utf-8 -*-

# Librairie standard
import math
import vtk

# Modules internes
from a_iso_analyzer.iso_interpreter import MoveType
from b_machines_config.machine_parameters import JsonDict, MachineParameters
from c_toolpath_constructor.toolpath_builder import ToolPathBuilder


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
            raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")

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
        points_rapid_feedrate = vtk.vtkPoints()
        points_work_feedrate = vtk.vtkPoints()
        vertex_rapid_feedrate = vtk.vtkCellArray()
        vertex_work_feedrate = vtk.vtkCellArray()
        c_values_rapid_feedrate = []
        c_values_work_feedrate = []

        # Outil courant
        current_tool = 0

        # Acteurs
        actors = {"work": [], "rapid": []}
        obj_vtk_functions = VtkFunctions()

        def add_c_values_for_new_points(points_vtk, c_values_container, previous_c, current_c):
            """Ajoute une valeur C pour chaque point cree entre deux instants."""
            num_points = points_vtk.GetNumberOfPoints()
            already_stored = len(c_values_container)
            new_points_count = num_points - already_stored
            if new_points_count <= 0:
                return

            if new_points_count == 1:
                c_values_container.append(float(current_c))
                return

            c_step = (current_c - previous_c) / (new_points_count - 1)
            for i in range(new_points_count):
                c_values_container.append(float(previous_c + i * c_step))

        def finalize_polydata_and_add_actors():
            """Construit les polydata, applique transformations puis cree les acteurs."""
            nonlocal actors
            poly_data_rapid_feedrate = vtk.vtkPolyData()
            poly_data_work_feedrate = vtk.vtkPolyData()
            poly_data_rapid_feedrate.SetPoints(points_rapid_feedrate)
            poly_data_work_feedrate.SetPoints(points_work_feedrate)
            poly_data_rapid_feedrate.SetLines(vertex_rapid_feedrate)
            poly_data_work_feedrate.SetLines(vertex_work_feedrate)

            poly_data_rapid_feedrate = obj_vtk_functions.add_c_angle_to_polydata(
                poly_data_rapid_feedrate,
                c_values_rapid_feedrate,
            )
            poly_data_work_feedrate = obj_vtk_functions.add_c_angle_to_polydata(
                poly_data_work_feedrate,
                c_values_work_feedrate,
            )

            poly_data_rapid_feedrate = obj_vtk_functions.apply_c_rotation_to_polydata(poly_data_rapid_feedrate)
            poly_data_work_feedrate = obj_vtk_functions.apply_c_rotation_to_polydata(poly_data_work_feedrate)

            # Application symetrie polydata si necessaire
            if symmetry_plane_vector is not None:
                poly_data_rapid_feedrate = obj_vtk_functions.apply_symmetry_to_polydata(
                    poly_data_rapid_feedrate,
                    symmetry_plane_vector["vector"])
                poly_data_work_feedrate = obj_vtk_functions.apply_symmetry_to_polydata(
                    poly_data_work_feedrate,
                    symmetry_plane_vector["vector"])

            # Application decalage en Z si epaisseur piece renseignee
            if self.part_thickness != 0:
                poly_data_rapid_feedrate = obj_vtk_functions.apply_z_offset_to_polydata(
                    poly_data_rapid_feedrate,
                    self.part_thickness)
                poly_data_work_feedrate = obj_vtk_functions.apply_z_offset_to_polydata(
                    poly_data_work_feedrate,
                    self.part_thickness)

            # Ajout des acteurs
            actors = obj_vtk_functions.create_actors(
                poly_data_rapid_feedrate,
                poly_data_work_feedrate,
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
                points_rapid_feedrate = vtk.vtkPoints()
                points_work_feedrate = vtk.vtkPoints()
                vertex_rapid_feedrate = vtk.vtkCellArray()
                vertex_work_feedrate = vtk.vtkCellArray()
                c_values_rapid_feedrate = []
                c_values_work_feedrate = []

            # Si nouvel outil
            if current_line.tool_number != current_tool and current_line.tool_number != 0:
                finalize_polydata_and_add_actors()

                # Redef structures points et lignes
                points_rapid_feedrate = vtk.vtkPoints()
                points_work_feedrate = vtk.vtkPoints()
                vertex_rapid_feedrate = vtk.vtkCellArray()
                vertex_work_feedrate = vtk.vtkCellArray()
                c_values_rapid_feedrate = []
                c_values_work_feedrate = []

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
                    before_count = points_rapid_feedrate.GetNumberOfPoints()

                    # Contructeur ligne
                    obj_tool_path_builder.create_line(points_rapid_feedrate, vertex_rapid_feedrate, previous_point, current_point)
                    if points_rapid_feedrate.GetNumberOfPoints() > before_count:
                        previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                        add_c_values_for_new_points(
                            points_rapid_feedrate,
                            c_values_rapid_feedrate,
                            previous_c,
                            float(current_point[3]))

                # Si ligne en avance travail
                elif current_line.move_type == MoveType.LINEAR_MOVE:
                    before_count = points_work_feedrate.GetNumberOfPoints()

                    # Contructeur ligne
                    obj_tool_path_builder.create_line(points_work_feedrate, vertex_work_feedrate, previous_point, current_point)
                    if points_work_feedrate.GetNumberOfPoints() > before_count:
                        previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                        add_c_values_for_new_points(
                            points_work_feedrate,
                            c_values_work_feedrate,
                            previous_c,
                            float(current_point[3]))

                # Si cercle CW
                elif current_line.move_type == MoveType.CIRCULAR_MOVE_CW:
                    before_count = points_work_feedrate.GetNumberOfPoints()

                    # Contructeur cercle
                    obj_tool_path_builder.create_circle(
                        points_work_feedrate,
                        vertex_work_feedrate,
                        previous_point,
                        current_point,
                        current_line.radius,
                        resolution_cercle,
                        True,
                        current_line.work_plane)
                    if points_work_feedrate.GetNumberOfPoints() > before_count:
                        previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                        add_c_values_for_new_points(
                            points_work_feedrate,
                            c_values_work_feedrate,
                            previous_c,
                            float(current_point[3]))

                # Si cercle CCW
                elif current_line.move_type == MoveType.CIRCULAR_MOVE_CCW:
                    before_count = points_work_feedrate.GetNumberOfPoints()

                    # Contructeur cercle
                    obj_tool_path_builder.create_circle(
                        points_work_feedrate,
                        vertex_work_feedrate,
                        previous_point,
                        current_point,
                        current_line.radius,
                        resolution_cercle,
                        False,
                        current_line.work_plane)
                    if points_work_feedrate.GetNumberOfPoints() > before_count:
                        previous_c = float(previous_point[3]) if len(previous_point) > 3 else 0.0
                        add_c_values_for_new_points(
                            points_work_feedrate,
                            c_values_work_feedrate,
                            previous_c,
                            float(current_point[3]))

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

    def create_actors(self, datas_rapid_feedrate, datas_work_feedrate, list_actors, current_tool):
        """Cette methode sert a creer les acteurs pour les trajectoires"""

        # Mapper
        mapper_rapid_feedrate = vtk.vtkPolyDataMapper()
        mapper_work_feedrate = vtk.vtkPolyDataMapper()
        mapper_rapid_feedrate.SetInputData(datas_rapid_feedrate)
        mapper_work_feedrate.SetInputData(datas_work_feedrate)

        # Actors
        actor_rapid_feedrate = vtk.vtkActor()
        actor_work_feedrate = vtk.vtkActor()
        actor_rapid_feedrate.SetMapper(mapper_rapid_feedrate)
        actor_work_feedrate.SetMapper(mapper_work_feedrate)

        # Tag pour recup num outil
        actor_rapid_feedrate.tag = current_tool
        actor_work_feedrate.tag = current_tool

        # Ajout dans structure 2 niveaux
        list_actors["work"].append(actor_work_feedrate)  # work index 0
        list_actors["rapid"].append(actor_rapid_feedrate)  # rapid index 1

        return list_actors
