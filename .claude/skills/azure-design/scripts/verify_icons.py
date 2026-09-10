# -*- coding: utf-8 -*-
"""
Find and verify drawio Azure icon paths BEFORE using them.

A wrong icon path renders as a broken-image placeholder, which looks worse than the sketch
you were asked to improve. The shape library lives inside drawio's app.asar, so this reads
that archive's index directly rather than guessing from memory.

    python verify_icons.py                     # list categories and counts
    python verify_icons.py networking          # list one category
    python verify_icons.py --find postgres     # search all categories
    python verify_icons.py --check a/B c/D     # exit 1 if any path is missing
"""
import sys, os, json, struct

ASAR = os.path.expandvars(r"%LOCALAPPDATA%\Programs\draw.io\resources\app.asar")


def all_paths(asar=ASAR):
    if not os.path.exists(asar):
        sys.exit("drawio not found at %s — install it or pass a path" % asar)
    with open(asar, "rb") as f:
        f.read(12)
        (n,) = struct.unpack("<I", f.read(4))
        head = json.loads(f.read(n).decode("utf-8"))
    out, stack = set(), [(head, "")]
    while stack:
        node, prefix = stack.pop()
        for name, child in (node.get("files") or {}).items():
            path = prefix + "/" + name
            if "files" in child:
                stack.append((child, path))
            elif "/img/lib/azure2/" in path:
                out.add(path.split("/img/lib/azure2/", 1)[1][:-4])   # category/Name
    return out


def main():
    paths = all_paths()
    args = sys.argv[1:]
    if not args:
        cats = {}
        for p in paths:
            cats[p.split("/")[0]] = cats.get(p.split("/")[0], 0) + 1
        for c in sorted(cats):
            print("%4d  %s" % (cats[c], c))
        print("\n%d icons total. `--find <term>` to search." % len(paths))
    elif args[0] == "--check":
        missing = [a for a in args[1:] if a not in paths]
        print("missing:", missing or "none")
        sys.exit(1 if missing else 0)
    elif args[0] == "--find":
        term = args[1].lower()
        for p in sorted(x for x in paths if term in x.lower()):
            print(p)
    else:
        for p in sorted(x for x in paths if x.startswith(args[0] + "/")):
            print(p)


if __name__ == "__main__":
    main()
