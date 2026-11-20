#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vergleichsbild: eigene Konstruktion neben das Vorbild-Foto legen.
Dient als Beleg, dass die Silhouette stimmt.
"""
import os, sys
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_bracket as B

# Zugeschnittener Ausschnitt (Lampe, Tafel, Mast) -- Personen sind nicht drauf.
# Das Originalfoto liegt ausserhalb des Repos; der Ausschnitt ist beigelegt.
PHOTO = os.path.join(HERE, "preview", "vorbild_ausschnitt.png")
OUT = os.path.join(HERE, "preview", "vergleich_vorbild.png")

def side_view(ax):
    """Konstruktion von vorn, ohne Massstab."""
    items = B.assembly()
    L = np.array([0.45, -0.55, 0.70]); L /= np.linalg.norm(L)
    T, C = [], []
    for _, m, col in items:
        sh = np.clip(m.face_normals @ L, 0, 1) * 0.55 + 0.45
        T.append(m.triangles[:, :, [0, 2]])
        C.append(np.clip(sh[:, None] * np.array(col)[None, :], 0, 1))
    tris, cols = np.concatenate(T), np.concatenate(C)
    o = np.argsort(tris[:, :, 1].mean(axis=1))
    ax.add_collection(PolyCollection(tris[o], facecolors=cols[o], edgecolors="none"))
    ax.autoscale(); ax.set_aspect("equal"); ax.axis("off")

fig = plt.figure(figsize=(9.5, 6.2))

# links: Vorbild
ax1 = fig.add_subplot(1, 2, 1)
img = Image.open(PHOTO).convert("RGB")
ax1.imshow(img)
ax1.set_title("Vorbild: DFI am Paula-Modersohn-Platz", fontsize=10)
ax1.axis("off")

# rechts: Konstruktion
ax2 = fig.add_subplot(1, 2, 2)
side_view(ax2)
ax2.set_title("Nachbau (3D-Modell, Vorderansicht)", fontsize=10)

fig.suptitle("Halterung im Vorbild der VAG-Abfahrtsanzeige", fontsize=11)
fig.tight_layout()
fig.savefig(OUT, dpi=115, bbox_inches="tight"); plt.close(fig)
print("  ->", OUT)
