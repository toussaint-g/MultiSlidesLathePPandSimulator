# PPandSimulatorForMultiSlidesLathe

## Auteur:
**Toussaint Guillaume**

## Description:
Ce développement a pour objectifs:
- De fournir une application capable de **générer du code ISO depuis les fichiers APT de CATIA V5**.
- D'**analyser les temps d'usinage et les distances parcourues** par chaque outil.
- De **simuler du code ISO** avec une représentation 3D (STL) de la pièce et des trajectoires des outils sous forme filaire.

Les machines cibles de ce projet sont des **décolleteuses CNC multi-canaux TSUGAMI avec commande FANUC**.

## Test:
Pour tester l'application, vous pouvez utilier les fichiers présents dans le répertoire "data_testing".

## Manipulateur du viewer 3D:
Différentes touches permettent d'exécuter des fonctions spécifiques:
- "Space" → masquer/afficher la pièce.
- "Escape" → masquer/afficher toutes les trajectoires.
- "Up" et "Down" → défiliement des trajectoires rapide et travail par outil.

## Améliorations futures:
### Générateur de code ISO depuis APT:
- Gestion des multi-canaux directement depuis CATIA V5.
- Traitement fichier APT unique pour tous canaux.
### Simulateur 3D:
- Défilement outil sur la trajectoire (avec représentation outil différencier tournage/fraisage).