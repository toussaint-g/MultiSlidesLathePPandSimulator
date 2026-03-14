# -*- coding: utf-8 -*-

import json


class MachinesConfigLoader:
    """Cette classe permet de gérer la configuration des machines (json)"""
    data = {}
    machines_list = {}

    @staticmethod
    def load_config():
        """Charge le fichier JSON et split application / machineslist"""
        try:
            with open('b_machines_config\\machines_config.json', 'r', encoding='utf-8') as file:
                MachinesConfigLoader.data = json.load(file)

            MachinesConfigLoader.machines_list = MachinesConfigLoader.data.get('machineslist', {})

        except FileNotFoundError:
            raise FileNotFoundError(
                'Erreur : Le fichier des configurations machines (.json) est introuvable.'
            )

    @staticmethod
    def get_machines_names():
        """Retourne la liste des noms de machines (clés du JSON)"""
        return sorted(MachinesConfigLoader.machines_list.keys())

    @staticmethod
    def get_channels_list():
        """Retourne la liste des canaux pour la première machine disponible"""
        machine_names = MachinesConfigLoader.get_machines_names()
        if not machine_names:
            return []
        return MachinesConfigLoader.get_channels_list_for_machine(machine_names[0])

    @staticmethod
    def get_channels_list_for_machine(machine_name: str):
        """Retourne la liste des canaux d'une machine donnée"""
        machine_config = MachinesConfigLoader.get_machine(machine_name)
        channels = machine_config.get('channelslist', {})
        return sorted(channels.keys())

    @staticmethod
    def get_machine(machine_name: str):
        """Retourne le dict de la machine"""
        return MachinesConfigLoader.machines_list.get(machine_name, {})
