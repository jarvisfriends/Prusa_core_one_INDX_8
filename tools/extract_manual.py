#!/usr/bin/env python3
"""Pull every step's pictures and colour-keyed text out of Prusa's PDF manuals.

Reads the PDFs in manuals/ (see manuals/manuals.yaml), writes:
  manuals/steps/<id>.json   one entry per step: title, picture count, picture file, text items
  manuals/img/<prefix><chapter>-<step>.jpg   the step's pictures side by side, 800x600 each
  manuals/PICTURES.md       every picture file with a link to the step it came from on Prusa's site

The pictures are the JPEGs embedded in the PDF, copied out as they are. Nothing is
rendered or screenshotted. The output is Prusa Research's material; it is committed so
the page builds anywhere, and every picture links back to its step on help.prusa3d.com.

You only need to run this when Prusa revises a manual:
  python tools/extract_manual.py          # needs the PDFs in manuals/, PyMuPDF and Pillow
  python tools/extract_manual.py --index  # only rewrite manuals/PICTURES.md
"""
from __future__ import annotations

import collections
import glob
import io
import json
import os
import re
import sys


import planlib as pl

CELL = (800, 600)
JPEG_QUALITY = 74


def hex_colour(c) -> str:
    if isinstance(c, int):
        return "#%06x" % c
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c)


def page_order(name: str):
    """Sort a manual split into '...-pages-1.pdf', '...-pages-2.pdf' by part number."""
    m = re.search(r"pages?-(\d+)", os.path.basename(name))
    return (int(m.group(1)) if m else 0, os.path.basename(name))


def read_steps(paths: list[str]) -> "collections.OrderedDict[str, dict]":
    import pymupdf
    steps: collections.OrderedDict[str, dict] = collections.OrderedDict()
    cur = None
    chapter = None
    for pdf in paths:
        doc = pymupdf.open(pdf)
        for page in doc:
            lines, pictures, icons, heads = [], [], [], []
            for b in page.get_text("dict")["blocks"]:
                if b["type"] == 1:
                    x0, y0, x1, y1 = b["bbox"]
                    if x1 - x0 < 30:  # the small info / warning / tip icons
                        icons.append({"y0": y0, "y1": y1, "x": x0, "size": (b["width"], b["height"]), "used": False})
                    else:
                        pictures.append((round(y0), round(x0), b["image"]))
                    continue
                for ln in b["lines"]:
                    spans = [s for s in ln["spans"] if s["text"]]
                    text = "".join(s["text"] for s in spans)
                    if not text.strip():
                        continue
                    x0, y0, x1, y1 = ln["bbox"]
                    if y0 < 50 and spans[0]["size"] <= 10.5:  # running header: "3. Z-axis upgrade"
                        m = re.match(r"\s*(\d+)[.:]\s", text)
                        if m:
                            chapter = int(m.group(1))
                        continue
                    if y0 > 715:  # page footer
                        continue
                    if "Cocogoose" in spans[0]["font"] and text.strip().startswith("STEP"):
                        m = re.match(r"\s*STEP\s+(\d+)\s*(.*)", text)
                        heads.append((y0, int(m.group(1)), m.group(2).strip()))
                        continue
                    if spans[0]["size"] > 12:  # chapter title pages
                        continue
                    lines.append({"x": x0, "xe": x1, "y0": y0, "y1": y1,
                                  "spans": [(s["text"], "Medium" in s["font"] or "Bold" in s["font"], s["color"]) for s in spans]})
            markers = []
            for d in page.get_drawings():
                r = d["rect"]
                if d["type"] == "f" and r.width < 12 and r.height < 12 and d.get("fill") is not None:
                    markers.append({"y0": r.y0, "y1": r.y1, "x": r.x0, "colour": hex_colour(d["fill"]), "used": False})

            # join fragments that sit on one baseline
            lines.sort(key=lambda l: (round(l["y0"]), l["x"]))
            merged = []
            for l in lines:
                if merged and abs(merged[-1]["y0"] - l["y0"]) < 3 and l["x"] > merged[-1]["x"] and l["x"] - merged[-1]["xe"] < 40:
                    merged[-1]["spans"] += l["spans"]
                    merged[-1]["xe"] = l["xe"]
                else:
                    merged.append(l)

            events = [(h[0], 0, "head", h) for h in heads] + [(l["y0"], 1, "line", l) for l in merged] + [(p[0], 1, "pic", p) for p in pictures]
            events.sort(key=lambda e: (e[0], e[1]))
            for _, _, kind, obj in events:
                if kind == "head":
                    key = f"{chapter}.{obj[1]}"
                    cur = steps.setdefault(key, {"title": obj[2], "pics": [], "items": [], "last": None})
                    continue
                if cur is None:
                    continue
                if kind == "pic":
                    cur["pics"].append(obj)
                    continue
                l = obj
                mid = (l["y0"] + l["y1"]) / 2
                marker = next((m for m in markers if not m["used"] and m["y0"] - 3 <= mid <= m["y1"] + 3 and 0 < l["x"] - m["x"] < 40), None)
                icon = next((i for i in icons if not i["used"] and i["y0"] - 3 <= mid <= i["y1"] + 3 and 0 < l["x"] - i["x"] < 45), None)
                segs = [[t, bold] for t, bold, _ in l["spans"]]
                red = all(colour == 0xFF0000 for t, _, colour in l["spans"] if t.strip())
                if marker:
                    marker["used"] = True
                    item = {"k": "b", "c": marker["colour"], "x": l["x"], "segs": segs}
                elif icon:
                    icon["used"] = True
                    kind2 = "warn" if red or icon["size"] == (170, 170) else "info"
                    item = {"k": kind2, "x": l["x"], "segs": segs}
                else:
                    last = cur["last"]
                    if last is not None and abs(last["x"] - l["x"]) < 3 and l["y0"] - last["y"] < 20:
                        if last["segs"] and not last["segs"][-1][0].endswith((" ", "-")):
                            last["segs"].append([" ", False])
                        last["segs"] += segs
                        last["y"] = l["y0"]
                        continue
                    item = {"k": "p", "x": l["x"], "segs": segs}
                item["y"] = l["y0"]
                cur["items"].append(item)
                cur["last"] = item
    return steps


