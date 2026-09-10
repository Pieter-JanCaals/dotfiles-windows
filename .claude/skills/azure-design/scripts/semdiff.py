# -*- coding: utf-8 -*-
"""
Recover hand edits made in drawio, by cell id.

drawio re-serialises the whole file when it saves — attribute order, whitespace, self-closing
tags all change — so `git diff` on a .drawio is thousands of lines of noise and useless for
seeing what a person actually changed. This compares two files semantically instead: same
cell id, different style / value / geometry.

Run this BEFORE regenerating, every time, whenever the file may have been touched by hand.
Fold what it reports back into the generator so the edits survive the next regeneration.

    python semdiff.py generated.drawio theirs.drawio
"""
import sys
import xml.etree.ElementTree as ET


def load(path):
    out = {}
    for d in ET.parse(path).getroot().findall("diagram"):
        for c in d.iter("mxCell"):
            g = c.find("mxGeometry")
            geo = tuple(g.get(k) for k in ("x", "y", "width", "height")) if g is not None else None
            out[(d.get("name"), c.get("id"))] = (c.get("style") or "", c.get("value") or "", geo)
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    mine, theirs = load(sys.argv[1]), load(sys.argv[2])

    added = [k for k in theirs if k not in mine]
    removed = [k for k in mine if k not in theirs]
    print("mine=%d  theirs=%d" % (len(mine), len(theirs)))

    print("\n=== added by hand (%d) ===" % len(added))
    for k in added:
        print("  +", k[0][:24], "|", (theirs[k][1] or "<no label>")[:80])

    print("\n=== deleted by hand (%d) ===" % len(removed))
    for k in removed:
        print("  -", k[0][:24], "|", (mine[k][1] or "<no label>")[:80])

    print("\n=== modified ===")
    n = 0
    for k in mine:
        if k not in theirs:
            continue
        for i, field in enumerate(("style", "value", "geom")):
            if mine[k][i] != theirs[k][i]:
                n += 1
                print("%s | %s | %s" % (k[0][:24], k[1], field))
                print("   mine : %s" % str(mine[k][i])[:220])
                print("   theirs: %s" % str(theirs[k][i])[:220])
    print("\n%d modified fields" % n)


if __name__ == "__main__":
    main()
