import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import build_bracket as B
PREV = B.PREV
SRC = os.path.join(B.HERE, "ref")

def load_bodies(path):
    m = trimesh.load(path)
    try:
        ps = m.split(only_watertight=False)
        if len(ps) >= 1: return ps
    except Exception:
        pass
    return [m]

print("=== t-display-s3-full.stl ===")
ps = load_bodies(os.path.join(SRC, "t-display-s3-full.stl"))
for i, p in enumerate(ps):
    b = p.bounds; d = b[1] - b[0]
    print("[%d] %6.2f x %6.2f x %6.2f  Vol %8.0f" % (i, d[0], d[1], d[2], p.volume))
    print("    X %7.2f..%7.2f  Y %7.2f..%7.2f  Z %7.2f..%7.2f" % (b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]))

items = [(("k%d" % i), p, (0.80, 0.25, 0.20) if i == 0 else (0.15, 0.40, 0.90)) for i, p in enumerate(ps)]
B.save_png(items, [0, 1], os.path.join(PREV, "off_XY.png"), "offiziell: X-Y (Draufsicht Platine)", "X (mm)", "Y (mm)")
B.save_png(items, [1, 2], os.path.join(PREV, "off_YZ.png"), "offiziell: Y-Z (Seitenprofil)", "Y (mm)", "Z (mm)", size=(7, 4))
B.save_png(items, [0, 2], os.path.join(PREV, "off_XZ.png"), "offiziell: X-Z (Stirn)", "X (mm)", "Z (mm)", size=(7, 4))

print()
print("=== LilyGO-Huelle: Fenster ===")
for nm in ("shell-cova", "shell-covb", "shell-covc", "shell-covd", "shell-cove"):
    fp = os.path.join(SRC, nm + ".stl")
    if not os.path.exists(fp): continue
    m = trimesh.load(fp)
    b = m.bounds; d = b[1] - b[0]
    ax = int(np.argmin(d))
    print("--- %s: %.2f x %.2f x %.2f (duennste Achse %d) ---" % (nm, d[0], d[1], d[2], ax))
    for f in (0.4, 0.6):
        o = [0.0, 0.0, 0.0]; o[ax] = b[0][ax] + d[ax] * f
        n = [0.0, 0.0, 0.0]; n[ax] = 1.0
        try:
            sec = m.section(plane_origin=o, plane_normal=n)
        except Exception as e:
            print("   Schnitt fehlgeschlagen:", e); continue
        if sec is None: continue
        pl, _ = sec.to_planar()
        print("   Schnitt bei %.2f: %d Polygon(e)" % (o[ax], len(pl.polygons_full)))
        for poly in pl.polygons_full:
            bb = poly.bounds
            print("      aussen %6.2f x %6.2f | Loecher %d" % (bb[2]-bb[0], bb[3]-bb[1], len(poly.interiors)))
            for h in poly.interiors:
                hb = h.bounds
                print("         LOCH %6.2f x %6.2f  @ %6.1f..%6.1f , %6.1f..%6.1f"
                      % (hb[2]-hb[0], hb[3]-hb[1], hb[0], hb[2], hb[1], hb[3]))
