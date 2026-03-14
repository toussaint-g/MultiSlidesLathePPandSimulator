# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
from functools import partial
import re
from enum import Enum


# -----------------------------
# Etat du post-processeur
# -----------------------------
@dataclass
class State:
    """L'etat courant de la machine tel que "vu" par le post-processeur."""

    motion: str = "RAPID"

    # Etats usuels
    channel: Optional[int] = None
    feed: Optional[float] = None
    spindle: Optional[float] = None
    spindle_dir: Optional[str] = None  # "CW" / "CCW"
    tool: Optional[int] = None
    coolant: bool = False

    # Derniere position connue
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Meta
    line_no: int = 0


# -----------------------------
# Outils formatage ISO
# -----------------------------
def format_float_to_iso(numeric_value: float) -> str:
    """Formatte un nombre pour l'ISO en supprimant les zeros inutiles."""
    formatted_value = f"{numeric_value:.3f}".rstrip("0").rstrip(".")
    return formatted_value if formatted_value else "0"

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

class WorkPlaneType(Enum):
    """Enum pour mémoriser les types de plan de travail"""
    XY = [0.0, 0.0, 1.0]
    XZ = [0.0, 1.0, 0.0]
    YZ = [1.0, 0.0, 0.0]


class IsoWriter:
    """Helper pour construire un programme ISO ligne par ligne a partir de l'etat du post-processeur."""

    def __init__(self, machine_config, channel_name) -> None:
        """Initialise le writer avec un etat vide et une liste de lignes ISO vide."""
        # out contient le programme ISO final, ligne par ligne.
        self.out: list[str] = []
        # Ces caches evitent de remettre F et S si la valeur n'a pas change.
        self.last_f: Optional[float] = None
        self.last_s: Optional[float] = None


        try:
            self.machine_config = machine_config
            self.channel_name = channel_name
            self.calculation_tolerance = self.machine_config["calculationtolerance"]
            # machineinformations
            # self.rapidfeedrate = self.machine_config["machineinformations"]["rapidfeedrate"]
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
            # self.activate_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingBP"])
            # self.disable_c_axis_indexing_BP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingBP"])
            # self.activate_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["activatecaxisindexingCOP"])
            # self.disable_c_axis_indexing_COP = _normalize_gm_code(self.machine_config["machineinformations"]["disablecaxisindexingCOP"])
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


    def emit(self, iso_line: str) -> None:
        """Ajoute une ligne ISO a la sortie."""
        self.out.append(iso_line)

    def comment(self, comment_text: str) -> None:
        """Ajoute un commentaire ISO a la sortie."""
        self.emit(f"({comment_text})")

    def header(self) -> None:
        """Ajoute l'en-tête minimal pour un programme de fraisage en coordonnées absolues."""
        self.emit("%")
        self.emit(f"O{self.channel_name}000")
        self.emit("G94")

    def footer(self) -> None:
        """Ajoute le pied de page minimal pour un programme de fraisage."""
        self.emit("M30")
        self.emit("%")

    def set_feed(self, feed_rate: float) -> None:
        """Met à jour l'avance et l'écrit en ISO si elle a changé."""
        if self.last_f != feed_rate:
            self.emit(f"F{format_float_to_iso(feed_rate)}")
            self.last_f = feed_rate

    def set_spindle(self, spindle_speed: float, spindle_direction: str) -> None:
        """Met à jour la vitesse de broche et la direction, et l'écrit en ISO si elle a changé."""
        if self.last_s != spindle_speed:
            self.emit(f"S{format_float_to_iso(spindle_speed)}")
            self.last_s = spindle_speed
        self.emit("M3" if spindle_direction == "CW" else "M4")

    def spindle_stop(self) -> None:
        """Arrête la broche."""
        self.emit("M5")

    def coolant_on(self) -> None:
        """Active le liquide de refroidissement."""
        self.emit("M8")

    def coolant_off(self) -> None:
        """Désactive le liquide de refroidissement."""
        self.emit("M9")

    def tool_change(self, tool_number: int) -> None:
        """Change l'outil."""
        self.emit(f"T{'0' if tool_number < 10 else ''}{tool_number} M6") # Formatage de l'outil avec un zéro devant si < 10, pour correspondre au format Txx attendu par la machine

    def move(self, motion_mode: str, x=None, y=None, z=None) -> None:
        """Déplace la machine selon le mode spécifié et les coordonnées fournies."""
        motion_code = "G0" if motion_mode == "RAPID" else "G1"
        axis_words = [motion_code]
        if x is not None:
            axis_words.append(f"X{format_float_to_iso(x)}")
        if y is not None:
            axis_words.append(f"Y{format_float_to_iso(y)}")
        if z is not None:
            axis_words.append(f"Z{format_float_to_iso(z)}")
        self.emit(" ".join(axis_words))


