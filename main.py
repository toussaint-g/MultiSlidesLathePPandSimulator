
# -*- coding: utf-8 -*-

# Librairie standard
from pathlib import Path
from datetime import datetime
import tkinter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkbootstrap import Style
import ttkbootstrap as tb 
from PIL import Image, ImageTk
import os
import re

# Modules internes
from a_iso_analyzer.iso_interpreter import IsoInterpreter
from a_iso_analyzer.iso_analyzer_writer import IsoAnalyzerWriter
from b_machines_config.machine_parameters import JsonDict
from b_machines_config.machines_config_loader import MachinesConfigLoader
from c_toolpath_constructor.toolpath_viewer import ToolPathViewer
from c_toolpath_constructor.toolpath_viewer_config_loader import ToolPathConfigLoader
# from d_iso_generator.apt_interpreter import AptInterpreter
# from d_iso_generator.apt_analyser_writer import AptAnalyserWriter
from d_iso_generator.apt2iso import convert_file


# Fonction sélection de fichier
def file_select(file_type, file_ext, label, update_calculate_button):
    """ Fonction de sélection de fichier """
    file = tkinter.filedialog.askopenfilename(title="Sélectionner un fichier", filetypes=[(file_type, file_ext)])
    if file:
        label.config(text=file)
        update_calculate_button()  # Met Ã  jour l'état du bouton "Calculer"


# Fonction sélection de dossier
def folder_select(label):
    """ Fonction de sélection de dossier """
    folder = tkinter.filedialog.askdirectory(title="Sélectionner un dossier")
    if folder:
        label.config(text=folder)


# Fonction pour nom de fichier Ã  la date et heure du jour
def get_datetime_string():
    """ Retourne la date et l'heure sous la forme YYYY-MM-DD_HH-MM-SS """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")











# Fonction traitement APT
def apt_treatment(path_apt_file, path_export_file, machine_name, channel_name):

    # Charge les config
    MachinesConfigLoader.load_config()

    # Récupère la config de la machine sélectionnée
    machine_config: JsonDict = MachinesConfigLoader.get_machine(machine_name)

    # Instanciation des classes
    # obj_interpreter = AptInterpreter(machine_config, channel_name) 
    # obj_writer = AptAnalyserWriter(machine_config)

    # list_datas = obj_interpreter.analyze(path_apt_file) # Récup data
    # obj_writer.write_iso_file(Path(path_export_file).with_suffix(".nc"), path_apt_file, list_datas) # Création du rapport

    #display_results(path_export_file)

    try:
        if not path_apt_file:
            messagebox.showwarning("APT manquant", "Sélectionne un fichier APT source.")
            return

        path_export_file.mkdir(parents=True, exist_ok=True)

        in_path = Path(path_apt_file)
        out_path = path_export_file / (in_path.stem + ".debug")

        convert_file(str(in_path), str(out_path), machine_config, channel_name)

        messagebox.showinfo("Conversion terminée", f"ISO généré :\n{out_path}")

    except Exception as e:
        messagebox.showerror("Erreur conversion", str(e))













# Fonction traitement G-Code
def gcode_treatment(path_gcode_file, path_export_file, machine_name, channel_name):

    # Charge les config
    MachinesConfigLoader.load_config()

    # RécupÃ¨re la config de la machine sélectionnée
    machine_config: JsonDict = MachinesConfigLoader.get_machine(machine_name)

    # Instanciation des classes
    obj_interpreter = IsoInterpreter(machine_config, channel_name) 
    obj_writer = IsoAnalyzerWriter(machine_config)

    list_datas = obj_interpreter.analyze(path_gcode_file) # Récup data
    obj_writer.write_report(Path(path_export_file).with_suffix(".txt"), path_gcode_file, list_datas) # Création du rapport
    obj_writer.write_debug_file(Path(path_export_file).with_suffix(".debug"), path_gcode_file, list_datas) # Création du fichier debug

    display_results(path_export_file)


