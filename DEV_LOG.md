# Suivi de developpement
## Auteur:
**Toussaint Guillaume**
## Le 15/07/2026

## Partie PP:
### Prochaines actions:
- Gestion des synchronisations des canaux.
- Finaliser la partie caxis_move du writer et l'appel depuis le handler (pour les ROTBL).
- Reprendre les mouvements C et Y lors des changements d'outils. Mettre plus d'inteligence car tout sort en dur sans analyse. Ajouter egalement dans la simulation des trajectoires de tournage un C0 (ou C = None) en dur (car doit figurer dans le programme ISO pour que ca marche bien mais aberant dans une partie tournage).
- Tester le full helical en 5x (seulement 3x teste actuellement).
- Faire un test plus complet pour les tool change (plusieurs outils avec des trajectoires 3x et 5x entre chaque changement).
- Faire json avec titres et les definitions plus explicites pour les parametres de json machine.
- Remettre tous les fichiers debug, html, etc... dans le dossier roaming (comme app HE ARC). Les autres??
- Dans le json machine: voir pour les outils de fraisage fixe (T13/14/15 -> X3, T31/36/37 > x2). Quel traitement dans CATIA??
- Revoir tous les TODO.
### Actions futures:
- Separer toutes les briques (generateur, analyseur, simulateur)??
- Creer un HTML pour la generation des gammes avec vue des trajectoires en 3D, etc...
- Voir pour modifier encore le gestion des transition en construisant les etats machine complets (etat courant et last)??
### Points a verifier (dans app):
- Verifier le ROTABL.
### Points a verifier (dans CATIA):
### Ameliorations a prevoir:
- Gestion des spindle on/off: cable avec on/off a chaque changement d'outil. Voir pour mettre plus d'intelligence a ce niveau (pas de on/off si meme broche, etc...).
### Choses a noter dans la doc finale:
- Pas de prise en compte des correcteurs en tournage mais en fraisage uniquement.
- Inversion des coordonnees X basee sur le booleen outil xmirror.
- Pour les machines ayant un peigne monobloc en broche principale (type B075), il faut programmer dans CATIA tous les outils du meme cote (repere canal 1). L'inversion des coordonnees X se fait par le PP.
- Un degagement d'outil en X est ecrit en dur avant les changements d'outil (T0 G0 X...) sans prise en compte de l'axe C courant (le degagement en X sera le meme si C=0 ou C=45). La valeur du X est donne par le hometool X.
- Les outils positionnes avec un vecteur K[0, 1, 0] ne sont pas pris en compte.
- ROTABL:
    - Utilisable en axe C et avec des outils de type MILL frontaux uniquement. Si un autre axe ou un autre type d'outil sont selectionnes, emission d'un message d'erreur.
    - Angle donne relatif avec sens a indiquer egalement dans CATIA.
- Listofspindles du json machine doit refleter les differentes broches definies dans CATIA.
- Dans CATIA pour BW128, 4 broches avec 4 reperes differents doivent-etre crees. Les 3 premiers s'explique simplement (repere representatifs des canaux) mais le 4eme a pour but de pouvoir utiliser les T43 a T47 ou T41 et T42 (canal 3 pour usiner sur COP). Pas d'autres possiblites dans CATIA pour ce point.
- Construction des spindles dans le json:
    - 1: pour broche principale (X1 sur BW128).
    - 2: contre operation (X2 sur BW128).
    - 3: broche principale avec X inverse (X3 sur BW128).
    - 4: contre operation avec X inverse (X3 sur BW128).
- Mouvements G2/G3 traites uniquement avec IJK. R non pris en charge.


## Partie analyse:
### Prochaines actions:
### Actions futures:
### Points a verifier (dans app):
### Points a verifier (dans CATIA):
### Ameliorations a prevoir:
### Choses a noter dans la doc finale:
- Les infos de l'analyse sont donnees avec X au rayon dans tous les cas (meme si true ou false dans JSON).

## Partie viewer:
### Prochaines actions:
### Actions futures:
### Points a verifier (dans app):
### Points a verifier (dans CATIA):
### Ameliorations a prevoir:
### Choses a noter dans la doc finale:
- Les coordonnees affichees sont toujours au rayon.
- Les hometool sont appliques par le simulateur pour determiner le 1er point de la trajectoire de l'outil courant.