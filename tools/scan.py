"""Scan every sprite definition in vanilla HoI4 + DLC folders and write catalog.json."""
import sys, os, re, glob, json

GAME = sys.argv[1]
OUT = sys.argv[2]

SPRITE_TYPES = {
    "spritetype", "frameanimatedspritetype", "textspritetype", "corneredtilespritetype",
    "progressbartype", "maskedshieldtype", "circularprogressbartype",
}

def strip_comments(text):
    out = []
    for line in text.splitlines():
        res, inq = [], False
        for ch in line:
            if ch == '"':
                inq = not inq
            if ch == '#' and not inq:
                break
            res.append(ch)
        out.append("".join(res))
    return "\n".join(out)

TOKEN = re.compile(r'"[^"]*"|[{}=]|[^\s{}="]+')

def parse(text):
    """Minimal Clausewitz parser -> list of (key, value) where value is str or list."""
    toks = TOKEN.findall(strip_comments(text))
    pos = 0
    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1
                return items
            if pos + 1 < len(toks) and toks[pos + 1] == "=":
                key = t; pos += 2
                if pos < len(toks) and toks[pos] == "{":
                    pos += 1
                    items.append((key, block()))
                elif pos < len(toks):
                    items.append((key, toks[pos].strip('"'))); pos += 1
            elif t == "{":
                pos += 1; items.append((None, block()))
            else:
                pos += 1
        return items
    return block()

def walk(items, found):
    for k, v in items:
        if isinstance(v, list):
            if k and k.lower() in SPRITE_TYPES:
                found.append((k, v))
            else:
                walk(v, found)

def field(items, name):
    for k, v in items:
        if k and k.lower() == name and not isinstance(v, list):
            return v
    return None

roots = [("Vanilla", GAME)]
for d in sorted(glob.glob(os.path.join(GAME, "integrated_dlc", "*"))):
    roots.append(("Integrated: " + os.path.basename(d), d))
for d in sorted(glob.glob(os.path.join(GAME, "dlc", "*"))):
    roots.append(("DLC: " + os.path.basename(d), d))

entries, seen = [], {}
for source, root in roots:
    files = sorted(glob.glob(os.path.join(root, "interface", "**", "*.gfx"), recursive=True))
    for f in files:
        try:
            text = open(f, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        found = []
        walk(parse(text), found)
        rel = os.path.relpath(f, root).replace("\\", "/")
        for kind, body in found:
            name = field(body, "name")
            if not name:
                continue
            tex = field(body, "texturefile") or field(body, "texturefile1") or ""
            frames = field(body, "noofframes")
            lazy = field(body, "legacy_lazy_load")
            e = {
                "id": name[4:] if name.startswith("GFX_") else name,
                "name": name,
                "kind": kind.lower(),
                "texture": tex.replace("\\", "/"),
                "frames": max(1, int(frames)) if frames and frames.isdigit() else 1,
                "always_loaded": (lazy or "").lower() == "no",
                "file": rel,
                "source": source,
                "root": root,
            }
            if e["name"] in seen:
                entries[seen[e["name"]]]["dupes"] = entries[seen[e["name"]]].get("dupes", 0) + 1
                continue
            seen[e["name"]] = len(entries)
            entries.append(e)

json.dump(entries, open(OUT, "w", encoding="utf-8"))
from collections import Counter
print(len(entries), "unique sprites")
print(Counter(e["kind"] for e in entries))
print("always loaded:", sum(e["always_loaded"] for e in entries))
print(Counter(e["source"].split(":")[0] for e in entries))
print("no texture:", sum(1 for e in entries if not e["texture"]))