def display_results(path_export_file):
    """ Affiche la fenêtre avec le résultat de l'analyse du G Code """

    result_window = tk.Toplevel()
    result_window.title("PPandSimulatorForMultiSlidesLathe: Résultat")
    result_window.state('zoomed')

    result_frame = tk.Frame(result_window)
    result_frame.pack(fill="both", expand=True, padx=10, pady=10)

    result_label = tk.Label(result_frame, text="Résultat :", font=("Segoe UI", 18, "bold"))
    result_label.pack(pady=10, anchor="w")

    # Rapport
    result_text_frame = tk.Frame(result_frame)
    result_text_frame.pack(padx=10, pady=5, fill="both", expand=True)
    result_text = tk.Text(result_text_frame, height=10, width=70, font=("Segoe UI", 12))
    result_scrollbar = tk.Scrollbar(result_text_frame, command=result_text.yview)
    result_text.config(yscrollcommand=result_scrollbar.set)
    result_text.pack(side="left", fill="both", expand=True)
    result_scrollbar.pack(side="right", fill="y")

    try:
        with open(path_export_file.with_suffix(".txt"), 'r') as file:
            result_text.insert(tk.END, file.read())
    except Exception as e:
        result_text.insert(tk.END, f"Erreur lors de la lecture du fichier : {e}")
    result_text.config(state=tk.DISABLED)

    # Debug
    separator = tk.Label(result_frame, text="Debug :", font=("Segoe UI", 18, "bold"))
    separator.pack(pady=5, anchor="w")

    debug_text_frame = tk.Frame(result_frame)
    debug_text_frame.pack(padx=10, pady=5, fill="both", expand=True)
    debug_text = tk.Text(debug_text_frame, height=10, width=70, font=("Courier", 7))
    debug_scrollbar = tk.Scrollbar(debug_text_frame, command=debug_text.yview)
    debug_text.config(yscrollcommand=debug_scrollbar.set)
    debug_text.pack(side="left", fill="both", expand=True)
    debug_scrollbar.pack(side="right", fill="y")

    try:
        with open(path_export_file.with_suffix(".debug"), 'r') as file:
            debug_text.insert(tk.END, file.read())
    except Exception as e:
        debug_text.insert(tk.END, f"Erreur lors de la lecture du fichier : {e}")
    debug_text.config(state=tk.DISABLED)


# Fonction traitement G-Code
def viewer_launch(path_gcode_file, stl_path_file, machine_name, channel_name, part_thickness):
    """ Lance la visualisation des trajectoires à partir du G-Code et du STL """
    # Charge les config
    MachinesConfigLoader.load_config()
    ToolPathConfigLoader.load_config()

    machine_config: JsonDict = MachinesConfigLoader.get_machine(machine_name)

    # Instanciation des classes
    obj_interpreter = IsoInterpreter(machine_config, channel_name) 
    obj_toolpathviewer = ToolPathViewer(machine_config, channel_name, part_thickness)

    # Récup datas g-code
    list_datas = obj_interpreter.analyze(path_gcode_file)

    # Start viewer
    obj_toolpathviewer.open_viewer(stl_path_file, list_datas)


def update_channel_combo(selected_machine, channel_combo, selected_channel):
    """ Met à jour la liste des canaux disponibles en fonction de la machine sélectionnée """
    machine_name = selected_machine.get()
    updated_channels = MachinesConfigLoader.get_channels_list_for_machine(machine_name)
    channel_combo["values"] = updated_channels
    selected_channel.set(updated_channels[0] if updated_channels else "")


def open_machine_image_for(machine_name):
    """ Ouvre l'image de la machine sélectionnée dans le visualiseur d'images par défaut du système """
    machine_config: JsonDict = MachinesConfigLoader.get_machine(machine_name)
    try:
        rel = machine_config["imgkinematic"]
    except KeyError:
        raise ValueError("MachineConfigError: une clé est absente dans le fichier JSON")

    base = Path(__file__).parent
    image_path = Path(base / rel)
    if not image_path.exists():
        raise ValueError(f"MachineConfigError: l'image spécifiée est introuvable : {image_path}")
    os.startfile(image_path)


def nombre_decimal_negatif_valide(nouveau_texte):
    """ Valide que l'entrée est un nombre décimal négatif ou un état intermédiaire autorisé """
    if nouveau_texte in ("", "-", ".", ",", "-.", "-,"):
        return True
    return re.fullmatch(r"-?(\d+([.,]\d*)?|[.,]\d+)", nouveau_texte) is not None


def update_calculate_button(label_path, buttons):
    """ Active ou désactive une liste de boutons selon la sélection ISO """
    state = "normal" if label_path.cget("text") else "disabled"
    for button in buttons:
        button.config(state=state)


