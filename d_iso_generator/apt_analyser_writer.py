
# -*- coding: utf-8 -*-

class AptAnalyserWriter:
    """Classe qui permet d'écrire le rapport"""

    def __init__(self, machine_config):
        self.digit_after_point_distance = 3
        self.digit_after_point_time = 4
        try:
            self.rapidfeedrate = machine_config["machineinformations"]["rapidfeedrate"]
        except KeyError:
            raise ValueError("MachineConfigError: Clé 'rapidfeedrate' absente du fichier JSON")






    def write_iso_file(self, file_name, program_name, list_datas):
        """Cette méthode crée et écrit un fichier de debug pour analyse"""

        with open(file_name, 'w') as file:
            file.write(f"%\n")
            file.write(f"O0001\n")
            # file.write(f"Durée du programme : {self.format_time(program_time)}\n")
            # file.write(f"Durée d'usinage : {self.format_time(program_productive_time)}\n")
            # file.write(f"Durée improductive : {self.format_time(program_imporductive_time)}\n")
            
            for entry in list_datas:

                if entry.apt_line: 
                    file.write(
                        f"{entry.apt_line.ljust(50)} --> "
                        
                    )