# -----------------------------
# Parsing APT (rigide)
# -----------------------------
def strip_comments(line_text: str) -> str:
    """Retire les commentaires inline pour simplifier le parsing."""
    stripped_line = line_text.rstrip("\n")
    for marker in ("!", "#", "//"):
        if marker in stripped_line:
            stripped_line = stripped_line.split(marker, 1)[0]
    return stripped_line.strip()


def parse_keyword_and_rhs(line_text: str) -> tuple[Optional[str], str]:
    """Extrait le mot-clé APT et le texte d'argument d'une ligne de code APT."""
    cleaned_line = strip_comments(line_text)
    if not cleaned_line:
        return None, ""

    if "/" in cleaned_line:
        apt_keyword, argument_text = cleaned_line.split("/", 1)
        return apt_keyword.strip().upper(), argument_text.strip()

    # fallback format "KEY args"
    apt_keyword, _, argument_text = cleaned_line.partition(" ")
    return apt_keyword.strip().upper(), argument_text.strip()


def csv_floats(argument_text: str) -> list[float]:
    """Parse une liste de nombres flottants séparés par des virgules, en tolérant les espaces."""
    # Utilitaire pour les commandes du type GOTO/x,y,z
    return [float(token.strip()) for token in argument_text.split(",") if token.strip()]


def csv_tokens(argument_text: str) -> list[str]:
    """Parse une liste de tokens séparés par des virgules, en tolérant les espaces."""
    return [token.strip() for token in argument_text.split(",") if token.strip()]


# -----------------------------
# Handlers APT -> ISO
# -----------------------------
# Chaque handler traduit une instruction APT en mise a jour d'etat
# et/ou en emission d'une ou plusieurs lignes ISO.
Handler = Callable[[str, str, State, IsoWriter], None]




def h_comment(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter, text_info: str | None = None) -> None:
    """Gère les commandes de type commentaire en les écrivant telles quelles dans un commentaire ISO."""
    iso_writer.comment(f"{text_info}: {argument_text.upper()}" if text_info else argument_text.upper())