# Point d'entrée app
def main():
    """Point d'entrée de l'application"""

    # Charge les config
    MachinesConfigLoader.load_config() 

    style = Style(theme="darkly") 

    # Création form avec nom & dimension
    form = style.master
    form.title("PPandSimulatorForMultiSlidesLathe")
    form.state('zoomed')

    # Frame principale
    main_frame = tb.Frame(form, padding=20)
    main_frame.pack(expand=True, fill="both")

    # 3 colonnes de même largeur
    for col in range(3):
        main_frame.grid_columnconfigure(col, weight=1, uniform="main_cols")

    # Icon de l'application
    icon_app = Image.open("img/iconform.png")
    #icon_app = icon_app.resize((32, 32))
    icon_app_tk = ImageTk.PhotoImage(icon_app) # Conversion image en format Tkinter
    form.iconphoto(True, icon_app_tk) # Appliquer l'icône au formulaire

    # Titre
    tb.Label(
        main_frame,
        text="PPandSimulatorForMultiSlidesLathe",
        font=("Segoe UI", 28, "bold"),
        bootstyle="dark",
        foreground="white"
    ).grid(column=0, row=0, columnspan=3, padx=5, pady=5)

    # Logo de l'application
    logo_app = Image.open("img/logoapp.png")
    logo_app_tk = ImageTk.PhotoImage(logo_app)
    label_logo_tk = tb.Label(main_frame, image=logo_app_tk)
    label_logo_tk.grid(column=0, row=1, columnspan=3, padx=5, pady=25)
   
    # Ligne vide
    tb.Label(main_frame, text="", font=("Segoe UI", 8)).grid(column=0, row=2, sticky="w", padx=5, pady=5)



    # Colonne 1
    # Section titre post-process
    tb.Label(main_frame, text="Zone post-process :", font=("Segoe UI", 20)).grid(column=0, row=3, sticky="w", padx=5, pady=5)
    tb.Label(main_frame, text="Pour le post-process des fichiers ATP de CATIA V5.", font=("Segoe UI", 14)).grid(column=0, row=4, sticky="w", padx=5, pady=5)
    
    # Ligne vide
    tb.Label(main_frame, text="", font=("Segoe UI", 8)).grid(column=0, row=5, sticky="w", padx=5, pady=5)

    # Section APT
    tb.Label(main_frame, text="Fichier APT :", font=("Segoe UI", 16)).grid(column=0, row=6, sticky="w", padx=5, pady=5)
    label_apt_for_pp = tb.Label(main_frame, text="", width=50, bootstyle="secondary")
    label_apt_for_pp.grid(column=0, row=7, sticky="w")
    tb.Button(main_frame, text="Sélectionner", bootstyle="primary", 
              command=lambda: file_select("Fichier APT", "*.aptsource", label_apt_for_pp, 
                                          lambda: update_calculate_button(label_apt_for_pp, [calculate_button_for_pp]))).grid(column=0, row=8, sticky="w", padx=5, pady=5)

    # Section dossier de sortie
    tb.Label(main_frame, text="Dossier de sortie :", font=("Segoe UI", 16)).grid(column=0, row=9, sticky="w", padx=5, pady=5)
    label_output_folder_for_pp = tb.Label(main_frame, text="C:\\Temp", width=50, bootstyle="secondary")
    label_output_folder_for_pp.grid(column=0, row=10, sticky="w")
    tb.Button(main_frame, text="Sélectionner", bootstyle="primary", 
              command=lambda: folder_select(label_output_folder_for_pp)).grid(column=0, row=11, sticky="w", padx=5, pady=5)

    # Ligne vide
    tb.Label(main_frame, text="", font=("Segoe UI", 8)).grid(column=0, row=12, sticky="w", padx=5, pady=5)

    # Section machine
    tb.Label(main_frame, text="Machine cible :", font=("Segoe UI", 16)).grid(column=0, row=13, sticky="w", padx=5, pady=5)
    # Données fournies par le JSON
    machines_list_for_pp = MachinesConfigLoader.get_machines_names()
    selected_machine_for_pp = tk.StringVar(value=machines_list_for_pp[0] if machines_list_for_pp else "")
    machine_combo_for_pp = tb.Combobox(
        main_frame,
        textvariable=selected_machine_for_pp,
        values=machines_list_for_pp,
        state="readonly",
        width=47,
        bootstyle="secondary"
    )
    machine_combo_for_pp.grid(column=0, row=14, sticky="w", padx=5, pady=5)

    # Section canal machine
    tb.Label(main_frame, text="Canal de la machine :", font=("Segoe UI", 16)).grid(column=0, row=15, sticky="w", padx=5, pady=5)
    # Données fournies par le JSON
    channels_list_for_pp = MachinesConfigLoader.get_channels_list_for_machine(selected_machine_for_pp.get())
    selected_channel_for_pp = tk.StringVar(value=channels_list_for_pp[0] if channels_list_for_pp else "")
    channel_combo_for_pp = tb.Combobox(
        main_frame,
        textvariable=selected_channel_for_pp,
        values=channels_list_for_pp,
        state="readonly",
        width=47,
        bootstyle="secondary"
    )
    channel_combo_for_pp.grid(column=0, row=16, sticky="w", padx=5, pady=5)

    machine_combo_for_pp.bind(
        "<<ComboboxSelected>>",
        lambda _event: update_channel_combo(selected_machine_for_pp, channel_combo_for_pp, selected_channel_for_pp),
    )

    # Ligne vide
    tb.Label(main_frame, text="", font=("Segoe UI", 8)).grid(column=0, row=17, sticky="w", padx=5, pady=5)

    # Section générer le fichier ISO
    tb.Label(main_frame, text="Générer le fichier ISO :", font=("Segoe UI", 16)).grid(column=0, row=18, sticky="w", padx=5, pady=5)

    # Section calculer les données
    calculate_button_for_pp = tb.Button(main_frame, text="Start", bootstyle="success", command=lambda: apt_treatment(
        Path(label_apt_for_pp.cget("text")),
        Path(label_output_folder_for_pp.cget("text")) / get_datetime_string(),
        selected_machine_for_pp.get(),
        selected_channel_for_pp.get()))
    calculate_button_for_pp.grid(column=0, row=19, sticky="w", pady=5)
    calculate_button_for_pp.config(state="disabled")  # Désactiver au début



    # Colonne 2
    # Section titre analyse
    tb.Label(main_frame, text="Zone analyse :", font=("Segoe UI", 20)).grid(column=1, row=3, sticky="w", padx=5, pady=5)
    tb.Label(main_frame, text="Pour l'analyse des temps d'usinage des fichiers ISO.", font=("Segoe UI", 14)).grid(column=1, row=4, sticky="w", padx=5, pady=5)

    # Section code ISO
    tb.Label(main_frame, text="Fichier ISO :", font=("Segoe UI", 16)).grid(column=1, row=6, sticky="w", padx=5, pady=5)
    label_iso_file_for_analyzer = tb.Label(main_frame, text="", width=50, bootstyle="secondary")
    label_iso_file_for_analyzer.grid(column=1, row=7, sticky="w")
    tb.Button(main_frame, text="Sélectionner", bootstyle="primary", 
              command=lambda: file_select("Fichier ISO", "*.anc;*.nc;*.txt;*.path1;*.path2;*.path3", label_iso_file_for_analyzer, 
                                          lambda: update_calculate_button(label_iso_file_for_analyzer, [calculate_button_for_analyzer, visualize_button_for_analyzer]))).grid(column=1, row=8, sticky="w", padx=5, pady=5)

    # Section dossier de sortie
    tb.Label(main_frame, text="Dossier de sortie :", font=("Segoe UI", 16)).grid(column=1, row=9, sticky="w", padx=5, pady=5)
    label_output_folder_for_analyzer = tb.Label(main_frame, text="C:\\Temp", width=50, bootstyle="secondary")
    label_output_folder_for_analyzer.grid(column=1, row=10, sticky="w")
    tb.Button(main_frame, text="Sélectionner", bootstyle="primary", 
              command=lambda: folder_select(label_output_folder_for_analyzer)).grid(column=1, row=11, sticky="w", padx=5, pady=5)

    # Section machine
    tb.Label(main_frame, text="Machine cible :", font=("Segoe UI", 16)).grid(column=1, row=13, sticky="w", padx=5, pady=5)
    # Données fournies par le JSON
    machines_list_for_analyzer = MachinesConfigLoader.get_machines_names()
    selected_machine_for_analyzer = tk.StringVar(value=machines_list_for_analyzer[0] if machines_list_for_analyzer else "")
    machine_combo_for_analyzer = tb.Combobox(
        main_frame,
        textvariable=selected_machine_for_analyzer,
        values=machines_list_for_analyzer,
        state="readonly",
        width=47,
        bootstyle="secondary"
    )
    machine_combo_for_analyzer.grid(column=1, row=14, sticky="w", padx=5, pady=5)

    # Section canal machine
    tb.Label(main_frame, text="Canal de la machine :", font=("Segoe UI", 16)).grid(column=1, row=15, sticky="w", padx=5, pady=5)
    # Données fournies par le JSON
    channels_list_for_analyzer = MachinesConfigLoader.get_channels_list_for_machine(selected_machine_for_analyzer.get())
    selected_channel_for_analyzer = tk.StringVar(value=channels_list_for_analyzer[0] if channels_list_for_analyzer else "")
    channel_combo_for_analyzer = tb.Combobox(
        main_frame,
        textvariable=selected_channel_for_analyzer,
        values=channels_list_for_analyzer,
        state="readonly",
        width=47,
        bootstyle="secondary"
    )
    channel_combo_for_analyzer.grid(column=1, row=16, sticky="w", padx=5, pady=5)

    machine_combo_for_analyzer.bind(
        "<<ComboboxSelected>>",
        lambda _event: update_channel_combo(selected_machine_for_analyzer, channel_combo_for_analyzer, selected_channel_for_analyzer),
    )

    # Section calculer les données
    tb.Label(main_frame, text="Analyser le fichier ISO :", font=("Segoe UI", 16)).grid(column=1, row=18, sticky="w", padx=5, pady=5)    
    calculate_button_for_analyzer = tb.Button(main_frame, text="Start", bootstyle="success", command=lambda: gcode_treatment(
        Path(label_iso_file_for_analyzer.cget("text")),
        Path(label_output_folder_for_analyzer.cget("text")) / get_datetime_string(),
        selected_machine_for_analyzer.get(),
        selected_channel_for_analyzer.get()))
    calculate_button_for_analyzer.grid(column=1, row=19, sticky="w", pady=5)
    calculate_button_for_analyzer.config(state="disabled")  # Désactiver au début



    # Colonne 3
    # Section titre simulateur
    tb.Label(main_frame, text="Zone simulation :", font=("Segoe UI", 20)).grid(column=2, row=3, sticky="w", padx=5, pady=5)
    tb.Label(main_frame, text="Pour la simulation des trajectoires des fichiers ISO.\n-> Sélection du fichier à simuler dans la zone ""analyse""", font=("Segoe UI", 14)).grid(column=2, row=4, sticky="w", padx=5, pady=5)

    # Section STL
    tb.Label(main_frame, text="Fichier STL :", font=("Segoe UI", 16)).grid(column=2, row=6, sticky="w", padx=5, pady=5)
    label_stl = tb.Label(main_frame, text="", width=50, bootstyle="secondary")
    label_stl.grid(column=2, row=7, sticky="w", padx=5)
    tb.Button(main_frame, text="Sélectionner", bootstyle="primary", 
              command=lambda: file_select("Fichier STL", "*.stl", label_stl, 
                                          lambda: update_calculate_button(label_iso_file_for_analyzer, [calculate_button_for_analyzer, visualize_button_for_analyzer]))).grid(column=2, row=8, sticky="w", padx=5, pady=5)

    # Section visualisation de la config machine
    tb.Label(main_frame, text="Visualiser la config machine :", 
             font=("Segoe UI", 16)).grid(column=2, row=13, sticky="w", padx=5, pady=5)

    visualize_button_for_analyzer = tb.Button(main_frame, text="Visualiser", bootstyle="primary", 
                                 command=lambda: open_machine_image_for(selected_machine_for_analyzer.get()))
    visualize_button_for_analyzer.grid(column=2, row=14, sticky="w", padx=5, pady=5)

    # Section décalage pièce
    tb.Label(main_frame, text="Epaisseur pièce (pour déc COP) :", 
             font=("Segoe UI", 16)).grid(column=2, row=15, sticky="w", padx=5, pady=5)
    
    # Validation de l'entrée pour n'autoriser que les nombres décimaux négatifs et les états intermédiaires
    vcmd = (form.register(nombre_decimal_negatif_valide), "%P")
    part_thickness_var = tk.DoubleVar(value=0.0)
    part_thickness = tb.Entry(
        main_frame,
        textvariable=part_thickness_var,
        width=50,
        bootstyle="secondary",
        validate="key",
        validatecommand=vcmd
    )
    part_thickness.grid(column=2, row=16, sticky="w", padx=5, pady=5)

    # Section Visualiser les trajectoires
    tb.Label(main_frame, text="Visualiser les trajectoires :", font=("Segoe UI", 16)).grid(column=2, row=18, sticky="w", padx=5, pady=5)
    visualize_button_for_analyzer = tb.Button(main_frame, text="Start", bootstyle="success", command=lambda: viewer_launch(
        Path(label_iso_file_for_analyzer.cget("text")), 
        Path(label_stl.cget("text")),
        selected_machine_for_analyzer.get(), 
        selected_channel_for_analyzer.get(),
        part_thickness_var.get()))
    visualize_button_for_analyzer.grid(column=2, row=19, sticky="w", padx=5, pady=5)
    visualize_button_for_analyzer.config(state="disabled")  # Désactiver au début

    update_calculate_button(
        label_path=label_iso_file_for_analyzer,
        buttons=[calculate_button_for_analyzer, visualize_button_for_analyzer],
    )

    form.mainloop()

if __name__ == "__main__":
    main()







