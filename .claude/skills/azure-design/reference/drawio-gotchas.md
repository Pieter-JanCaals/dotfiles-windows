# drawio traps

Every one of these cost real debugging time. They are not obvious from the XML.

## The file is probably open, and drawio will overwrite you

drawio desktop holds the file and re-saves it. If it saves after you generate, your work is
gone. Before writing: check for a running process and for a `.$<name>.drawio.bkp` lock file
next to the target. After writing: **tell the user to reload** (File → Reload, or close and
reopen) and never assume they did.

```powershell
Get-Process -Name "draw.io" -ErrorAction SilentlyContinue
```

## `git diff` on a .drawio is useless

drawio re-serialises everything on save — attribute order, whitespace, self-closing tags — so
a line diff shows thousands of changes and hides the three a person actually made. Use
`scripts/semdiff.py` to compare by cell id. Run it before every regeneration when the file may
have been touched by hand, and fold what it finds back into the generator.

## Overflowing labels get an invisible white box

drawio injects `background-color: var(--ge-adaptive-bg, #ffffff)` on any label wider than its
shape — which every icon label is. Invisible on a white page, a pale rectangle on any tinted
container. Fix: `labelBackgroundColor=none` on icons (the kit does this). Confirm by exporting
to **SVG** and reading the markup — SVG is text, so you can see exactly what drawio emitted
instead of guessing from a PNG.

## Empty edge labels still paint a background

Setting `labelBackgroundColor` on an edge whose value is `""` renders a bare white rectangle
near the target. Only set it when there is a label (the kit does this).

## Icon paths must be verified, not remembered

A wrong path renders as a broken-image placeholder. Run `scripts/verify_icons.py` and check
every path you have not personally used before. The library is inside `app.asar`.

## Page export is 1-indexed

`--page-index 0` fails with "pages are numbered from 1". Export runs:

```powershell
& $drawio --export --format png --page-index $i --scale 1.4 --border 8 -o out.png file.drawio
```

The GPU-cache errors on stderr are harmless noise; redirect with `2>$null`.

## `|` in a JMESPath query breaks through PowerShell into cmd

`az ... --query "resourceTypes[?x=='y'].locations|[0]"` fails with `'[0]' is not recognized`.
Use the flatten operator `[]` instead of a pipe.

## Corner icons overhang their container

`scope_corner` places the icon at `(x-14, y-14)`. Bounds checks must allow -14, and the
outermost container needs ≥14px clearance from the page edge.

## Always look at the render

Structural validation passes on diagrams that are visually broken. Export every page to PNG
and actually read it. Collisions between edge labels and text, captions overlapping box
borders, and empty bands inside a group are only ever visible this way.
