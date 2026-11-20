#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch the official LilyGO board model used for the fit check.

The holder is designed against the *official* mechanical drawing of the
T-Display S3, not against estimates. That model is MIT-licensed and lives in
LilyGO's own repository, so it is not redistributed here -- this script pulls
it into ``ref/`` on demand.

    python3 hardware/get_board_model.py

Afterwards ``board_fit.py`` finds it in ``ref/`` automatically.
"""
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref")
OUT = os.path.join(REF, "t-display-s3-full.stl")

URL = ("https://raw.githubusercontent.com/Xinyuan-LilyGO/T-Display-S3/"
       "main/dimensions/t-display-s3-full.stl")
EXPECT = 188584          # bytes, as published -- catches a truncated download


def main():
    os.makedirs(REF, exist_ok=True)
    if os.path.exists(OUT) and os.path.getsize(OUT) == EXPECT:
        print(f"  already present: {OUT} ({EXPECT} B)")
        return
    print(f"  downloading {URL}")
    req = urllib.request.Request(URL, headers={"User-Agent": "holder-fit-check/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if len(data) != EXPECT:
        print(f"  WARNING: got {len(data)} B, expected {EXPECT} B")
    with open(OUT, "wb") as f:
        f.write(data)
    print(f"  -> {OUT} ({len(data)} B)")


if __name__ == "__main__":
    sys.exit(main())
