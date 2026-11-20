"""Alle Teile auf Druckplatten legen und als 3MF exportieren.

Die Teile werden reihenweise auf 220x220-Platten verteilt, damit auch ein
kleiner Drucker (z. B. Bambu A1 / Prusa MK4) alles drucken kann.
"""
import os, sys
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_bracket as B

BED = 220.0          # Bauraum Kantenlänge
GAP = 8.0            # Abstand zwischen den Teilen

parts = [(n, B.to_bed(f())) for n, _, f in B.PARTS]

# auf Platten verteilen (Reihen füllen, umbrechen)
scene = trimesh.Scene()
x = y = row_h = 0.0
plates = 1
for n, m in parts:
    d = m.bounds[1] - m.bounds[0]
    if x + d[0] > BED:                      # neue Reihe
        x = 0.0; y += row_h + GAP; row_h = 0.0
        if y + d[1] > BED:                  # neue Platte
            y = 0.0; plates += 1
    m = m.copy(); m.apply_translation((x - m.bounds[0][0], y - m.bounds[0][1], 0))
    scene.add_geometry(m, node_name=n)
    x += d[0] + GAP
    row_h = max(row_h, d[1])

print(f"  {len(parts)} Teile auf {plates} Platte(n), Bauraum {BED:.0f} x {BED:.0f} mm")
out = os.path.join(HERE, "stl", "alle_teile.3mf")
scene.export(out)
print("  ->", out, os.path.getsize(out), "B")

# Einzelteile auch als 3MF (manche Dienste wollen das)
for n, m in parts:
    m.export(os.path.join(HERE, "stl", n + ".3mf"))
print(f"  -> {len(parts)} Einzel-3MF geschrieben")