def h_channel(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Gère la commande CHANNEL en la commentant dans l'ISO."""
    channel_tokens = csv_tokens(argument_text)
    channel_number = int(float(channel_tokens[0]))
    state.channel = channel_number
    iso_writer.tool_change(channel_number)






def h_fedrat(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Met à jour l'avance et l'écrit en ISO si elle a changé."""
    feed_rate = float(argument_text)
    state.feed = feed_rate
    iso_writer.set_feed(feed_rate)


def h_spindl(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Met à jour la vitesse de broche et la direction, et l'écrit en ISO si elle a changé."""
    # Exemple accepte : SPINDL/3000,CLW
    spindle_tokens = [token.upper() for token in csv_tokens(argument_text)]
    if not spindle_tokens:
        return

    spindle_speed = float(spindle_tokens[0])
    if any(token in ("CLW", "CW", "M3") for token in spindle_tokens[1:]):
        spindle_direction = "CW"
    elif any(token in ("CCLW", "CCW", "M4") for token in spindle_tokens[1:]):
        spindle_direction = "CCW"
    else:
        spindle_direction = "CW"

    state.spindle = spindle_speed
    state.spindle_dir = spindle_direction
    iso_writer.set_spindle(spindle_speed, spindle_direction)


def h_spstop(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Arrête la broche."""
    state.spindle = None
    state.spindle_dir = None
    iso_writer.spindle_stop()


def h_coolnt(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Active ou désactive le liquide de refroidissement."""
    coolant_command = argument_text.strip().upper()
    if coolant_command == "ON":
        state.coolant = True
        iso_writer.coolant_on()
    elif coolant_command == "OFF":
        state.coolant = False
        iso_writer.coolant_off()
    else:
        iso_writer.comment(f"COOLNT non reconnu: {argument_text}")


def h_loadtl(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Change l'outil."""
    tool_tokens = csv_tokens(argument_text)
    tool_number = int(float(tool_tokens[0]))
    state.tool = tool_number
    iso_writer.tool_change(tool_number)


def h_rapid(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Le prochain GOTO utilisera G0."""
    state.motion = "RAPID"


def h_linear(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Le prochain GOTO utilisera G1."""
    state.motion = "LINEAR"


def h_goto(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Déplace la machine selon le mode spécifié et les coordonnées fournies."""
    coordinates = csv_floats(argument_text)
    x = coordinates[0] if len(coordinates) >= 1 else None
    y = coordinates[1] if len(coordinates) >= 2 else None
    z = coordinates[2] if len(coordinates) >= 3 else None

    if x is not None:
        state.x = x
    if y is not None:
        state.y = y
    if z is not None:
        state.z = z

    iso_writer.move(state.motion, x=x, y=y, z=z)


def h_fini(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Termine le programme ISO."""
    iso_writer.footer()


def h_default(apt_keyword: str, argument_text: str, state: State, iso_writer: IsoWriter) -> None:
    """Gère les commandes non reconnues en les commentant."""
    iso_writer.comment(f"NON GERE: {apt_keyword}/{argument_text}".strip())


DISPATCH: dict[str, Handler] = {
    # "FEDRAT": h_fedrat,
    # "SPINDL": h_spindl,
    # "SPSTOP": h_spstop,
    # "COOLNT": h_coolnt,
    
    # "LINEAR": h_linear,
    

    # Path
    "CHANNEL" : partial(h_comment, text_info="CHANNEL"),



    
    # Trajectoires
    "RAPID": h_rapid,
    "GOTO": h_goto,
    "END": h_fini,
    # Meta-informations (commentées dans l'ISO)
    #"PARTNO": h_comment(text_info="PART NUMBER"), # Voir si utile...
    "PART_OPE": partial(h_comment, text_info="PHASE"),
    "PROGRAM": partial(h_comment, text_info="PROGRAMME"),
    "MACHINE": partial(h_comment, text_info="MACHINE"),
    "CATPROCESS": partial(h_comment, text_info="CATPROCESS"),
    "CATPRODUCT": partial(h_comment, text_info="CATPRODUCT"),
    # Commentaires généraux
    "PPRINT": h_comment,
    # Outils
    "TPRINT": h_comment,
    "LOADTL": h_loadtl,
}






def apt_to_iso_lines(apt_lines: list[str], machine_config, channel_name) -> list[str]:
    """Convertit une liste de lignes APT en lignes ISO."""
    state = State()
    iso_writer = IsoWriter(machine_config, channel_name)
    iso_writer.header()

    for line_number, line_text in enumerate(apt_lines, start=1):
        state.line_no = line_number
        apt_keyword, argument_text = parse_keyword_and_rhs(line_text)
        if apt_keyword is None:
            continue

        handler = DISPATCH.get(apt_keyword, h_default)
        handler(apt_keyword, argument_text, state, iso_writer)

        # END termine explicitement le programme APT.
        if apt_keyword == "END":
            break

    # Securite : si pas de END, on termine quand meme
    if not iso_writer.out or iso_writer.out[-1] != "%": # Si le programme n'est pas termine, on ajoute un pied de page
        if "M30" not in iso_writer.out[-5:]: # Si le pied de page n'est pas deja present, on l'ajoute
            iso_writer.footer()

    return iso_writer.out


def convert_file(input_path: str, output_path: str, machine_config, channel_name) -> None:
    """Convertit un fichier APT en fichier ISO en utilisant les handlers définis ci-dessus."""
    with open(input_path, "r", encoding="utf-8", errors="replace") as input_file:
        apt_lines = input_file.readlines()

    iso_lines = apt_to_iso_lines(apt_lines, machine_config, channel_name)

    with open(output_path, "w", encoding="utf-8", newline="\n") as output_file:
        output_file.write("\n".join(iso_lines) + "\n")
