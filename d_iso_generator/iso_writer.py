
# -*- coding: utf-8 -*-

class IsoWriter:
    """Classe qui permet d'écrire le rapport"""

    def __init__(self, machine_config):
        self.digit_after_point_distance = 3
        self.digit_after_point_time = 4
        try:
            self.rapidfeedrate = machine_config["machineinformations"]["rapidfeedrate"]
        except KeyError:
            raise ValueError("MachineConfigError: Clé 'rapidfeedrate' absente du fichier JSON")


    def format_time(self, minutes):
        """Cette fonction convertit les minutes en heures, minutes, secondes"""
        total_seconds = minutes * 60  # Conversion en secondes
        hours = total_seconds // 3600  # Nombre d'heures --> // retourne l'entier arrondi vers le bas
        minutes = (total_seconds % 3600) // 60  # Nombre de minutes restantes --> // retourne l'entier arrondi vers le bas
        seconds = total_seconds % 60  # Nombre de secondes restantes

        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"





    def write_iso_file(self, file_name, program_name, list_datas):
        """Cette méthode crée et écrit un fichier de debug pour analyse"""

        current_tool = None
        current_tool_offset = None
        time_sum = 0.0
        productive_time_sum = 0.0
        distance_sum = 0.0
        void = ""

        program_time = sum(item.time for item in list_datas)
        program_productive_time = sum(item.productive_time for item in list_datas)
        program_imporductive_time = program_time - program_productive_time

        with open(file_name, 'w') as file:
            file.write(f"Programme : {program_name}\n")
            file.write(f"Nombre de lignes du programme : {len(list_datas)}\n")
            file.write(f"Durée du programme : {self.format_time(program_time)}\n")
            file.write(f"Durée d'usinage : {self.format_time(program_productive_time)}\n")
            file.write(f"Durée improductive : {self.format_time(program_imporductive_time)}\n")
            
            for entry in list_datas:

                # Données opération
                if entry.tool_number != current_tool:
                    if current_tool is not None and current_tool != 0:
                        file.write(
                            f"\n"
                            f"{void.ljust(52)} ==> "
                            f"Distance: {str(round(distance_sum, self.digit_after_point_distance)).ljust(10)}mm   "
                            f"Distance dans la matière: {str(round(distance_in_material_sum, self.digit_after_point_distance)).ljust(10)}mm   "
                            f"Durée: {self.format_time(time_sum).ljust(10)}"
                            f"Durée d'usinage: {self.format_time(productive_time_sum).ljust(10)}"
                            f"Durée imporductif: {self.format_time(time_sum - productive_time_sum)}\n\n"
                        )
                    
                    # Remise des compteurs à 0
                    current_tool = entry.tool_number
                    current_tool_offset = entry.tool_offset
                    time_sum = 0.0
                    productive_time_sum = 0.0
                    distance_sum = 0.0
                    distance_in_material_sum = 0.0
                
                time_sum += entry.time
                productive_time_sum += entry.productive_time
                distance_sum += entry.distance
                distance_in_material_sum += entry.distance_in_material

                # Données ligne
                if entry.move_type == 0 or entry.move_type == 1 :
                    radius = 0.0
                else:
                    radius = entry.radius

                if entry.move_type == 0 :
                    feedrate = self.rapidfeedrate
                else:
                    feedrate = entry.feedrate

                if entry.g_code_line: 
                    file.write(
                        f"{entry.g_code_line.ljust(50)} --> "
                        f"Outil: {str(entry.tool_number).ljust(10)}"
                        f"Correcteur: {str(entry.tool_offset).ljust(10)}"
                        f"Mouvement: {entry.move_type.name.ljust(20)}"
                        f"Plan de travail: {entry.work_plane.name.ljust(10)}"
                        f"Position X: {str(round(entry.endpoint_x, self.digit_after_point_distance)).ljust(10)}"
                        f"Position Y: {str(round(entry.endpoint_y, self.digit_after_point_distance)).ljust(10)}"
                        f"Position Z: {str(round(entry.endpoint_z, self.digit_after_point_distance)).ljust(10)}"
                        f"Position C: {str(round(entry.endpoint_c, self.digit_after_point_distance)).ljust(10)}"
                        f"Rayon: {str(round(radius, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance: {str(round(entry.distance, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance dans la matière: {str(round(entry.distance_in_material, self.digit_after_point_distance)).ljust(10)}"
                        f"Avance: {str(feedrate).ljust(10)}"
                        f"Durée: {str(round(entry.time * 60, self.digit_after_point_time))}s \n"
                    )

            # Données outils dernier outil
            if current_tool is not None and current_tool != 0:
                file.write(
                        f"\n"
                        f"{void.ljust(52)} ==> "
                        f"Distance: {str(round(distance_sum, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance dans la matière: {str(round(distance_in_material_sum, self.digit_after_point_distance)).ljust(10)}"
                        f"Durée: {self.format_time(time_sum)}\n\n"
                    )







    def write_debug_file(self, file_name, program_name, list_datas):
        """Cette méthode crée et écrit un fichier de debug pour analyse"""

        current_tool = None
        current_tool_offset = None
        time_sum = 0.0
        productive_time_sum = 0.0
        distance_sum = 0.0
        void = ""

        program_time = sum(item.time for item in list_datas)
        program_productive_time = sum(item.productive_time for item in list_datas)
        program_imporductive_time = program_time - program_productive_time

        with open(file_name, 'w') as file:
            file.write(f"Programme : {program_name}\n")
            file.write(f"Nombre de lignes du programme : {len(list_datas)}\n")
            file.write(f"Durée du programme : {self.format_time(program_time)}\n")
            file.write(f"Durée d'usinage : {self.format_time(program_productive_time)}\n")
            file.write(f"Durée improductive : {self.format_time(program_imporductive_time)}\n")
            
            for entry in list_datas:

                # Données opération
                if entry.tool_number != current_tool:
                    if current_tool is not None and current_tool != 0:
                        file.write(
                            f"\n"
                            f"{void.ljust(52)} ==> "
                            f"Distance: {str(round(distance_sum, self.digit_after_point_distance)).ljust(10)}mm   "
                            f"Distance dans la matière: {str(round(distance_in_material_sum, self.digit_after_point_distance)).ljust(10)}mm   "
                            f"Durée: {self.format_time(time_sum).ljust(10)}"
                            f"Durée d'usinage: {self.format_time(productive_time_sum).ljust(10)}"
                            f"Durée imporductif: {self.format_time(time_sum - productive_time_sum)}\n\n"
                        )
                    
                    # Remise des compteurs à 0
                    current_tool = entry.tool_number
                    current_tool_offset = entry.tool_offset
                    time_sum = 0.0
                    productive_time_sum = 0.0
                    distance_sum = 0.0
                    distance_in_material_sum = 0.0
                
                time_sum += entry.time
                productive_time_sum += entry.productive_time
                distance_sum += entry.distance
                distance_in_material_sum += entry.distance_in_material

                # Données ligne
                if entry.move_type == 0 or entry.move_type == 1 :
                    radius = 0.0
                else:
                    radius = entry.radius

                if entry.move_type == 0 :
                    feedrate = self.rapidfeedrate
                else:
                    feedrate = entry.feedrate

                if entry.g_code_line: 
                    file.write(
                        f"{entry.g_code_line.ljust(50)} --> "
                        f"Outil: {str(entry.tool_number).ljust(10)}"
                        f"Correcteur: {str(entry.tool_offset).ljust(10)}"
                        f"Mouvement: {entry.move_type.name.ljust(20)}"
                        f"Plan de travail: {entry.work_plane.name.ljust(10)}"
                        f"Position X: {str(round(entry.endpoint_x, self.digit_after_point_distance)).ljust(10)}"
                        f"Position Y: {str(round(entry.endpoint_y, self.digit_after_point_distance)).ljust(10)}"
                        f"Position Z: {str(round(entry.endpoint_z, self.digit_after_point_distance)).ljust(10)}"
                        f"Position C: {str(round(entry.endpoint_c, self.digit_after_point_distance)).ljust(10)}"
                        f"Rayon: {str(round(radius, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance: {str(round(entry.distance, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance dans la matière: {str(round(entry.distance_in_material, self.digit_after_point_distance)).ljust(10)}"
                        f"Avance: {str(feedrate).ljust(10)}"
                        f"Durée: {str(round(entry.time * 60, self.digit_after_point_time))}s \n"
                    )

            # Données outils dernier outil
            if current_tool is not None and current_tool != 0:
                file.write(
                        f"\n"
                        f"{void.ljust(52)} ==> "
                        f"Distance: {str(round(distance_sum, self.digit_after_point_distance)).ljust(10)}"
                        f"Distance dans la matière: {str(round(distance_in_material_sum, self.digit_after_point_distance)).ljust(10)}"
                        f"Durée: {self.format_time(time_sum)}\n\n"
                    )

