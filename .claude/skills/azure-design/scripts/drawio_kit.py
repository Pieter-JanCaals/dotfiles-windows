# -*- coding: utf-8 -*-
"""
drawio_kit — the visual system for Azure architecture diagrams, as reusable primitives.

Copy this next to a `build_<project>.py` that composes pages from it. Everything here is
topology-agnostic: it knows about scopes, groups, plans, subnets and private endpoints, not
about any particular application.

Conventions this file enforces so you cannot accidentally break them:
  * all geometry lands on the 10px grid (assert in _geo)
  * icon labels never get drawio's adaptive white backing
  * edges with no label never get a label background
  * container labels always knock out to white
  * pages size themselves to their content

Usage sketch:

    from drawio_kit import *
    p = Page("D1 · Something", "d1", 1320)
    header(p, p.ANN, "Title", "Subtitle", "DESIGN 1 OF 3")
    ...
    xml = emit([p])
    open(out, "w", encoding="utf-8", newline="\\n").write(xml)
    validate(xml, verified_icon_paths())
"""
import html as _h
import io
import os
import struct
import json
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- palette ---
INK    = "#1F2430"   # primary text
MUTED  = "#5A6472"   # secondary text
EDGE   = "#B9C0CC"   # neutral panel border
SCOPE  = "#8A94A6"   # tenant border
AZ     = "#0F6CBD"   # Azure blue — networking / private link
TEAL   = "#0F8A6A"   # observability
PURPLE = "#6B4FA8"   # identity
PAPER  = "#FFFFFF"

RG_BORDER, RG_FILL   = "#C8CFD8", "#F7F8FA"   # resource groups — never colour-coded
GRP_BORDER           = "#E3E7EC"              # grouping bands: present but quiet
SUB_BORDER           = "#CBD3DC"              # subnets and plan boxes
SUBS_FILL, SUBS_STROKE = "#fff2cc", "#d6b656" # subscription

WARN_B, WARN_F = "#B26A00", "#FFF6E9"
DANG_B, DANG_F = "#B3261E", "#FDEDEB"
INFO_B, INFO_F = "#0F6CBD", "#EDF3FB"
OKAY_B, OKAY_F = "#0F8A6A", "#EAF5F1"

FONT = "Segoe UI"
MONO = 'font-family:Consolas,monospace;'

# ------------------------------------------------------------------ icons ---
# Aliases for the ones you reach for constantly. Anything else: pass the azure2 path
# directly, e.g. icon(p, L, "networking/Front_Doors", ...). Always run verify_icons.py
# before trusting a path you have not used before — a wrong one renders as a broken image.
ICONS = {
    "tenant": "other/Entra_Identity",      "extid":  "identity/External_ID",
    "appreg": "identity/App_Registrations", "users": "identity/Users",
    "mi":     "identity/Managed_Identities", "sub":   "general/Subscriptions",
    "rg":     "general/Resource_Groups",    "mg":     "general/Management_Groups",
    "slot":   "general/Web_Slots",          "mobile": "general/Mobile",
    "asp":    "app_services/App_Service_Plans", "app": "app_services/App_Services",
    "apim":   "app_services/API_Management_Services",
    "func":   "compute/Function_Apps",      "vm":     "compute/Virtual_Machine",
    "aks":    "containers/Kubernetes_Services", "acr": "containers/Container_Registries",
    "pg":     "databases/Azure_Database_PostgreSQL_Server",
    "sql":    "databases/Azure_SQL",        "cosmos": "databases/Azure_Cosmos_DB",
    "redis":  "databases/Cache_Redis",
    "kv":     "security/Key_Vaults",        "st":     "storage/Storage_Accounts",
    "appi":   "devops/Application_Insights", "law":   "analytics/Log_Analytics_Workspaces",
    "vnet":   "networking/Virtual_Networks", "snet":  "networking/Subnet",
    "pe":     "networking/Private_Endpoint", "dns":   "networking/DNS_Zones",
    "nsg":    "networking/Network_Security_Groups",
    "lb":     "networking/Load_Balancers",   "agw":   "networking/Application_Gateways",
    "fd":     "networking/Front_Doors",      "fw":    "networking/Firewalls",
    "sb":     "integration/Service_Bus",     "evh":   "analytics/Event_Hubs",
}


