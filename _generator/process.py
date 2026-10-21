"""Turn raw Overpass JSON for Slatina into a compact street dataset + a KML for Google My Maps.

usage: python -I process.py <raw_dir> <out_dir>
"""
import json
import math
import sys
import unicodedata
from collections import defaultdict
from xml.sax.saxutils import escape

sys.stdout.reconfigure(encoding="utf-8")
RAW, OUT = sys.argv[1], sys.argv[2]

hw = json.load(open(f"{RAW}/slatina_highways.json", encoding="utf-8"))
bd = json.load(open(f"{RAW}/slatina_boundary.json", encoding="utf-8"))
OSM_TS = hw["osm3s"]["timestamp_osm_base"]

LAT0, LON0 = 44.43, 24.375
KX = math.cos(math.radians(LAT0)) * 111320.0
KY = 110540.0


def xy(p):
    return ((p[1] - LON0) * KX, (p[0] - LAT0) * KY)


def seg_len(a, b):
    ax, ay = xy(a)
    bx, by = xy(b)
    return math.hypot(bx - ax, by - ay)


def line_len(pts):
    return sum(seg_len(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def simplify(pts, tol=0.8):
    """Douglas-Peucker in local metres."""
    if len(pts) < 3:
        return pts
    if pts[0] == pts[-1]:  # closed ring: a chord of length 0 would drop every vertex, so split it
        h = len(pts) // 2
        return simplify(pts[:h + 1], tol) + simplify(pts[h:], tol)[1:]
    P = [xy(p) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = P[i], P[j]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        best, bi = -1, -1
        for k in range(i + 1, j):
            d = abs(dy * (P[k][0] - x1) - dx * (P[k][1] - y1)) / L
            if d > best:
                best, bi = d, k
        if best > tol:
            keep[bi] = True
            stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]


# ---------- municipality boundary ----------
rel = bd["elements"][0]
segs = [[(g["lat"], g["lon"]) for g in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m["role"] == "outer"]
rings = []
while segs:
    ring = segs.pop(0)
    changed = True
    while changed and ring[0] != ring[-1]:
        changed = False
        for i, s in enumerate(segs):
            if s[0] == ring[-1]:
                ring += s[1:]
            elif s[-1] == ring[-1]:
                ring += s[::-1][1:]
            elif s[-1] == ring[0]:
                ring = s[:-1] + ring
            elif s[0] == ring[0]:
                ring = s[::-1][:-1] + ring
            else:
                continue
            segs.pop(i)
            changed = True
            break
    rings.append(ring)
print("boundary rings:", [len(r) for r in rings], "closed:", [r[0] == r[-1] for r in rings])


def inside(p):
    lat, lon = p
    c = False
    for ring in rings:
        for i in range(len(ring) - 1):
            (la1, lo1), (la2, lo2) = ring[i], ring[i + 1]
            if (la1 > lat) != (la2 > lat):
                x = lo1 + (lat - la1) * (lo2 - lo1) / (la2 - la1)
                if lon < x:
                    c = not c
    return c


# ---------- classify ways ----------
RANK = {"motorway": 1, "trunk": 1, "primary": 2, "secondary": 3, "tertiary": 4,
        "unclassified": 5, "residential": 5, "living_street": 5,
        "motorway_link": 3, "trunk_link": 3, "primary_link": 3, "secondary_link": 4, "tertiary_link": 4,
        "pedestrian": 6, "service": 6, "track": 6,
        "path": 7, "footway": 7, "cycleway": 7, "steps": 8}
SIDEWALKISH = {"path", "footway", "cycleway", "steps"}
UNNAMED_OK = {"secondary", "tertiary", "unclassified", "residential", "living_street"}
PREFIXES = [("Bulevardul ", "bulevard"), ("Strada ", "stradă"), ("Aleea ", "alee"), ("Calea ", "cale"),
            ("Piațeta ", "piațetă"), ("Piața ", "piață"), ("Intrarea ", "intrare"), ("Fundătura ", "fundătură"),
            ("Drumul ", "drum"), ("Șoseaua ", "șosea"), ("Splaiul ", "splai"), ("Prelungirea ", "prelungire")]
STREETY = tuple(p for p, _ in PREFIXES)


def fold(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


ways = []
for e in hw["elements"]:
    if e["type"] != "way" or "geometry" not in e:
        continue
    t = e["tags"]
    h = t.get("highway")
    if h not in RANK:
        continue
    pts = [(g["lat"], g["lon"]) for g in e["geometry"]]
    if not any(inside(p) for p in pts):
        continue
    name = t.get("name")
    if name and h in (SIDEWALKISH | {"service", "track"}) and not name.startswith(STREETY):
        name = None  # "McDrive", "Parcarea Pirelli" etc.
    if not name:
        ref = t.get("ref")
        if h in ("trunk", "motorway") and ref:
            name = f"Drumul Expres {ref}" if ref.startswith("DEx") else ref
        elif h == "primary" and ref:
            name = f"Drumul Național {ref[2:]} ({ref})" if ref.startswith("DN") else ref
    ways.append({"id": e["id"], "h": h, "name": name, "pts": pts})
print("ways inside municipality:", len(ways))

# merge spelling variants (Ionascu / Ionașcu) -> keep the variant carrying diacritics / most length
variants = defaultdict(lambda: defaultdict(float))
for w in ways:
    if w["name"]:
        variants[fold(w["name"])][w["name"]] += line_len(w["pts"])
canon = {}
for k, v in variants.items():
    best = max(v, key=lambda n: (sum(1 for c in n if ord(c) > 127), v[n]))
    for n in v:
        canon[n] = best
        if n != best:
            print("  merged spelling:", n, "->", best)
for w in ways:
    if w["name"]:
        w["name"] = canon[w["name"]]

# per name: drop sidewalk-type ways when the street has real carriageway ways
byname = defaultdict(list)
for w in ways:
    if w["name"]:
        byname[w["name"]].append(w)
for n, ws in byname.items():
    if any(w["h"] not in SIDEWALKISH for w in ws):
        byname[n] = [w for w in ws if w["h"] not in SIDEWALKISH]


def clusters(ws, gap=80.0):
    parent = list(range(len(ws)))

    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    P = [[xy(p) for p in w["pts"]] for w in ws]
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            if f(i) == f(j):
                continue
            if any(math.hypot(a[0] - b[0], a[1] - b[1]) < gap for a in (P[i][0], P[i][-1]) for b in P[j]) or \
               any(math.hypot(a[0] - b[0], a[1] - b[1]) < gap for a in (P[j][0], P[j][-1]) for b in P[i]):
                parent[f(i)] = f(j)
    groups = defaultdict(list)
    for i in range(len(ws)):
        groups[f(i)].append(ws[i])
    return list(groups.values())


def label_point(lines):
    """Point on the street closest to its length-weighted centroid."""
    sx = sy = sl = 0.0
    for pts in lines:
        for a, b in zip(pts, pts[1:]):
            L = seg_len(a, b)
            sx += (a[0] + b[0]) / 2 * L
            sy += (a[1] + b[1]) / 2 * L
            sl += L
    if sl == 0:
        return lines[0][0]
    c = xy((sx / sl, sy / sl))
    best, bp = 1e18, lines[0][0]
    for pts in lines:
        for a, b in zip(pts, pts[1:]):
            (ax, ay), (bx, by) = xy(a), xy(b)
            dx, dy = bx - ax, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, ((c[0] - ax) * dx + (c[1] - ay) * dy) / (dx * dx + dy * dy)))
            px, py = ax + t * dx, ay + t * dy
            d = (px - c[0]) ** 2 + (py - c[1]) ** 2
            if d < best:
                best, bp = d, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return bp


def kind_and_key(name):
    for p, k in PREFIXES:
        if name.startswith(p):
            return k, name[len(p):]
    if name.startswith("Drumul Expres") or name.startswith("Drumul Național"):
        return "drum național", name
    return "", name


def r6(p):
    return [round(p[0], 6), round(p[1], 6)]


# Street names are unique within the municipality; parts of one name that sit apart are the same
# street interrupted in OSM, so a name is one item with a label on every part longer than 80 m.
items = []
for n, ws in byname.items():
    cl = clusters(ws)
    cl.sort(key=lambda g: -sum(line_len(w["pts"]) for w in g))
    lines, lps = [], []
    for ci, g in enumerate(cl):
        part = [simplify(w["pts"]) for w in g]
        lines += part
        if ci == 0 or sum(line_len(w["pts"]) for w in g) >= 80:
            lps.append(r6(label_point(part)))
    kind, key = kind_and_key(n)
    items.append({
        "id": fold(n).replace(" ", "-"),
        "n": n, "k": key, "t": kind,
        "r": min(RANK[w["h"]] for w in ws),
        "len": round(sum(line_len(w["pts"]) for w in ws)),
        "lp": lps,
        "g": [[r6(p) for p in pts] for pts in lines],
    })

# unnamed carriageways: one item per way, context = nearest named street
named_pts = [(it["n"], xy(tuple(p))) for it in items for pts in it["g"] for p in pts[:: max(1, len(pts) // 6)]]
unnamed = [w for w in ways if not w["name"] and w["h"] in UNNAMED_OK]
for w in unnamed:
    pts = simplify(w["pts"])
    lp = label_point([pts])
    c = xy(lp)
    near = min(named_pts, key=lambda q: (q[1][0] - c[0]) ** 2 + (q[1][1] - c[1]) ** 2)
    items.append({
        "id": f"w{w['id']}", "n": "Stradă fără nume", "k": "~", "t": "fără nume în OSM",
        "r": RANK[w["h"]], "len": round(line_len(w["pts"])), "lp": [r6(lp)],
        "g": [[r6(p) for p in pts]], "ctx": f"lângă {near[0]}", "u": 1,
    })

items.sort(key=lambda it: (it.get("u", 0), fold(it["k"]), it.get("ctx", "")))
named_count = sum(1 for it in items if not it.get("u"))
print(f"items: {len(items)}  named/ref streets: {named_count}  unnamed segments: {len(items) - named_count}")
print("multi-part streets:", [(it["n"], len(it["lp"])) for it in items if len(it["lp"]) > 1])

boundary = [[r6(p) for p in simplify(r, 3.0)] for r in rings]
data = {"osm": OSM_TS, "boundary": boundary, "streets": items}
json.dump(data, open(f"{OUT}/streets.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("streets.json bytes:", len(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()))

# ---------- KML for Google My Maps: every named street, one feature each ----------
def kml_coords(pts):
    return " ".join(f"{p[1]},{p[0]},0" for p in pts)


pm = []
for it in items:
    if it.get("u"):
        continue
    title = it["n"] + (f" ({it['ctx']})" if it.get("ctx") else "")
    geo = "".join(f"<LineString><tessellate>1</tessellate><coordinates>{kml_coords(p)}</coordinates></LineString>" for p in it["g"])
    pm.append(
        f"<Placemark><name>{escape(title)}</name>"
        f"<description>{escape((it['t'] or 'drum').capitalize())} · {it['len']} m</description>"
        f"<styleUrl>#strada</styleUrl>"
        f"<ExtendedData><Data name=\"Tip\"><value>{escape(it['t'])}</value></Data>"
        f"<Data name=\"Lungime (m)\"><value>{it['len']}</value></Data></ExtendedData>"
        f"<MultiGeometry>{geo}</MultiGeometry></Placemark>")
kml = (
    '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
    f"<name>Străzi Slatina (OSM {OSM_TS[:10]})</name>"
    "<description>Toate străzile cu nume din municipiul Slatina. Date © OpenStreetMap contributors (ODbL).</description>"
    '<Style id="strada"><LineStyle><color>ff9c5a1a</color><width>3</width></LineStyle></Style>'
    + "".join(pm) + "</Document></kml>")
open(f"{OUT}/Strazi-Slatina-toate.kml", "w", encoding="utf-8").write(kml)
print("KML placemarks:", len(pm), "bytes:", len(kml.encode()))