def to_text(segs: list) -> str:
    joined = []
    for t, bold in segs:
        if joined and joined[-1][1] == bold:
            joined[-1][0] += t
        else:
            joined.append([t, bold])
    out = ""
    for t, bold in joined:
        if bold and t.strip():
            out += (" " if t.startswith(" ") else "") + "**" + t.strip() + "**" + (" " if t.endswith(" ") else "")
        else:
            out += t
    out = out.replace("** **", " ")
    return re.sub(r"\s+", " ", out).strip()


def write_manual(key: str, man: dict, out_json: str, out_img: str) -> tuple[int, int]:
    from PIL import Image
    files = sorted(glob.glob(pl.path("manuals", man["files"])), key=page_order)
    if not files:
        print(f"  {man['label']}: no PDF matching manuals/{man['files']} (skipped)")
        return 0, 0
    steps = read_steps(files)
    result = {}
    pictures = 0
    for step_key, s in steps.items():
        ch, n = step_key.split(".")
        cells = []
        for _, _, data in sorted(s["pics"], key=lambda p: (round(p[0] / 8), p[1])):
            im = Image.open(io.BytesIO(data)).convert("RGB")
            if im.size != CELL:
                canvas = Image.new("RGB", CELL, (255, 255, 255))
                im.thumbnail(CELL)
                canvas.paste(im, ((CELL[0] - im.width) // 2, (CELL[1] - im.height) // 2))
                im = canvas
            cells.append(im)
        name = None
        if cells:
            strip = Image.new("RGB", (CELL[0] * len(cells), CELL[1]))
            for i, c in enumerate(cells):
                strip.paste(c, (CELL[0] * i, 0))
            name = f"{man['image_prefix']}{ch}-{n}.jpg"
            strip.save(os.path.join(out_img, name), quality=JPEG_QUALITY, optimize=True, progressive=True)
            pictures += len(cells)
        items = []
        for it in s["items"]:
            entry = {"k": it["k"], "t": to_text(it["segs"])}
            if it["k"] == "b":
                entry["c"] = it["c"]
            if entry["t"]:
                items.append(entry)
        result[f"{man['prefix']}{step_key}"] = {"title": s["title"], "n": len(cells), "img": name, "items": items}
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    expected = sum(man["chapters"].values())
    flag = "" if len(result) == expected else f"  (manuals.yaml expects {expected}: has the manual been revised?)"
    print(f"  {man['label']}: {len(result)} steps, {pictures} pictures{flag}")
    return len(result), pictures


def write_picture_index(manuals: dict) -> int:
    """manuals/PICTURES.md: where every picture file came from."""
    data = pl.load_steps(manuals)
    out = ["# Where the pictures come from", "",
           "Every file in `manuals/img/` holds the pictures of one manual step, side by side. They are the",
           "JPEGs embedded in Prusa Research's PDF manuals, copied out by `tools/extract_manual.py` and",
           "re-saved as one strip per step. The pictures and the step text in `manuals/steps/` are Prusa's;",
           "they are here so the build plan can show them next to each row. Each line below links to the",
           "step on help.prusa3d.com, where the original full-size pictures and the readers' comments are.", "",
           "This file is generated. Do not edit it by hand.", ""]
    count = 0
    for key, man in manuals.items():
        out += [f"## {man['title']}", "", f"Manual: <{man['url']}> ({man['version']})", ""]
        for ch, steps in man["chapters"].items():
            rows = []
            for n in range(1, steps + 1):
                ref = f"{man['prefix']}{ch}.{n}"
                step = data.get(ref)
                if not step or not step["img"]:
                    continue
                rows.append(f"| `{step['img']}` | {step['n']} | [{ch}.{n} {step['title']}]({pl.step_url(ref, manuals)}) |")
                count += 1
            if rows:
                out += [f"### Chapter {ch}", "", "| File | Pictures | Step on Prusa's site |", "|---|---|---|", *rows, ""]
    with open(pl.path("manuals", "PICTURES.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return count


def main() -> int:
    manuals = pl.load_manuals()
    if "--index" in sys.argv[1:]:
        print(f"manuals/PICTURES.md: {write_picture_index(manuals)} picture files listed")
        return 0
    out_manual = pl.path("manuals", "steps")
    out_img = pl.path("manuals", "img")
    os.makedirs(out_manual, exist_ok=True)
    os.makedirs(out_img, exist_ok=True)
    print("Extracting manuals:")
    total = 0
    for key, man in manuals.items():
        n, _ = write_manual(key, man, os.path.join(out_manual, f"{key}.json"), out_img)
        total += n
    if not total:
        print("No PDFs found. See manuals/README.md for where to download them.")
        return 1
    print(f"manuals/PICTURES.md: {write_picture_index(manuals)} picture files listed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
