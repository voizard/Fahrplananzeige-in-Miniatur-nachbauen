#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Screw-joint check: does every screw fit, pass through, and grip?

For each screw hole the *diameter* is measured perpendicular to the screw axis
(scanning through the hole centre). Rules for an M3 screw in PLA:

  * part the screw passes THROUGH  -> clearance hole  >= 3.2 mm
  * part the screw screws INTO     -> pilot hole      ~ 2.5 mm
  * both holes must be coaxial and reach each other

Run:  PYTHONPATH=<site-packages> python3 hardware/screw_check.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_bracket as B

OK, BAD = "OK ", "!! "


def T(fn, xyz):
    m = fn()
    m.apply_translation(xyz)
    return m


def width(part, axis, center, span, n=800):
    """Diameter of the hole around `center`: the contiguous air run that
    contains the centre point. Air *outside* the part is ignored."""
    a0, a1 = span
    ts = np.linspace(a0, a1, n)
    pts = np.tile(np.array(center, float), (n, 1))
    pts[:, axis] = ts
    air = ~part.contains(pts)
    c = int(np.argmin(np.abs(ts - center[axis])))
    if not air[c]:
        return 0.0                      # centre is material -> no hole here
    lo = c
    while lo > 0 and air[lo - 1]:
        lo -= 1
    hi = c
    while hi < n - 1 and air[hi + 1]:
        hi += 1
    return float(ts[hi] - ts[lo]) + (a1 - a0) / n


def line(label, d, want, kind):
    lo, hi = want
    good = lo <= d <= hi
    print(f"  {OK if good else BAD}{label:34} {d:5.2f} mm   (soll {kind} {lo:.1f}-{hi:.1f})")
    return good


def main():
    housing = T(B.part_housing, (B.PANEL_X, 0, B.SIGN_Z0))
    cover = T(B.part_cover, (B.PANEL_X, 0, B.SIGN_Z0))
    cross = T(B.part_crossbar, (0, 0, B.SIGN_Z1))
    clamp = T(B.part_clamp, (B.POLE_X, B.POLE_Y, B.CLAMP_Z0))

    _, pz, P = B.posts()
    post_x = [B.PANEL_X + x for x, _ in P][:2]          # linke zwei Dome
    post_z = B.SIGN_Z0 + B.GH_H / 2 + pz

    print("=" * 74)
    print("SCHRAUBEN-PRUEFUNG   (Durchmesser quer zur Schraubenachse gemessen)")
    print("=" * 74)
    ok = True

    print("\n[1] Rueckdeckel -> Schraubdome  (4x M3, Achse Y)")
    ok &= line("Deckel: Durchgang", width(cover, 0, (post_x[0], 9.25, post_z), (post_x[0] - 5, post_x[0] + 5)), (3.1, 3.6), "Durchgang")
    ok &= line("Dom: Kernloch", width(housing, 0, (post_x[0], 0.5, post_z), (post_x[0] - 5, post_x[0] + 5)), (2.3, 2.7), "Kernloch")

    print("\n[2] Querbalken -> Blende Deckwand  (2x M3, Achse Z)")
    x = B.SCREW_GLOBAL[0]
    ok &= line("Querbalken: Durchgang", width(cross, 0, (x, 0.0, B.SIGN_Z1 + 3), (x - 5, x + 5)), (3.1, 3.6), "Durchgang")
    ok &= line("Blende: Kernloch", width(housing, 0, (x, 0.0, B.SIGN_Z0 + B.GH_H - 2), (x - 5, x + 5)), (2.3, 2.7), "Kernloch")

    print("\n[3] Balkenarm -> Schelle  (2x M3, Achse Z)")
    x = B.POLE_X + B.ARM_SCREW_DX
    ok &= line("Arm: Durchgang", width(cross, 0, (x, B.ARM_SCREW_Y_G, B.SIGN_Z1 + 3), (x - 5, x + 5)), (3.1, 3.6), "Durchgang")
    ok &= line("Schelle: Kernloch", width(clamp, 0, (x, B.ARM_SCREW_Y_G, B.CLAMP_Z1 - 1.5), (x - 5, x + 5)), (2.3, 2.7), "Kernloch")

    print("\n[4] Klemmschraube Schelle  (1x M3, Achse X)")
    yc = B.POLE_Y + B.POLE_D / 2 + B.CLAMP_T / 2
    zc = B.CLAMP_Z0 + B.CLAMP_H / 2
    ok &= line("Schelle: Durchgang links", width(clamp, 1, (B.POLE_X - 5, yc, zc), (yc - 5, yc + 5)), (3.1, 3.6), "Durchgang")
    ok &= line("Schelle: Kernloch rechts", width(clamp, 1, (B.POLE_X + 5, yc, zc), (yc - 5, yc + 5)), (2.3, 2.7), "Kernloch")

    print("\n" + "=" * 74)
    print("ERGEBNIS:", "alle Schrauben passen" if ok else "FEHLER -- Loecher stimmen nicht")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