def IMG(ref):
    """Alias | 'category/Name' | full path  ->  full drawio image path."""
    if ref.startswith("img/"):
        return ref
    ref = ICONS.get(ref, ref)
    return "img/lib/azure2/%s.svg" % ref


def verified_icon_paths(asar=None):
    """Every azure2 icon path that actually exists in the local drawio install.

    Returns an empty set if drawio is not installed, in which case validate() skips the
    icon check — say so out loud rather than pretending it passed.
    """
    asar = asar or os.path.expandvars(
        r"%LOCALAPPDATA%\Programs\draw.io\resources\app.asar")
    if not os.path.exists(asar):
        return set()
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
                out.add(path.split("/webapp/", 1)[-1])
    return out


# ------------------------------------------------------------- primitives ---
class Page:
    def __init__(self, name, tag, w=1600):
        self.name, self.tag, self.w = name, tag, w
        self.layers, self.cells, self.maxy, self._n = [], [], 0, 0
        # Four layers on every topology page. Keep the names identical across pages so a
        # reader can mute the same concern everywhere.
        self.BASE = self.layer(tag + "_base", "Base")
        self.NET  = self.layer(tag + "_net",  "Networking")
        self.OBS  = self.layer(tag + "_obs",  "Observability")
        self.ANN  = self.layer(tag + "_ann",  "Annotations")

    def layer(self, lid, label):
        self.layers.append((lid, label))
        return lid

    def track(self, y, h):
        self.maxy = max(self.maxy, y + h)

    def uid(self, kind="c"):
        self._n += 1
        return "%s_%s_%d" % (self.tag, kind, self._n)

    def add(self, xml):
        self.cells.append(xml)


def esc(s):
    return _h.escape(s, quote=True)


def mono(s):
    return '<span style="%s">%s</span>' % (MONO, s)


def _geo(x, y, w, h):
    for v in (x, y, w, h):
        assert float(v) == int(v), "off-grid geometry: %r" % ((x, y, w, h),)
    return '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/>' % (x, y, w, h)


def box(p, layer, x, y, w, h, label="", stroke=EDGE, fill="none", dash=False,
        fs=12, bold=True, align="left", valign="top", sl=10, st=6, radius=0,
        opacity=100, fc=INK, extra=""):
    cid = p.uid("b")
    # absoluteArcSize keeps the radius a fixed 6px rather than a percentage of the box,
    # so large containers stay crisp instead of turning into lozenges.
    corner = "rounded=1;absoluteArcSize=1;arcSize=6;" if radius else "rounded=0;"
    style = (corner + "whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;verticalAlign=%s;"
             "align=%s;spacingLeft=%d;spacingTop=%d;fontFamily=%s;fontSize=%d;fontColor=%s;"
             "fontStyle=%d;opacity=%d;%s"
             % (fill, stroke, valign, align, sl, st, FONT, fs, fc, 1 if bold else 0,
                opacity, extra))
    if dash:
        style += "dashed=1;dashPattern=8 6;"
    p.add('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">%s</mxCell>'
          % (cid, esc(label), style, layer, _geo(x, y, w, h)))
    p.track(y, h)
    return cid


def icon(p, layer, ref, x, y, label="", w=32, h=32, side="bottom", fs=10,
         bold=False, opacity=100, fc=INK):
    """side: 'bottom' centres the label under the icon, 'top' above it, 'right' beside it."""
    cid = p.uid("i")
    if side == "bottom":
        pos = "labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;spacingTop=2;"
    elif side == "top":
        pos = "labelPosition=center;verticalLabelPosition=top;align=center;verticalAlign=bottom;spacingBottom=2;"
    else:
        pos = "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=6;"
    # labelBackgroundColor=none is REQUIRED. An icon label is always wider than its 24-32px
    # shape, and drawio gives overflowing labels an adaptive white backing, which shows up as
    # a pale rectangle against any tinted container.
    style = ("image;aspect=fixed;html=1;points=[];image=%s;%sfontFamily=%s;fontSize=%d;"
             "fontColor=%s;fontStyle=%d;opacity=%d;labelBackgroundColor=none;"
             % (IMG(ref), pos, FONT, fs, fc, 1 if bold else 0, opacity))
    p.add('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">%s</mxCell>'
          % (cid, esc(label), style, layer, _geo(x, y, w, h)))
    p.track(y, h + (14 if side == "bottom" else 0))
    return cid


