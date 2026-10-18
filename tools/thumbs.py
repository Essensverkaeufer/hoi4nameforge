"""Render frame 1 of every catalog sprite into 64px cells packed in WebP atlas sheets."""
import sys, os, json
from multiprocessing import Pool
from PIL import Image

GAME, CATALOG, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
CELL, COLS, ROWS = 64, 32, 32
PER_SHEET = COLS * ROWS

def resolve(root, tex):
    if not tex:
        return None
    base, _ = os.path.splitext(tex)
    for r in (root, GAME):
        for cand in (tex, base + ".dds", base + ".tga", base + ".png"):
            p = os.path.join(r, cand)
            if os.path.isfile(p):
                return p
    return None

def render(job):
    path, frames = job
    try:
        im = Image.open(path)
        im.load()
        im = im.convert("RGBA")
        w, h = im.size
        fw = w // frames if frames > 1 and w >= frames else w
        frame = im.crop((0, 0, fw, h))
        fh = h
        frame.thumbnail((CELL, CELL), Image.LANCZOS)
        return job, (fw, fh, frame.tobytes(), frame.size)
    except Exception as e:
        return job, ("error", str(e)[:120])

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    cat = json.load(open(CATALOG, encoding="utf-8"))
    jobs = {}
    for e in cat:
        p = resolve(e["root"], e["texture"])
        e["_path"] = p
        if p:
            jobs[(p, e["frames"])] = None
    print(len(cat), "sprites,", len(jobs), "unique textures to render")
    results = {}
    with Pool(max(2, os.cpu_count() - 1)) as pool:
        for i, (job, res) in enumerate(pool.imap_unordered(render, list(jobs), chunksize=16)):
            results[job] = res
            if i % 2000 == 0:
                print("rendered", i, flush=True)
    # Pack into sheets; identical texture+frames share one cell.
    cell_of, sheets, sheet, n = {}, [], None, 0
    def flush():
        if sheet is not None:
            idx = len(sheets)
            sheet.save(os.path.join(OUTDIR, f"atlas-{idx:02d}.webp"), "WEBP", quality=82, method=4)
            sheets.append(idx)
    for job, res in results.items():
        if res[0] == "error":
            continue
        if n % PER_SHEET == 0:
            flush()
            sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
        fw, fh, data, size = res
        tile = Image.frombytes("RGBA", size, data)
        slot = n % PER_SHEET
        x, y = (slot % COLS) * CELL, (slot // COLS) * CELL
        sheet.paste(tile, (x + (CELL - size[0]) // 2, y + (CELL - size[1]) // 2))
        cell_of[job] = (n // PER_SHEET, slot, fw, fh)
        n += 1
    flush()
    missing = errors = 0
    for e in cat:
        key = (e["_path"], e["frames"])
        if not e["_path"]:
            missing += 1
        elif key in cell_of:
            e["sheet"], e["slot"], e["w"], e["h"] = cell_of[key]
        else:
            errors += 1
            e["error"] = results.get(key, ("error", "?"))[1]
        del e["_path"]
    json.dump(cat, open(CATALOG.replace(".json", "_thumbs.json"), "w", encoding="utf-8"))
    print("cells", n, "sheets", len(sheets), "missing texture", missing, "decode errors", errors)
