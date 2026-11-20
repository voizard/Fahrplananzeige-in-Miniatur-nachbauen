#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einbaupassung pruefen: offizielle Platine (LilyGO t-display-s3-full.stl) in die
Blende setzen und pruefen, ob das Sichtfenster genau ueber dem Bildschirm liegt.

Offizielle Achsen:  X = Platinenbreite (26 mm), Y = Platinenlaenge (62 mm),
                    Z = Dicke.  Bestueckung auf +Z, LCD-Glas auf -Z.
Blenden-Achsen:     X = Breite, Y = Tiefe (Front = -Y), Z = Hoehe.
Umsetzung:          X_h = Y_b,  Y_h = Z_b,  Z_h = X_b   (Drehung, keine Spiegelung)
"""
import os, sys, glob
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_bracket as B

CANDIDATES = [
    os.path.join(B.HERE, "ref", "t-display-s3-full.stl"),
    os.path.join(B.HERE, "..", "dimensions", "t-display-s3-full.stl"),
]


def find_board():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    hits = glob.glob(os.path.join(B.HERE, "**", "*full*.stl"), recursive=True)
    return hits[0] if hits else None


def orient(m):
    """Offizielle Achsen -> Blenden-Achsen, Ursprung = Platinenmitte."""
    v = np.asarray(m.vertices, dtype=float)
    v = v - (v.min(axis=0) + v.max(axis=0)) / 2.0
    v = np.column_stack([v[:, 1], v[:, 2], v[:, 0]])   # X_h=Y_b, Y_h=Z_b, Z_h=X_b
    m = m.copy()
    m.vertices = v
    return m


def main():
    src = find_board()
    if not src:
        print("Platine-STL nicht gefunden.")
        print("Erst laden:  python3 hardware/get_board_model.py")
        return
    print("Quelle:", src)
    raw = trimesh.load(src)
    parts = raw.split(only_watertight=False)
    # Groesster Koerper = Platine inkl. bestueckter Teile, kleinster = LCD-Glas
    pcb = max(parts, key=lambda p: float(np.prod(p.bounds[1] - p.bounds[0])))
    glass = min(parts, key=lambda p: float(np.prod(p.bounds[1] - p.bounds[0])))
    print(f"  Koerper: {len(parts)}  (Platine + LCD-Glas)")

    # Beide um denselben Platinen-Ursprung drehen/verschieben
    ref = np.asarray(pcb.vertices, dtype=float)
    c0 = (ref.min(axis=0) + ref.max(axis=0)) / 2.0

    def place(m):
        # Platinenruecken soll an der Deckel-Innenflaeche liegen
        v = np.asarray(m.vertices, dtype=float) - c0
        v = np.column_stack([v[:, 1], v[:, 2], v[:, 0]])
        v += np.array([B.PANEL_X, B.BOARD_Y, B.SIGN_Z0 + B.GH_H / 2])
        m = m.copy(); m.vertices = v
        return m

    pcb_h, glass_h = place(pcb), place(glass)

    b = pcb_h.bounds
    print(f"\nPlatine in der Blende (X-Y-Z):")
    print(f"  X {b[0][0]:7.2f}..{b[1][0]:7.2f}  (Breite {b[1][0]-b[0][0]:5.2f})")
    print(f"  Y {b[0][1]:7.2f}..{b[1][1]:7.2f}  (Tiefe  {b[1][1]-b[0][1]:5.2f})")
    print(f"  Z {b[0][2]:7.2f}..{b[1][2]:7.2f}  (Hoehe  {b[1][2]-b[0][2]:5.2f})")

    g = glass_h.bounds
    win_x0 = B.PANEL_X + B.WIN_DX - B.WIN_W / 2
    win_x1 = B.PANEL_X + B.WIN_DX + B.WIN_W / 2
    zc = B.SIGN_Z0 + B.GH_H / 2 + B.WIN_DZ
    win_z0, win_z1 = zc - B.WIN_H / 2, zc + B.WIN_H / 2
    # Aktive Flaeche = Mitte des LCD-Moduls + Nennmass 42,63 x 22,65
    acx = (g[0][0] + g[1][0]) / 2
    acz = (g[0][2] + g[1][2]) / 2
    ax0, ax1 = acx - B.ACT_W / 2, acx + B.ACT_W / 2
    az0, az1 = acz - B.ACT_H / 2, acz + B.ACT_H / 2
    print(f"\nLCD-Modul (Glas)  : X {g[0][0]:7.2f}..{g[1][0]:7.2f}   Z {g[0][2]:7.2f}..{g[1][2]:7.2f}")
    print(f"  aktive Flaeche  : X {ax0:7.2f}..{ax1:7.2f}   Z {az0:7.2f}..{az1:7.2f} "
          f"({B.ACT_W:.2f} x {B.ACT_H:.2f})")
    print(f"Sichtfenster      : X {win_x0:7.2f}..{win_x1:7.2f}   Z {win_z0:7.2f}..{win_z1:7.2f} "
          f"({B.WIN_W:.1f} x {B.WIN_H:.1f})")
    print(f"\n  Rand links  {ax0-win_x0:+.2f} mm   rechts {win_x1-ax1:+.2f} mm")
    print(f"  Rand unten  {az0-win_z0:+.2f} mm   oben   {win_z1-az1:+.2f} mm")
    ok = (ax0 > win_x0 - 0.01 and ax1 < win_x1 + 0.01
          and az0 > win_z0 - 0.01 and az1 < win_z1 + 0.01)
    print(f"  -> aktive Flaeche liegt {'VOLLSTAENDIG' if ok else 'NICHT'} im Fenster")
    print(f"  -> Fenster zeigt {'nur den Bildschirm' if ok else 'auch Platine'}; "
          f"Glas ({B.GLASS_W:.2f} mm) ist {'hinter der Wand verdeckt' if B.GLASS_W > B.WIN_W else 'SICHTBAR'}")
    # Glas darf die Frontwand nicht durchdringen
    print(f"\n  Glasfront y = {g[0][1]:.2f} | Innenwand y = {B.FRONT_IN:.2f} "
          f"(Vertiefung bis {B.REC_IN:.2f}) | Aussenflaeche y = {-B.GH_D/2:.2f}")
    print(f"  -> Glas {'sitzt in der Vertiefung' if g[0][1] >= B.REC_IN - 0.01 else 'DRINGT DURCH'}"
          f", Frontwand {'bleibt frei' if g[0][1] >= B.FRONT_IN - 0.01 else 'WIRD DURCHDRUNGEN'}")

    # Harte Kollisionspruefung: schneidet das Glas die Blende?
    try:
        h = B.part_housing().copy(); h.apply_translation((B.PANEL_X, 0, B.SIGN_Z0))
        inter = trimesh.boolean.intersection([h, glass_h])
        vol = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
        print(f"  Kollision Blende<->Glas: {vol:.3f} mm3 -> "
              f"{'frei' if vol < 1.0 else 'UEBERSCHNEIDUNG'}")
    except Exception as e:
        print("  Kollisionspruefung fehlgeschlagen:", e)

    # Vorschau: Blende + Platine + Glas, Blick von vorn
    items = [("Blende", B.part_housing().copy(), (0.10, 0.10, 0.12)),
             ("Platine", pcb_h, (0.15, 0.45, 0.25)),
             ("Glas", glass_h, (0.90, 0.75, 0.10))]
    items[0][1].apply_translation((B.PANEL_X, 0, B.SIGN_Z0))
    B.save_png(items, [0, 2], os.path.join(B.PREV, "einbau_vorn.png"),
               "Einbau: Blende (grau) + Platine (gruen) + LCD (gelb)", "X (mm)", "Z (mm)", size=(7, 4))
    # Schnitt in der Fensterebene
    sec = B.part_housing().copy()
    sec.apply_translation((B.PANEL_X, 0, B.SIGN_Z0))
    try:
        s = sec.section(plane_origin=(0, B.FRONT_IN + 0.01, 0), plane_normal=(0, 1, 0))
        pl, _ = s.to_planar()
        print(f"\nSchnitt in der Frontwand: {len(pl.polygons_full)} Polygon(e)")
        for poly in pl.polygons_full:
            bb = poly.bounds
            print(f"   aussen {bb[2]-bb[0]:6.2f} x {bb[3]-bb[1]:6.2f} mm, "
                  f"Loecher {len(poly.interiors)}")
            for h in poly.interiors:
                hb = h.bounds
                print(f"      FENSTER {hb[2]-hb[0]:6.2f} x {hb[3]-hb[1]:6.2f} mm "
                      f"@ X {hb[0]:7.2f}..{hb[2]:7.2f}  Z {hb[1]:7.2f}..{hb[3]:7.2f}")
    except Exception as e:
        print("Schnitt fehlgeschlagen:", e)


if __name__ == "__main__":
    main()
