#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Halterung fuer die Tram-Abfahrtsanzeige (LilyGO T-Display S3, Querformat).

Vorbild: die VAG-DFI am Paula-Modersohn-Platz. Dunkle Tafel mit Sichtfenster,
darueber der rote Querbalken; die Tafel haengt LINKS neben dem Mast, der Mast
laeuft hinter der Tafel vom Sockel bis ueber den Balken.

Kein Lampenkopf (die Leuchte auf dem Foto gehoert zu einem anderen Mast).

Gesamthoehe 210 mm; Tafel 70 x 42 mm -> Massstab ca. 1:14.

Der USB-C-Anschluss sitzt in der RUECKWAND des Sockels. Ein Kabel laeuft vom
Board durch die Tafel, in den hohlen Mast und im Sockel ueber einen gefuehrten
Kanal zum Einbau-Stecker. Der Sockel ist hohl (kein Sand) -- der Kanal haelt das
Kabel auf seinem Weg.

Achsen:  X = Breite, Y = Tiefe (-Y = Front/Blickrichtung), Z = Hoehe. Masse in mm.
"""
import os
import math
import numpy as np
import trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")
PREV = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

# --------------------------------------------------------------- PARAMETER
# Platine -- gemessen aus LilyGO "dimensions/t-display-s3-full.stl"
BOARD_W, BOARD_H, BOARD_T = 61.98, 26.09, 9.88   # Querformat: Laenge x Hoehe x Tiefe
BOARD_Y = 0.76                                    # Platinenruecken liegt am Deckel an
ACT_W, ACT_H = 42.63, 22.65                       # aktive Flaeche 1,9" (320:170)

# Tafelgehaeuse (Front zeigt nach -Y); Bauteil wird um (0,0) gebaut
GH_W, GH_H, GH_D = 78.0, 42.0, 16.0   # Laenge >= 72 mm: Platine 62 + Stecker/Kabel
FRONT, WALL, BACK_T = 2.5, 2.5, 2.5
CAV_D = GH_D - FRONT - BACK_T                     # 11,0 Innentiefe
WIN_W, WIN_H, WIN_R = 45.0, 25.0, 2.0   # Sichtfenster = reine Bildschirmgroesse
WIN_DX = 1.81                             # LCD liegt 1,81 mm aus der Platinenmitte (off. STL)
WIN_DZ = -0.29                            # ... und 0,29 mm quer dazu (off. STL)
# Vertiefung in der Frontwand: nimmt das LCD-Glas auf und zentriert die Platine
GLASS_W, GLASS_H, GLASS_T = 49.87, 25.95, 1.53   # LCD-Modul (off. STL)
REC_D = 1.60                              # Tiefe der Vertiefung (Glas 1,53, Front buendig)
REC_W, REC_H = GLASS_W + 0.6, GLASS_H + 0.6      # Spiel 0,30 mm je Seite
POST_R, PILOT_R = 2.5, 1.25
RIB_T, RIB_D = 1.4, 3.0
PAD_T = 4.70                                       # Druckpolster im Deckel (haelt die Platine vorn)
FRONT_IN = -16.0 / 2 + 2.5                         # Innenflaeche der Frontwand (y = -5,5)
REC_IN = FRONT_IN - REC_D                          # hintere Flaeche der Vertiefung (y = -7,1)

PANEL_X = -26.0                                   # Tafelmitte (Mast sitzt rechts daneben)
SIGN_Z0, SIGN_Z1 = 136.0, 178.0

# Mast -- steht HINTER der Tafel (y) und an deren rechtem Rand (x)
POLE_X, POLE_Y = 8.0, 22.0
POLE_W, POLE_D = 12.0, 9.0                        # eckiger Vierkantmast (X x Y), Vorbild
POLE_T = 2.0                                      # Wandstaerke -> innen 8 x 5 (Kabel)
CABLE_Z = 150.0                                   # Kabelaustritt aus dem Mast

# Querbalken (rot) + Arm zur Schelle
BAR_OVER = 5.0                                    # Ueberstand ueber die Blende, je Seite
BAR_X0 = PANEL_X - GH_W / 2 - BAR_OVER            # -70,0
BAR_X1 = PANEL_X + GH_W / 2 + BAR_OVER            # +18,0
BAR_Y0, BAR_Y1 = -5.0, 5.0
BAR_H = 6.0
ARM_HW = 6.0                                      # halbe Armbreite
ARM_Y1 = 17.0                                     # Armende: reicht ueber die Schellen-Auflage
ARM_SCREW_DX = 3.5                                # Schraubenabstand quer
ARM_SCREW_Y = -6.5                                # Schraubenebene (lokal, in der Schellen-Frontwand)
ARM_SCREW_Y_G = POLE_Y + ARM_SCREW_Y              # 15,5 global
SCREW_DX = 24.0                                   # Schraubenabstand, ab Tafelmitte
SCREW_LOCAL = (-SCREW_DX, SCREW_DX)               # in der Blende (lokal)
SCREW_GLOBAL = (PANEL_X - SCREW_DX, PANEL_X + SCREW_DX)   # im Balken (global)

# Schelle -- Oberkante liegt auf der Balkenunterkante (SIGN_Z1)
CLAMP_T, CLAMP_H, SLIT_W, SCREW_R = 4.0, 10.0, 2.0, 1.6
CLAMP_Z0, CLAMP_Z1 = SIGN_Z1 - CLAMP_H, SIGN_Z1

# Sockel
BASE_X, BASE_Y, BASE_H = 120.0, 90.0, 16.0         # flacher Sockel
BW, BOSS_H = 3.0, 3.0
BASE_TOP = BASE_H + BOSS_H                        # 19,0
USB_W, USB_H = 13.4, 10.2                         # Einbaubuchse: Breite x Hoehe (gemessen)
USB_BOSS_Y, USB_BOSS_T = 5.0, 34.0                # Wandverstaerkung innen (bleibt in der Sockelhoehe)
USB_BOSS_H = 12.0
USB_Z = 8.0
RIB_HW = 8.0                                      # halbe Breite des Kabelkanals
TUN_HW, TUN_Z0, TUN_Z1 = 5.0, 5.0, 11.0           # Kanal im Sockel
POLE_TOP = 210.0
TOTAL_H = POLE_TOP

# ------------------------------------------------------------------ Helfer
def bx(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    m = box(extents=(sx, sy, sz)); m.apply_translation((x, y, z)); return m

def cyz(r, h, x=0.0, y=0.0, z=0.0, sec=64):
    m = cylinder(radius=r, height=h, sections=sec); m.apply_translation((x, y, z)); return m

def cyy(r, h, x=0.0, y=0.0, z=0.0, sec=64):
    m = cylinder(radius=r, height=h, sections=sec)
    m.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0])); m.apply_translation((x, y, z)); return m

def cyx(r, h, x=0.0, y=0.0, z=0.0, sec=64):
    m = cylinder(radius=r, height=h, sections=sec)
    m.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0])); m.apply_translation((x, y, z)); return m

def uni(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = trimesh.boolean.union([out, m])
    return out

def dif(a, *ms):
    return trimesh.boolean.difference([a, *ms])

def rrect_xz(w, h, t, r, x=0.0, z=0.0):
    """Abgerundetes Rechteck in der X-Z-Ebene, Dicke t entlang Y."""
    p = [bx(w, t, h - 2 * r + 0.02), bx(w - 2 * r + 0.02, t, h)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(cyy(r, t, sx * (w / 2 - r), 0, sz * (h / 2 - r)))
    m = uni(*p); m.apply_translation((x, 0, z)); return m

def posts():
    px = GH_W / 2 - WALL - POST_R
    pz = GH_H / 2 - WALL - POST_R
    return px, pz, [(sx * px, sz * pz) for sx in (-1, 1) for sz in (-1, 1)]

# ------------------------------------------------------------------- Teile
def part_housing():
    """Blende: 78 x 42 x 16; Frontwand mit Sichtfenster + Glasvertiefung, Ruecken offen."""
    zc = GH_H / 2
    outer = bx(GH_W, GH_D, GH_H, 0, 0, zc)
    cav_d = GH_D - FRONT + 4.0                       # Kavitaet bis hinter die Rueckebene
    cav_y = -GH_D / 2 + FRONT + cav_d / 2
    cav = bx(GH_W - 2 * WALL, cav_d, GH_H - 2 * WALL, 0, cav_y, zc)
    m = dif(outer, cav)
    # Sichtfenster durch die Frontwand
    win = rrect_xz(WIN_W, WIN_H, FRONT + 8, WIN_R, WIN_DX, zc + WIN_DZ)
    win.apply_translation((0, -GH_D / 2 + FRONT / 2, 0))
    m = dif(m, win)
    # Glasvertiefung in der Innenflaeche: die Platine wird darin zentriert und das
    # Fenster liegt ohne Spalt genau ueber dem Bildschirm.
    m = dif(m, bx(REC_W, REC_D, REC_H, WIN_DX, FRONT_IN - REC_D / 2, zc + WIN_DZ))

    px, pz, P = posts()
    post_h = GH_D - FRONT - 1.5                      # Schraubdome bleiben in der Kavitaet
    post_y = FRONT_IN + post_h / 2
    add = [cyy(POST_R, post_h, x, post_y, zc + z) for x, z in P]
    m = uni(m, *add)
    # Stege unter der Deckwand: geben der Schraube echtes Gewinde (Wand allein 2,5)
    m = uni(m, *[bx(7.0, 7.0, 4.0, lx, 0, GH_H - WALL - 2.0) for lx in SCREW_LOCAL])
    # Gewinde fuer den Querbalken (von oben durch die Deckwand) -- Kernloch M3
    m = dif(m, *[cyz(1.25, 9, lx, 0, GH_H - 1.5) for lx in SCREW_LOCAL])
    m = dif(m, *[cyy(PILOT_R, 9.0, x, post_y + 1.5, zc + z) for x, z in P])   # Sackloch, 3 mm Rest
    return m

def part_cover():
    """Rueckdeckel mit Passrand, Kabelloch + Kabelstutzen zum Mast, Lueftung."""
    zc = GH_H / 2
    m = uni(bx(GH_W, BACK_T, GH_H, 0, GH_D / 2 + BACK_T / 2, zc),
            bx(GH_W - 2 * WALL - 0.6, 1.2, GH_H - 2 * WALL - 0.6, 0, GH_D / 2 - 0.6, zc))
    # Anpresspolster: druecken die Platine nach vorn in die Fenstervertiefung
    pad_y = GH_D / 2 - 0.6 - PAD_T / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            m = uni(m, bx(8.0, PAD_T, 8.0, sx * (BOARD_W / 2 - 6.0), pad_y,
                          zc + sz * (BOARD_H / 2 - 6.0)))
    px, pz, P = posts()
    m = dif(m, *[cyy(1.6, BACK_T + 6, x, GH_D / 2 + BACK_T / 2, zc + z) for x, z in P])
    lx = POLE_X - PANEL_X                                # Kabelstutzen auf Mastachse
    lz = CABLE_Z - SIGN_Z0
    m = uni(m, cyy(6.0, 11.0, lx, GH_D / 2 + 5.5, lz))   # Stutzen zur Mastwand
    m = dif(m, cyy(4.0, 18.0, lx, GH_D / 2 + 5.0, lz))   # Kabeldurchfuehrung
    vents = [bx(3.0, BACK_T + 4, 1.6, i * 6.0, GH_D / 2 + BACK_T / 2, zc + sz * 15.0)
             for i in range(-2, 3) for sz in (-1, 1)]
    return dif(m, *vents)

def part_crossbar():
    """Roter Querbalken mit Arm zur Schelle. Z=0 ist die Tafeloberkante."""
    rail = bx(BAR_X1 - BAR_X0, BAR_Y1 - BAR_Y0, BAR_H,
              (BAR_X0 + BAR_X1) / 2, 0, BAR_H / 2)
    arm = bx(2 * ARM_HW, ARM_Y1 - BAR_Y1, BAR_H, POLE_X, (BAR_Y1 + ARM_Y1) / 2, BAR_H / 2)
    m = uni(rail, arm)
    m = dif(m, *[cyz(1.6, BAR_H + 3, lx, 0, BAR_H / 2) for lx in SCREW_GLOBAL])   # Durchgang Tafelschrauben
    # Senkrechte Schrauben von oben durch den Arm in die Schelle (Durchgangsbohrung)
    m = dif(m, *[cyz(1.6, 10, POLE_X + sx * ARM_SCREW_DX, ARM_SCREW_Y_G, BAR_H / 2)
                 for sx in (-1, 1)])
    return m

def part_clamp():
    """Eckige Schelle um den Vierkantmast. Ein Schlitz in der RUECKWAND macht sie zur
    Klemme (vorne bleibt ein Steg als Scharnier): die Schraube quer (Achse X) zieht
    die beiden Schlitzseiten zusammen. Oben liegt die Auflage fuer den Balkenarm."""
    zc = CLAMP_H / 2
    ow, od = POLE_W + 2 * CLAMP_T, POLE_D + 2 * CLAMP_T
    yc = POLE_D / 2 + CLAMP_T / 2                     # Mitte der Rueckwand
    m = bx(ow, od, CLAMP_H, 0, 0, zc)
    m = dif(m, bx(POLE_W + 0.4, POLE_D + 0.4, CLAMP_H + 4, 0, 0, zc))   # Mastdurchlass
    # Schlitz nur in der Rueckwand -> Klemme mit Scharnier, zerfaellt nicht
    m = dif(m, bx(SLIT_W, CLAMP_T + 2.0, CLAMP_H + 4, 0, yc, zc))
    # Klemmschraube quer (Achse X), beide Bohrungen auf derselben Achse:
    # links Durchgang, rechts Kernloch -> die Schraube zieht den Schlitz zu
    m = dif(m, cyx(SCREW_R, 9.0, -(SLIT_W / 2 + 4.5), yc, zc))                # links Durchgang
    m = dif(m, cyx(SCREW_R - 0.35, 7.0, SLIT_W / 2 + 3.5, yc, zc))            # rechts Kernloch
    m = dif(m, cyx(SCREW_R + 1.5, 3.0, -(ow / 2 - 0.6), yc, zc))              # Kopfsenke
    # Gewinde fuer den Querbalkenarm (senkrecht von oben)
    m = dif(m, *[cyz(1.25, 6.5, sx * ARM_SCREW_DX, ARM_SCREW_Y, CLAMP_H - 3.25)
                 for sx in (-1, 1)])
    return m

def part_pole():
    """Hohler Vierkantmast (eckig wie das Vorbild); Kabelaustritt auf Tafelhoehe."""
    h = POLE_TOP - BASE_TOP
    m = bx(POLE_W, POLE_D, h, 0, 0, h / 2)
    m = dif(m, bx(POLE_W - 2 * POLE_T, POLE_D - 2 * POLE_T, h + 4, 0, 0, h / 2))
    m = dif(m, cyy(3.0, POLE_D + 8, 0, 0, CABLE_Z - BASE_TOP))
    return m

def part_base():
    """Flacher Sockel: hohl, gefuehrter Kabelkanal, rechteckiges Buchsenloch."""
    zc = BASE_H / 2
    ow, od = POLE_W + 2 * CLAMP_T, POLE_D + 2 * CLAMP_T
    m = bx(BASE_X, BASE_Y, BASE_H, 0, 0, zc)
    m = dif(m, bx(BASE_X - 2 * BW, BASE_Y - 2 * BW, BASE_H - 2 * BW, 0, 0, zc))
    # Kanalrumpf: fuehrt das Kabel im hohlen Sockel zum Stecker
    m = uni(m, bx(2 * RIB_HW, 26.0, BASE_H - 2 * BW, POLE_X, 31.0, zc))
    m = uni(m, bx(ow, od, BOSS_H, POLE_X, POLE_Y, BASE_H + BOSS_H / 2))   # Mastkragen
    # Loch der Einbaubuchse (gemessenes Mass) + Wandverstaerkung innen
    m = uni(m, bx(USB_BOSS_T, USB_BOSS_Y, USB_BOSS_H, POLE_X,
                  BASE_Y / 2 - BW - USB_BOSS_Y / 2, USB_Z))
    m = dif(m, bx(USB_W, 24.0, USB_H, POLE_X, BASE_Y / 2, USB_Z))
    m = dif(m, bx(2 * TUN_HW, 30.0, TUN_Z1 - TUN_Z0, POLE_X, 32.0, (TUN_Z0 + TUN_Z1) / 2))
    # Mastkanal (Kabel) + Steckfassung fuer den Vierkantmast
    m = dif(m, bx(POLE_W - 2 * POLE_T, POLE_D - 2 * POLE_T, BASE_H - 5, POLE_X, POLE_Y,
                  5 + (BASE_H - 5) / 2))
    m = dif(m, bx(POLE_W + 0.6, POLE_D + 0.6, BOSS_H + 2.0, POLE_X, POLE_Y,
                  BASE_H + BOSS_H / 2 + 1.0))
    return m

PARTS = [
    ("01_blende",      "Blende (Tafelgehaeuse)", part_housing),
    ("02_rueckdeckel", "Rueckdeckel",            part_cover),
    ("03_querbalken",  "Querbalken rot",         part_crossbar),
    ("04_schelle",     "Mastschelle",            part_clamp),
    ("05_mast",        "Mast (hohl)",            part_pole),
    ("06_sockel",      "Sockel",                 part_base),
]

def to_bed(m):
    m2 = m.copy(); m2.apply_translation((0, 0, -m2.bounds[0][2])); return m2

# ------------------------------------------------------------- Montagebild
def assembly():
    items = []
    h = part_housing(); h.apply_translation((PANEL_X, 0, SIGN_Z0))
    items.append(("Blende", h, (0.05, 0.05, 0.06)))          # schwarz
    c = part_cover(); c.apply_translation((PANEL_X, 0, SIGN_Z0))
    items.append(("Rueckdeckel", c, (0.09, 0.09, 0.10)))     # schwarz
    b = part_crossbar(); b.apply_translation((0, 0, SIGN_Z1))
    items.append(("Querbalken", b, (0.78, 0.12, 0.10)))      # rot
    cl = part_clamp(); cl.apply_translation((POLE_X, POLE_Y, CLAMP_Z0))
    items.append(("Schelle", cl, (0.90, 0.90, 0.91)))        # weiss (Mast)
    pl = part_pole(); pl.apply_translation((POLE_X, POLE_Y, BASE_TOP))
    items.append(("Mast", pl, (0.95, 0.95, 0.96)))           # weiss
    items.append(("Sockel", part_base(), (0.05, 0.05, 0.06)))  # schwarz
    return items

# -------------------------------------------------------------- Darstellung
def _shade_and_project(items, keep):
    dep = ({0, 1, 2} - set(keep)).pop()
    L = np.array([0.45, -0.55, 0.70]); L /= np.linalg.norm(L)
    T, C, D = [], [], []
    for _, m, col in items:
        sh = np.clip(m.face_normals @ L, 0, 1) * 0.55 + 0.45
        T.append(m.triangles[:, :, keep].copy())
        C.append(np.clip(sh[:, None] * np.array(col)[None, :], 0, 1))
        D.append(m.triangles[:, :, dep].mean(axis=1))
    tris, cols, dep = np.concatenate(T), np.concatenate(C), np.concatenate(D)
    o = np.argsort(-dep)                       # Vorderes zuletzt zeichnen
    return tris[o], cols[o]

def save_png(items, keep, fname, title, xlabel, ylabel, size=(9, 5)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig, ax = plt.subplots(figsize=size)
    tris, cols = _shade_and_project(items, keep)
    ax.add_collection(PolyCollection(tris, facecolors=cols, edgecolors="none"))
    ax.autoscale(); ax.set_aspect("equal")
    ax.grid(alpha=0.3, linestyle=":")
    ax.set_title(title, fontsize=10); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    sx = x0 + (x1 - x0) * 0.03; sy = y0 + (y1 - y0) * 0.05
    ax.plot([sx, sx + 100], [sy, sy], color="black", lw=2.5)
    ax.text(sx + 50, sy + (y1 - y0) * 0.02, "100 mm", ha="center", fontsize=8)
    fig.savefig(fname, dpi=110, bbox_inches="tight"); plt.close(fig)
    print("  ->", os.path.basename(fname))

# --------------------------------------------------------------- Pruefung
def fit_check():
    print("=== Passkontrolle ===")
    print(f"  Innenraum            {GH_W-2*WALL:.2f} x {GH_H-2*WALL:.2f} x {CAV_D:.2f} mm")
    print(f"  Fenstervertiefung    {REC_W:.2f} x {REC_H:.2f} x {REC_D:.2f} mm "
          f"(LCD-Modul {GLASS_W:.2f} x {GLASS_H:.2f} x {GLASS_T:.2f})")
    print(f"  Bauhoehe mit Glas    {BOARD_T:.2f} mm (Glas {GLASS_T:.2f} + Platine) | "
          f"Kavitaet {GH_D-FRONT:.2f} mm -> Rest {GH_D-FRONT-REC_D-BOARD_T:.2f} mm")
    print(f"  Deckelpolster        {PAD_T:.2f} mm -> druecken die Platine in die Vertiefung")
    print(f"  Platine (Quer)       {BOARD_W:.2f} x {BOARD_H:.2f} x {BOARD_T:.2f} mm")
    print(f"  Spiel Breite/Hoehe   {GH_W-2*WALL-BOARD_W:+.2f} / {GH_H-2*WALL-BOARD_H:+.2f} mm")
    print(f"  Spiel Tiefe          {CAV_D-BOARD_T:+.2f} mm")
    print(f"  Fenster {WIN_W:.1f}x{WIN_H:.1f} (Versatz {WIN_DX:+.2f} mm) vs. aktiv "
          f"{ACT_W:.2f}x{ACT_H:.2f} -> Rand {(WIN_W-ACT_W)/2:.2f} / {(WIN_H-ACT_H)/2:.2f} mm")
    print(f"  Querbalken {BAR_X1-BAR_X0:.1f} mm breit -> Ueberstand "
          f"{BAR_OVER:.1f} mm je Seite")
    px, pz, _ = posts()
    d = math.hypot(px - BOARD_W / 2, pz - BOARD_H / 2)
    print(f"  Schraubdom zur Platinenecke: {d:.2f} mm (R{POST_R:.1f}) -> "
          f"{'OK' if d > POST_R + 0.2 else 'KOLLISION'}")
    print(f"  Tafel hinten y=+{GH_D/2:.1f} | Mast vorne y={POLE_Y-POLE_D/2:.1f} "
          f"-> Luft {POLE_Y-POLE_D/2-GH_D/2:.1f} mm (Kabelstutzen ueberbrueckt)")
    print(f"  USB-C-Loch {USB_W:.1f} (B) x {USB_H:.1f} (H) mm (Einbaubuchse), Wand innen "
          f"auf {BW+USB_BOSS_Y:.1f} mm verstaerkt")
    print("=== Standsicherheit ===")
    print(f"  Sockel {BASE_X:.0f} x {BASE_Y:.0f} mm, Gesamthoehe {TOTAL_H:.0f} mm")
    print(f"  Mast auf x={POLE_X:.0f} (mittig) -> Randabstand {BASE_X/2-POLE_X:.0f} mm")
    vol = (BASE_X - 2 * BW) * (BASE_Y - 2 * BW) * (BASE_H - 2 * BW) / 1000.0
    print(f"  Sockel hohl: {vol:.0f} cm^3 Innenraum, kein Sand -- Standflaeche "
          f"{BASE_X:.0f} x {BASE_Y:.0f} mm")
    print(f"  Schwerpunkt liegt ueber der Standflaeche; bei Zug am Kabel hilft "
          f"ein Klettband unter dem Sockel")
    print("=== Kabellaenge USB-C (Board -> Sockelbuchse) ===")
    a = abs(PANEL_X) + GH_W / 2 - 10            # Board-USB bis Tafelmitte
    b = POLE_Y - GH_D / 2                       # Stutzen ueber den Spalt
    c = CABLE_Z - BASE_TOP                      # im Mast nach unten
    d2 = (BASE_Y / 2 - POLE_Y) + 10             # im Sockel zur Rueckwand
    tot = a + b + c + d2 + 60                   # + Bogen/Reserve
    print(f"  Tafel {a:.0f} + Spalt {b:.0f} + Mast {c:.0f} + Sockel {d2:.0f} + Reserve 60 "
          f"= ca. {tot:.0f} mm")
    print(f"  -> 0,2 m {'reicht NICHT' if tot > 200 else 'reicht'}; "
          f"0,3 m ist die sichere Wahl")

# ------------------------------------------------------------------- main
def main():
    print("=== Teile ===")
    print(f"  {'Datei':16}{'B x H x T (mm)':>26}{'Volumen':>13}{'dicht':>8}")
    total = 0.0
    for name, label, fn in PARTS:
        m = to_bed(fn())
        d = m.bounds[1] - m.bounds[0]
        total += m.volume
        m.export(os.path.join(OUT, name + ".stl"))
        print(f"  {name:16}{d[0]:8.1f} x{d[1]:7.1f} x{d[2]:6.1f}"
              f"{m.volume:12.0f} mm3 {str(m.is_watertight):>8}")
    print(f"  {'SUMME':16}{'':26}{total:12.0f} mm3")
    print(f"\n  Material (PLA, 20 % Fuellung): ca. {total*0.45/1000:.0f} g")
    print(f"  Tafel {GH_W:.0f} x {GH_H:.0f} x {GH_D:.0f} mm | Gesamthoehe {TOTAL_H:.0f} mm")
    print("  Farben: Mast weiss, Querbalken rot, Tafelgehaeuse + Sockel schwarz")
    fit_check()

    asm = assembly()
    print("\n=== Vorschau ===")
    save_png(asm, [0, 2], os.path.join(PREV, "montage_vorn.png"),
             "Vorderansicht -- Vorbild: roter Balken ueber der Tafel", "X (mm)", "Z (mm)")
    save_png(asm, [1, 2], os.path.join(PREV, "montage_seite.png"),
             "Seitenansicht -- Tafel kragt nach vorn, Mast dahinter",
             "Y (mm) = Tiefe", "Z (mm)", size=(6, 5))
    head = [it for it in asm if it[1].bounds[0][2] > SIGN_Z1 - 55]
    save_png(head, [0, 2], os.path.join(PREV, "kopf_detail.png"),
             "Kopfbereich: Blende, Deckel, Querbalken, Schelle", "X (mm)", "Z (mm)", size=(8, 5))
    base = [it for it in asm if it[1].bounds[1][2] < 40]
    save_png(base, [0, 1], os.path.join(PREV, "sockel_detail.png"),
             "Sockel Draufsicht (X-Y): Mastkragen, Kabelkanal",
             "X (mm)", "Y (mm)", size=(8, 4))
    save_png(base, [0, 2], os.path.join(PREV, "sockel_hinten.png"),
             "Sockel Rueckwand (X-Z): Loch der Einbaubuchse 13,4 x 10,2 mm",
             "X (mm)", "Z (mm)", size=(8, 4))

if __name__ == "__main__":
    main()