def text(p, layer, x, y, w, h, body, fs=11, align="left", valign="top",
         color=INK, bold=False, bg="none"):
    cid = p.uid("t")
    style = ("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=%s;"
             "verticalAlign=%s;fontFamily=%s;fontSize=%d;fontColor=%s;fontStyle=%d;"
             "spacingLeft=0;spacingTop=0;labelBackgroundColor=%s;"
             % (align, valign, FONT, fs, color, 1 if bold else 0, bg))
    p.add('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">%s</mxCell>'
          % (cid, esc(body), style, layer, _geo(x, y, w, h)))
    p.track(y, h)
    return cid


# ---------------------------------------------------------------- edges -----
FLOW  = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=" + INK +
         ";strokeWidth=1.5;endArrow=blockThin;endFill=1;")
PLINK = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=" + AZ +
         ";strokeWidth=1.2;dashed=1;dashPattern=1 3;endArrow=none;endFill=0;")
TELEM = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=" + TEAL +
         ";strokeWidth=1.2;dashed=1;dashPattern=8 4;endArrow=blockThin;endFill=1;")


def _edge(p, layer, src, tgt, label, style, exitp=None, entryp=None, waypoints=None):
    cid = p.uid("e")
    s = style + "fontFamily=%s;fontSize=10;fontColor=%s;" % (FONT, MUTED)
    if label:
        # Only when a label exists — set unconditionally, drawio paints a bare white
        # rectangle for the empty label instead.
        s += "labelBackgroundColor=%s;" % PAPER
    if exitp:
        s += "exitX=%s;exitY=%s;exitDx=0;exitDy=0;" % exitp
    if entryp:
        s += "entryX=%s;entryY=%s;entryDx=0;entryDy=0;" % entryp
    geo = '<mxGeometry relative="1" as="geometry">'
    if waypoints:
        geo += '<Array as="points">' + "".join(
            '<mxPoint x="%d" y="%d"/>' % (wx, wy) for wx, wy in waypoints) + "</Array>"
    geo += "</mxGeometry>"
    p.add('<mxCell id="%s" value="%s" style="%s" edge="1" parent="%s" source="%s" '
          'target="%s">%s</mxCell>' % (cid, esc(label), s, layer, src, tgt, geo))
    return cid


flow  = lambda *a, **k: _edge(a[0], a[1], a[2], a[3], a[4], FLOW,  **k)
plink = lambda *a, **k: _edge(a[0], a[1], a[2], a[3], a[4], PLINK, **k)
telem = lambda *a, **k: _edge(a[0], a[1], a[2], a[3], a[4], TELEM, **k)


# ------------------------------------------------------------- composites ---
def header(p, layer, title, subtitle, kicker):
    box(p, layer, 0, 0, p.w, 76, "", stroke="none", fill=PAPER)
    text(p, layer, 40, 14, p.w - 480, 26, title, fs=19, bold=True)
    text(p, layer, 40, 42, p.w - 480, 20, subtitle, fs=11, color=MUTED)
    text(p, layer, p.w - 440, 18, 400, 18, kicker, fs=11, bold=True, align="right", color=AZ)
    box(p, layer, 40, 74, p.w - 80, 2, "", stroke="none", fill=EDGE)


def scope_corner(p, layer, ref, bx, by, label, sub="", fs=14, sub_fs=9, color=INK):
    """Scope icon straddling a container's top-left corner, carrying its own label to the
    right. Call AFTER box() for the same container so the icon paints over the border.

    The white knockout is what stops the container's own top edge drawing through the text.
    """
    val = '<b><font style="font-size: %dpx;">%s</font></b>' % (fs, label)
    if sub:
        val += '<br><font style="font-size: %dpx;">%s</font>' % (sub_fs, sub)
    cid = p.uid("i")
    style = ("image;aspect=fixed;html=1;points=[];image=%s;labelPosition=right;"
             "verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=7;"
             "fontFamily=%s;fontSize=6;fontColor=%s;fontStyle=0;labelBackgroundColor=#FFFFFF;"
             % (IMG(ref), FONT, color))
    p.add('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">%s</mxCell>'
          % (cid, esc(val), style, layer, _geo(bx - 14, by - 14, 28, 28)))
    return cid


