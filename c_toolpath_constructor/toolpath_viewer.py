
# -*- coding: utf-8 -*-

# Librairie standard
#from operator import index
import vtk
from vtkmodules.vtkCommonColor import vtkNamedColors

# Modules internes
from b_machines_config.machine_parameters import JsonDict
from c_toolpath_constructor.toolpath_viewer_config_loader import ToolPathConfigLoader
from c_toolpath_constructor.toolpath_interpeter import ToolPathInterpreter


class ToolPathViewer:
    """Cette classe permet la lecture et la creation d'un viewer de ficher 3D"""

    def __init__(self, machine_config: JsonDict, channel_name: str, part_thickness):
        try:
            self.machine_config = machine_config
            self.channel_name = channel_name
            self.part_thickness = part_thickness
            self.viewer_background_color = ToolPathConfigLoader.data["viewer"]["backgroundcolor"]
            self.viewer_text_color = ToolPathConfigLoader.data["viewer"]["textinfocolor"]
            self.viewer_text_size = ToolPathConfigLoader.data["viewer"]["textinfosize"]
            self.viewer_object_color = ToolPathConfigLoader.data["viewer"]["objectcolor"]
            self.viewer_origin_color = ToolPathConfigLoader.data["viewer"]["origincolor"]
            self.viewer_origin_diameter = ToolPathConfigLoader.data["viewer"]["origindiameter"]
            self.viewer_compass_size = ToolPathConfigLoader.data["viewer"]["compasssize"]
            self.tool_path_width = ToolPathConfigLoader.data["toolpath"]["pathwidth"]
            self.tool_path_rapid_move_color = ToolPathConfigLoader.data["toolpath"]["rapidmovecolor"]
            self.tool_path_work_move_color = ToolPathConfigLoader.data["toolpath"]["workmovecolor"]
            self.tool_path_circle_resolution = ToolPathConfigLoader.data["toolpath"]["circleresolution"]
        except KeyError:
            raise ValueError("ToolPathConfigLoaderError: une cle est absente dans le fichier JSON")


    def open_viewer(self, path_file, list_datas):
        """Cette methode ouvre et parametre le viewer 3D"""

        # Couleurs
        colors = vtkNamedColors()
        # Acteur pour stl
        actor_stl = vtk.vtkActor()

        # Contrôle de sélection de fichier STL
        if path_file != "":
            # Lire le fichier STL
            reader = vtk.vtkSTLReader()
            reader.SetFileName(path_file)
            # Acteur pour stl
            mapper_stl = vtk.vtkPolyDataMapper()
            mapper_stl.SetInputConnection(reader.GetOutputPort())
            actor_stl.SetMapper(mapper_stl)
            actor_stl.GetProperty().SetColor(colors.GetColor3d(self.viewer_object_color))
            actor_stl.GetProperty().SetAmbient(0.2)
            actor_stl.GetProperty().SetDiffuse(0.7)
            actor_stl.GetProperty().SetSpecular(0.4)
            actor_stl.GetProperty().SetSpecularPower(30)
            actor_stl.GetProperty().SetOpacity(1)

        # Acteur pour sphère d'origine
        radius = self.viewer_origin_diameter / 2
        sphere_origine = vtk.vtkSphereSource()
        sphere_origine.SetCenter(0.0, 0.0, 0.0)
        sphere_origine.SetRadius(radius)
        sphere_origine.SetPhiResolution(30)
        sphere_origine.SetThetaResolution(30)
        sphere_origine.Update()
        mapper_origine = vtk.vtkPolyDataMapper()
        mapper_origine.SetInputConnection(sphere_origine.GetOutputPort())
        actor_origine = vtk.vtkActor()
        actor_origine.SetMapper(mapper_origine)
        actor_origine.GetProperty().SetColor(colors.GetColor3d(self.viewer_origin_color))
        actor_origine.GetProperty().SetSpecular(0.3) # Lumière spéculaire (point de brillance)
        actor_origine.GetProperty().SetSpecularPower(20) # Netteté de cette lumière spéculaire

        # Moteurs de rendu piece
        renderer_pc = vtk.vtkRenderer()
        renderer_pc.SetBackground(colors.GetColor3d(self.viewer_background_color))
        renderer_pc.AddActor(actor_stl)
        renderer_pc.AddActor(actor_origine)
        renderer_pc.SetLayer(0)


        # Création message texte
        text_rendu = "Escape -> masquage/affichage trajectoires\nSpace -> masquage/affichage pièce\nUp/down -> défilement trajectoires\n\nRendu toolpath: "
        text = vtk.vtkTextActor()
        text.SetInput(text_rendu + "toutes trajectoires affichées")
        textprop = text.GetTextProperty()
        textprop.SetFontSize(self.viewer_text_size)
        textprop.SetColor(colors.GetColor3d(self.viewer_text_color))
        text.SetPosition(10, 10)
        renderer_pc.AddActor2D(text)

        # Moteurs de rendu toolpath
        renderer_toolpath = vtk.vtkRenderer()
        
        # Recup actors
        obj_tool_path_interpeter = ToolPathInterpreter(self.machine_config, self.channel_name, self.part_thickness)
        actors_list = obj_tool_path_interpeter.analyze(
            list_datas,
            self.tool_path_circle_resolution)

        # Boucle recup actor et ajout dans moteur rendu
        for actor_work, actor_rapid in zip(actors_list["work"], actors_list["rapid"]):
            actor_rapid.GetProperty().SetColor(colors.GetColor3d(self.tool_path_rapid_move_color))
            actor_rapid.GetProperty().SetLineWidth(self.tool_path_width)
            actor_work.GetProperty().SetColor(colors.GetColor3d(self.tool_path_work_move_color))
            actor_work.GetProperty().SetLineWidth(self.tool_path_width)
            renderer_toolpath.AddActor(actor_work)
            renderer_toolpath.AddActor(actor_rapid)

        # Layer par dessus la piece
        renderer_toolpath.SetLayer(1)
        renderer_toolpath.SetBackgroundAlpha(0) # Transparence

        # Param form d'affichage
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer_pc)
        render_window.AddRenderer(renderer_toolpath)
        render_window.SetNumberOfLayers(2)
        render_window.SetWindowName("Part Program Analyzer: Viewer 3D")
        render_window.SetSize(800, 800)
        screen_size = render_window.GetScreenSize()
        window_size = render_window.GetSize()
        x_pos = (screen_size[0] - window_size[0]) // 2
        y_pos = (screen_size[1] - window_size[1]) // 2
        render_window.SetPosition(x_pos, y_pos)
        
        # Caméras synchronisées
        renderer_toolpath.SetActiveCamera(renderer_pc.GetActiveCamera())

        # Variables etat
        etat_visu = {
            "current_index": -1,
            "all_visible": True
            }
        
        # Fonctions de navigation
        def visu_actor_list(index):

            # Boucle sur tous les actors work et rapid pour basculer leur visibilité
            for i, (actor_work, actor_rapid) in enumerate(zip(actors_list["work"], actors_list["rapid"])):
                is_visible = (i == index)
                actor_work.SetVisibility(is_visible)
                actor_rapid.SetVisibility(is_visible)

                # Mise a jour du texte
                if is_visible:
                    text.SetInput(f"{text_rendu} T{actor_work.tag}")

            render_window.Render()

        # Basculer la visibilite actor unique (ici uniquement l'acteur stl)
        def visu_actors_uniq(actor):
            actor.SetVisibility(not actor.GetVisibility())
            render_window.Render()

        # Basculer la visibilite de tous les actors
        def visu_tout():

            etat_visu["all_visible"] = not etat_visu["all_visible"]

            # Boucle sur tous les actors work et rapid pour basculer leur visibilité
            for i, (actor_work, actor_rapid) in enumerate(zip(actors_list["work"], actors_list["rapid"])):
                actor_work.SetVisibility(etat_visu["all_visible"])
                actor_rapid.SetVisibility(etat_visu["all_visible"])

            # Mise a jour du texte
            if etat_visu["all_visible"]:
                text.SetInput(text_rendu + "toutes trajectoires affichées")
            else:
                text.SetInput(text_rendu + "toutes trajectoires masquées")

            render_window.Render()

        # Appui clavier
        def appui_clavier(obj, event):

            # Var touche
            touche = obj.GetKeySym()

            # Suivant touche
            # Défilement des toolpath (par bloc ebauche et finition)
            if touche == "Down":
                if etat_visu["current_index"] < len(actors_list["work"]) - 1:
                    etat_visu["current_index"] += 1
                    visu_actor_list(etat_visu["current_index"])

            elif touche == "Up":
                if etat_visu["current_index"] > 0:
                    etat_visu["current_index"] -= 1
                    visu_actor_list(etat_visu["current_index"])

            # Masquer ou afficher tous les actors de traj
            elif touche == "Escape":
                visu_tout()
                etat_visu["current_index"] = -1

            # Masquer ou afficher le stl
            elif touche == "space":
                visu_actors_uniq(actor_stl)
        
        # Interacteur pour naviguer en 3D
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
        interactor.AddObserver("KeyPressEvent", appui_clavier)

         # Supprimer les lumières automatiques
        renderer_pc.AutomaticLightCreationOff()
        renderer_pc.RemoveAllLights()
        renderer_toolpath.AutomaticLightCreationOff()
        renderer_toolpath.RemoveAllLights()

        # Créer une lumière fixe dans la scène
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPositional(True)
        light.SetPosition(100, 100, 100)     # Position fixe
        light.SetFocalPoint(0, 0, 0)         # Elle regarde le centre
        light.SetColor(1.0, 1.0, 1.0)
        light.SetIntensity(0.8)
        renderer_pc.AddLight(light)

        # Mise à jour lumière (position relative a la caméra)
        def update_light_coupled_to_camera(caller, event):
            camera = renderer_pc.GetActiveCamera()
            cam_pos = camera.GetPosition()
            cam_fp = camera.GetFocalPoint()
            light.SetPosition(cam_pos)
            light.SetFocalPoint(cam_fp)

        # Observer sur mouvement de caméra
        renderer_pc.GetActiveCamera().AddObserver("ModifiedEvent", update_light_coupled_to_camera)

        # Mettre a jour les donnees et rendre
        renderer_toolpath.ResetCamera() # Recentre la scene sur le toolpath
        render_window.Render()
        interactor.Initialize()

        # Boussole en bas à droite
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(self.viewer_compass_size, self.viewer_compass_size, self.viewer_compass_size)  # Longueur des axes XYZ
        axes.AxisLabelsOn() # Affiche XYZ
        orientation_widget = vtk.vtkOrientationMarkerWidget()
        orientation_widget.SetOrientationMarker(axes)
        orientation_widget.SetInteractor(interactor)
        orientation_widget.SetViewport(0.8, 0.0, 1.0, 0.2) # Position boussole
        orientation_widget.SetEnabled(1)
        orientation_widget.InteractiveOff() # Non cliquable

        # Start
        interactor.Start()
