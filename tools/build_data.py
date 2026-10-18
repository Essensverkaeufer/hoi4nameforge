"""Pack catalog_thumbs.json + flags into v3 catalog-data.js."""
import sys, os, re, json

CAT, FLAGS, V2HTML, OUT = sys.argv[1:5]

cat = json.load(open(CAT, encoding="utf-8"))
flags = json.load(open(FLAGS, encoding="utf-8"))
v2 = open(V2HTML, encoding="utf-8").read()
builtin = json.loads(re.search(r"const BUILTIN_ICONS = (\[.*?\]);\n", v2, re.S).group(1))
curated = {b["id"]: b for b in builtin}

GROUP_RULES = [
    (r"^texticons", "Text icons"),
    (r"goals_shine", "Focus icons (shine)"),
    (r"goals|focus", "Focus icons"),
    (r"portrait|leader|characters|advisor", "Portraits & characters"),
    (r"ideas|idea_", "National spirits & ideas"),
    (r"technolog|tech_", "Technology"),
    (r"event", "Event pictures"),
    (r"decision", "Decisions"),
    (r"subunit|unit_|division|counter|template", "Units & divisions"),
    (r"tank_|plane_|ship|naval|equipment|designer|modules", "Equipment designer"),
    (r"music|speech|radio", "Music & speeches"),
    (r"intelligence|operation|agency|lar_", "Intelligence & operations"),
    (r"special_project|military_industrial|mio", "MIOs & special projects"),
    (r"state|building|province|map|supply|terrain", "Map, states & buildings"),
    (r"medal|ribbon|achievement|traits?|ace", "Traits, medals & aces"),
    (r"background|frame|tile|bg|window|button|scroll|frontend|menu|core|generic|topbar|bar",
     "UI chrome & backgrounds"),
]

def group_for(file):
    stem = os.path.splitext(os.path.basename(file))[0].lower()
    for pat, g in GROUP_RULES:
        if re.search(pat, stem):
            return g
    return "Other"

groups, files, sources, kinds = [], [], [], []
def idx(lst, v):
    try:
        return lst.index(v)
    except ValueError:
        lst.append(v)
        return len(lst) - 1

rows = []
for e in cat:
    if e["id"] in curated:
        g = "Text icons"
    else:
        g = group_for(e["file"])
    rows.append([
        e["id"],
        curated[e["id"]]["label"] if e["id"] in curated else "",
        idx(groups, g),
        idx(files, e["file"]),
        idx(sources, e["source"]),
        e["frames"],
        (1 if e["always_loaded"] else 0) | (2 if e["id"] in curated else 0),
        idx(kinds, e["kind"]),
        e.get("sheet", -1),
        e.get("slot", -1),
        e.get("w", 0),
        e.get("h", 0),
    ])

# Curated v2 IDs that the scan did not find stay available (kept from v2 as-is).
have = {r[0] for r in rows}
for b in builtin:
    if b["id"] not in have:
        rows.append([b["id"], b["label"], idx(groups, "Text icons"), idx(files, "v2 curated list"),
                     idx(sources, "Vanilla"), b.get("frames", 1), 3, idx(kinds, "spritetype"), -1, -1, 0, 0])

sheets = 1 + max(r[8] for r in rows)
data = {
    "groups": groups, "files": files, "sources": sources, "kinds": kinds,
    "sheets": sheets, "cell": 64, "cols": 32,
    "rows": rows, "flags": flags,
}
with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Generated from the local HoI4 install. Row: id,label,group,file,source,frames,"
            "bits(1=always loaded,2=v2 curated),kind,sheet,slot,frameW,frameH */\n")
    f.write("const CATALOG=" + json.dumps(data, separators=(",", ":")) + ";\n")
print(len(rows), "rows,", sheets, "sheets,", os.path.getsize(OUT) // 1024, "KB")
from collections import Counter
print(Counter(groups[r[2]] for r in rows).most_common())
