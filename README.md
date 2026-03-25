# PPandSimulatorForMultiSlidesLathe

## Auteur:
**Toussaint Guillaume**

## Description:
Ce developpement a pour objectifs:
- De fournir une application capable de **generer du code ISO depuis les fichiers APT de CATIA V5**.
- D'**analyser les temps d'usinage et les distances parcourues** par chaque outil.
- De **simuler du code ISO** avec une representation 3D (STL) de la piece et des trajectoires des outils sous forme filaire.

Les machines cibles de ce projet sont des **decolleteuses CNC multi-canaux TSUGAMI avec commande FANUC**.

## Test:
Pour tester l'application, vous pouvez utilier les fichiers presents dans le repertoire "data_testing".

## Manipulateur du viewer 3D:
Differentes touches permettent d'executer des fonctions specifiques:
- "Space"  masquer/afficher la piece.
- "Escape"  masquer/afficher toutes les trajectoires.
- "Up" et "Down"  defiliement des trajectoires rapide et travail par outil.

## Ameliorations futures:
### Generateur de code ISO depuis APT:
- Gestion des multi-canaux directement depuis CATIA V5.
- Traitement fichier APT unique pour tous canaux.
### Simulateur 3D:
- Defilement outil sur la trajectoire (avec representation outil differencier tournage/fraisage).