def group(p, layer, x, y, w, h, label, bg=RG_FILL):
    """A quiet grouping band. Label sits on the top border like a fieldset legend, knocked
    out of it, so the whole interior stays free for content."""
    b = box(p, layer, x, y, w, h, "", stroke=GRP_BORDER, fill="none")
    text(p, layer, x + 12, y - 7, 340, 14, label, fs=10, bold=True, color=MUTED,
         valign="middle", bg=bg)
    return b


def subnet(p, layer, x, y, w, h, label, bg=RG_FILL):
    b = box(p, layer, x, y, w, h, "", stroke=SUB_BORDER, fill="none", dash=True)
    text(p, layer, x + 12, y - 7, 200, 14, label, fs=9, bold=True, color=MUTED,
         valign="middle", bg=bg)
    return b


def plan_box(p, x, y, w, plan_name, sku, apps, icon_ref="asp"):
    """A hosting plan drawn as a real container — whatever it runs sits inside it. This is
    what makes a plan legible; a caption floating under an app is not.

    apps: [(icon_ref, label), ...]. Returns the height used.
    """
    h = 34 + len(apps) * 36 + 6
    box(p, p.BASE, x, y, w, h, "", stroke=SUB_BORDER, fill=PAPER)
    icon(p, p.BASE, icon_ref, x + 12, y + 8, "%s  ·  %s" % (plan_name, sku),
         w=18, h=18, side="right", fs=10)
    for n, (ref, lbl) in enumerate(apps):
        icon(p, p.BASE, ref, x + 20, y + 34 + n * 36, lbl, w=26, h=26, side="right", fs=10)
    return h


def pe_column(p, cx, y_pe, y_res, pe_label, res_ref, res_label):
    """Private endpoint directly above the resource it fronts, joined by a short vertical
    private-link line. Alignment does most of the explaining; the line confirms it."""
    pe = icon(p, p.NET, "pe", cx - 12, y_pe, pe_label, w=24, h=24, side="top", fs=8)
    rs = icon(p, p.BASE, res_ref, cx - 16, y_res, res_label, w=32, h=32, side="bottom", fs=9)
    plink(p, p.NET, pe, rs, "", exitp=("0.5", "1"), entryp=("0.5", "0"))
    return rs


def vnet_band(p, x, y, w, h, vnet_name, note, pe_y, pe_cols, res_y, res_cols):
    """A virtual network: snet-app on top, snet-pe below, endpoints lined up over the
    resources they front. res_cols: [(pe_label, res_ref, res_label), ...]"""
    assert len(pe_cols) == len(res_cols), "one private endpoint column per resource"
    assert not res_cols or res_y > y + h, (
        "fronted resources must sit BELOW the network band (endpoint above resource) — "
        "band ends at %d, resources start at %d" % (y + h, res_y))
    group(p, p.NET, x, y, w, h, "Networking - %s" % vnet_name)
    subnet(p, p.NET, x + 12, y + 30, w - 24, 54, "snet-app")
    text(p, p.NET, x + 24, y + 50, w - 48, 28, note, fs=8, color=MUTED)
    subnet(p, p.NET, x + 12, y + 96, w - 24, 74, "snet-pe")
    for n, cx in enumerate(pe_cols):
        pe_column(p, cx, pe_y, res_y, *res_cols[n])


def converge(p, layer, sources, target, target_cx, bus_y, style=telem):
    """Many-to-one along a single shared horizontal, routed through a gap so it crosses no
    labels. sources: [(cell_id, centre_x), ...]"""
    for cid, cx in sources:
        style(p, layer, cid, target, "", exitp=("0.5", "1"), entryp=("0.5", "0"),
              waypoints=[(cx, bus_y), (target_cx, bus_y)])


def badge(p, layer, x, y, n):
    """Numbered step marker. Use these instead of edge labels on sequence diagrams —
    seven labelled arrows will always collide, seven badges never do."""
    cid = p.uid("n")
    style = ("ellipse;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=#FFFFFF;strokeWidth=2;"
             "fontColor=#FFFFFF;fontFamily=%s;fontSize=11;fontStyle=1;align=center;"
             "verticalAlign=middle;" % (INK, FONT))
    p.add('<mxCell id="%s" value="%d" style="%s" vertex="1" parent="%s">%s</mxCell>'
          % (cid, n, style, layer, _geo(x, y, 24, 24)))
    p.track(y, 24)
    return cid


