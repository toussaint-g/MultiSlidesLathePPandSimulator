%
O1000 (  )
( ------------------------------- )
( Muratec MW40 - Fanuc 31i        )
( PHASE D,usinage.1               )
( Auteur: toussain_g              )
( Vendredi 06.03.2026 - 07:53:28  )
( PP: 312_MuratecMW40_Fanuc31i_04 )
( ------------------------------- )
M9199 (init.)

M18
G28 W0
G28 U0 V0
M5

T3333 ( FRAISE D1.0 X 3 - XXX )
M108
( CONT CANAL2 LATERALE - R+0 - L+0 )
M68 (ACTIVATION AXE C)
G28 H0
G28 G0 V0
M16 (FREIN BROCHE ON)
G97 M13 S15915
G0 X-18. Y-0.2
G0 Z-2.4
G0 X-12.
G1 G98 X-8. F200
G1 G41 Y-0.7 Z-2.2 F318
G2 G19 Y0 Z-1.5 J0.7 K0    (R=0.7)
G1 Y1.2
G2 Y2. Z-2.3 J0 K-0.8    (R=0.8)
G1 Z-3.7
G2 Y1.2 Z-4.5 J-0.8 K0    (R=0.8)
G1 Y-1.2
G2 Y-2. Z-3.7 J0 K0.8    (R=0.8)
G1 Z-2.3
G2 Y-1.2 Z-1.5 J0.8 K0    (R=0.8)
G1 Y0
G2 Y0.7 Z-2.2 J0 K-0.7    (R=0.7)
G1 G40 Y0.2 Z-2.4
G1 X-12. F1000
G0 X-18.
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
M15
M46

G28 U0 V0 W0
M69
M41
M230
M30
%
