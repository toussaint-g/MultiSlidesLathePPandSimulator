%
O1000 (  )
( ------------------------------- )
( Muratec MW40 - Fanuc 31i        )
( PHASE D,usinage.1               )
( Auteur: toussain_g              )
( Vendredi 06.03.2026 - 08:50:31  )
( PP: 312_MuratecMW40_Fanuc31i_04 )
( ------------------------------- )
M9199 (init.)

M18
G28 W0
G28 U0 V0

T3131 ( PORTE-PLAQUETTE EXTÉRIEUR.2 )
M108
( FIN RAYON - G2 )
G97 M4 S15915
G0 G18 Z2.
G1 G98 Z0 F200
G1 G99 X-4. F0.4
G2 X-8. Z-2. I0 K-2.    (R=2.)
G1 Z-4.
G1 G98 X-12. F1000
( FIN RAYON - G3 )
G1 X-8. F200
G1 G99 Z-2. F0.4
G3 X-4. Z0 I2. K0    (R=2.)
G1 X0
G1 G98 Z2. F1000
M109
G28 W0
G28 U0 V0

M18
M45
G97 M4 S2500

G4 X2
M59
G4 X2
M60
G4 X2
M5
M46

G28 U0 V0 W0
M69
M41
M230
M30
%