def sample_line(p, layer, x, y, w, style, label):
    """A legend swatch for an edge style."""
    a, b = p.uid("pt"), p.uid("pt")
    inv = "shape=rectangle;fillColor=none;strokeColor=none;html=1;"
    for cid, xx in ((a, x), (b, x + w)):
        p.add('<mxCell id="%s" style="%s" vertex="1" parent="%s">%s</mxCell>'
              % (cid, inv, layer, _geo(xx, y, 1, 1)))
    p.add('<mxCell id="%s" value="" style="%s" edge="1" parent="%s" source="%s" target="%s">'
          '<mxGeometry relative="1" as="geometry"/></mxCell>' % (p.uid("e"), style, layer, a, b))
    text(p, layer, x + w + 14, y - 8, 220, 16, label, fs=10)


# ------------------------------------------------------------- emit/check ---
def emit(pages, margin=40):
    out = io.StringIO()
    out.write('<mxfile host="Electron" type="device">\n')
    for n, pg in enumerate(pages):
        h = pg.maxy + margin                     # canvas trimmed to content, per page
        out.write('  <diagram name="%s" id="page-%d">\n' % (esc(pg.name), n))
        out.write('    <mxGraphModel dx="%d" dy="%d" grid="1" gridSize="10" guides="1" '
                  'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
                  'pageWidth="%d" pageHeight="%d" math="0" shadow="0">\n' % (pg.w, h, pg.w, h))
        out.write('      <root>\n        <mxCell id="0"/>\n')
        for lid, lbl in pg.layers:
            out.write('        <mxCell id="%s" value="%s" parent="0"/>\n' % (lid, esc(lbl)))
        for c in pg.cells:
            out.write("        " + c + "\n")
        out.write('      </root>\n    </mxGraphModel>\n  </diagram>\n')
    out.write("</mxfile>\n")
    return out.getvalue()


def validate(xml, verified=None, banned=()):
    """Structural gate. Raises on anything that would render wrong; returns a report dict.

    `banned` is how you prove removed content stayed removed — pass strings that must not
    appear in any style or value (old colour codes, retired resource names).
    """
    root = ET.fromstring(xml)
    rep = dict(pages=0, cells=0, bad_icons=set(), banned=set(), oob=[], sizes=[])
    for d in root.findall("diagram"):
        m = d.find("mxGraphModel")
        W, H = int(m.get("pageWidth")), int(m.get("pageHeight"))
        rep["pages"] += 1
        rep["sizes"].append((d.get("name"), W, H))
        ids = set()
        for c in d.iter("mxCell"):
            rep["cells"] += 1
            cid = c.get("id")
            assert cid not in ids, "duplicate id %s in %s" % (cid, d.get("name"))
            ids.add(cid)
            st, val = c.get("style") or "", c.get("value") or ""
            if verified and "image=" in st:
                path = st.split("image=", 1)[1].split(";", 1)[0]
                if path not in verified:
                    rep["bad_icons"].add(path)
            for b in banned:
                if b in st or b in val:
                    rep["banned"].add((d.get("name"), b))
            g = c.find("mxGeometry")
            if c.get("vertex") == "1" and g is not None:
                x, y = float(g.get("x") or 0), float(g.get("y") or 0)
                w, h = float(g.get("width") or 0), float(g.get("height") or 0)
                if x < -14 or y < -14 or x + w > W or y + h > H:   # -14: corner icons overhang
                    rep["oob"].append((d.get("name"), cid, x, y, w, h))
        for c in d.iter("mxCell"):
            if c.get("edge") == "1":
                for end in ("source", "target"):
                    assert c.get(end) in ids, "dangling %s in %s" % (end, d.get("name"))
    return rep


def report(rep, verified):
    print("pages=%d cells=%d" % (rep["pages"], rep["cells"]))
    print("icon check:", "SKIPPED (drawio not found)" if not verified
          else (sorted(rep["bad_icons"]) or "all verified"))
    print("banned content:", sorted(rep["banned"]) or "none")
    print("out of bounds:", rep["oob"] or "none")
    for name, w, h in rep["sizes"]:
        print("   %-34s %dx%d" % (name, w, h))
    ok = not rep["bad_icons"] and not rep["banned"] and not rep["oob"]
    print("RESULT:", "ok" if ok else "PROBLEMS ABOVE")
    return ok
