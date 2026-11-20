#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bemaszte technische Zeichnung der Blende (Front- und Schnittansicht)."""
import os, sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_bracket as B

OUT = os.path.join(HERE, "preview", "zeichnung_blende.png")

def shade_project(m, keep, L):
    sh = np.clip(m.face_normals @ L, 0, 1) * 0.5 + 0.5
    tris = m.triangles[:, :, keep]
    cols = np.clip(sh[:, None] * np.array([0.62, 0.66, 0.74])[None, :], 0, 1)
    o = np.argsort(tris[:, :, 1].mean(axis=1))
    return tris[o], cols[o]

def dim_h(ax, x0, x1, y, text, off=0.0, fs=7.5):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", lw=0.8, color="#b00"))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom",
            fontsize=fs, color="#b00")

def dim_v(ax, y0, y1, x, text, off=0.0, fs=7.5):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", lw=0.8, color="#b00"))
    ax.text(x + off, (y0 + y1) / 2, text, ha="left", va="center",
            fontsize=fs, color="#b00", rotation=90)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.6))
L = np.array([0.4, -0.5, 0.76]); L /= np.linalg.norm(L)

# ---------------------------------------------------------- Frontansicht
h = B.part_housing()
tris, cols = shade_project(h, [0, 1], L)
ax1.add_collection(PolyCollection(tris, facecolors=cols, edgecolors="none"))
ax1.autoscale(); ax1.set_aspect("equal")
ax1.set_title("Blende -- Frontansicht", fontsize=10)
ax1.set_xlabel("X (mm)"); ax1.set_ylabel("Y (mm)")
ax1.grid(alpha=0.25, linestyle=":")
hw, hh = B.GH_W / 2, B.GH_H / 2
ax1.set_ylim(-hh - 16, hh + 26)
ax1.set_xlim(-hw - 16, hw + 16)
dim_h(ax1, -hw, hw, -hh - 7, f"{B.GH_W:.0f}")
dim_v(ax1, -hh, hh, -hw - 7, f"{B.GH_H:.0f}")
dim_h(ax1, -B.WIN_W / 2, B.WIN_W / 2, hh + 7, f"Fenster {B.WIN_W:.0f}")
dim_v(ax1, -B.WIN_H / 2, B.WIN_H / 2, hw + 7, f"{B.WIN_H:.0f}")
dim_h(ax1, -hw, hw, hh + 17, f"Balken ragt {B.BAR_OVER:.0f} mm je Seite ueber", fs=7)
ax1.annotate("", xy=(-B.WIN_W / 2, 0), xytext=(-hw, 0),
             arrowprops=dict(arrowstyle="<->", lw=0.7, color="#06a", ls="--"))
ax1.text((-hw - B.WIN_W / 2) / 2, 3.5, f"{(B.GH_W-B.WIN_W)/2:.1f}",
         ha="center", fontsize=7, color="#06a")
ax1.text(0, hh + 12, f"Eckradius {B.WIN_R:.1f} | Wand {B.WALL:.1f} | Front {B.FRONT:.1f}",
         ha="center", fontsize=7.5, color="#333")

# ---------------------------------------------------------- Schnitt (Seite)
# Schnitt bei y=0 durch die Blende: Blende, Deckel, Querbalken
side = []
for m, col in [(B.part_housing(), (0.30, 0.31, 0.34)),
               (B.part_cover(), (0.55, 0.57, 0.62)),
               (B.part_crossbar(), (0.78, 0.15, 0.12))]:
    sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    if sec is None:
        continue
    planar, _ = sec.to_planar()
    for poly in planar.polygons_full:
        xs, ys = poly.exterior.xy
        ax2.fill(xs, ys, facecolor=col, edgecolor="k", lw=0.7, zorder=2)
        for hole in poly.interiors:
            hx, hy = hole.xy
            ax2.fill(hx, hy, facecolor="white", edgecolor="k", lw=0.5, zorder=3)

ax2.set_aspect("equal")
ax2.set_ylim(-B.GH_W / 2 - 14, B.GH_W / 2 + 24)
ax2.set_title("Schnitt durch die Blende (y = 0)", fontsize=10)
ax2.set_xlabel("Z (mm) = Tiefe"); ax2.set_ylabel("X (mm)")
ax2.grid(alpha=0.25, linestyle=":")
dim_h(ax2, 0, B.GH_D, -B.GH_W / 2 - 6, f"{B.GH_D:.1f}")
ax2.text(B.GH_D / 2, -B.GH_W / 2 - 12,
         f"Front {B.FRONT:.1f} + Innen {B.GH_D-B.FRONT-B.BACK_T:.1f} + Deckel {B.BACK_T:.1f}",
         ha="center", fontsize=7.5, color="#333")
ax2.text(B.GH_D / 2, B.GH_W / 2 + 19,
         f"Platine {B.BOARD_T:.1f} mm dick + Glas {B.GLASS_T:.1f} in der Vertiefung",
         ha="center", fontsize=7.5, color="#06a")
ax2.text(B.GH_D / 2, B.GH_W / 2 + 13,
         "Sichtfenster 45 x 25 -- nur der Bildschirm ist sichtbar",
         ha="center", fontsize=7.5, color="#b00")

fig.suptitle("Halterung Tram-Abfahrtsanzeige -- Blende, Maszangaben in mm", fontsize=11)
fig.tight_layout()
fig.savefig(OUT, dpi=115, bbox_inches="tight"); plt.close(fig)
print("  ->", OUT)
