#!/usr/bin/env python3
"""Bins and labels: turn plan/kits.yaml into a kitting guide and label files.

  python tools/kitting.py                      # defaults from plan/options.yaml; writes docs/KITTING.md, docs/labels.csv, docs/labels.html
  python tools/kitting.py --on gen2,dryer      # exactly these options on
  python tools/kitting.py --box 16             # slots (1x1 units) per container, for the box plan
  python tools/kitting.py --tape 12 --mm 36    # label tape height and the usable label length on a 1x1 bin, in mm
  python tools/kitting.py --trays 6            # use up to six 1x4 bins divided into 8 compartments in place of 1x1 bins
  python tools/kitting.py --trays all --suffix=-trays   # as many trays as it takes; write KITTING-trays.md, labels-trays.*

The label files are made for 12 mm label tape (P-touch and the like): two lines per label,
line 1 is the phase and the contents, line 2 the row codes and manual steps.
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import re
import sys

import planlib as pl


def slots(size: str) -> int:
    a, b = size.lower().split("x")
    return int(a) * int(b)


def qty_text(b: dict) -> str:
    q = b.get("qty")
    if q is None:
        return ""
    return f"x{q}" if isinstance(q, int) else str(q)


def line1(b: dict, pn: int) -> str:
    q = b.get("qty")
    name = b.get("label") or b["part"]
    if isinstance(q, int) and f"x{q}" not in name:
        return f"P{pn} {name} x{q}"
    return f"P{pn} {name}"


def short(b: dict) -> str:
    """One-line label for a tray compartment."""
    if b.get("short"):
        return str(b["short"])
    name = re.sub(r"^(Keep|Kept) ", "", b.get("label") or b["part"])
    q = b.get("qty")
    return f"{name} x{q}" if isinstance(q, int) and f"x{q}" not in name else name


def line2(b: dict) -> str:
    if b.get("line2"):
        return str(b["line2"])
    rows = " ".join(b.get("rows") or [])
    steps = " ".join(b.get("steps") or [])
    out = rows
    if steps:
        out = f"{out}  {steps}" if out else steps
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--on", help="comma-separated option ids to turn on, or 'none'")
    ap.add_argument("--box", type=int, default=20, help="1x1 slots per container (default 20, a 4x5 box)")
    ap.add_argument("--tape", type=float, default=12, help="label tape height in mm (default 12)")
    ap.add_argument("--mm", type=float, default=36, help="usable label length on a 1x1 bin in mm (default 36)")
    ap.add_argument("--out", default="docs", help="folder for labels.csv and labels.html (default docs)")
    ap.add_argument("--trays", default="0", help="how many 1x4 bins with 8 compartments you have (a number, or 'all')")
    ap.add_argument("--suffix", default="", help="added to the output file names, e.g. -trays")
    args = ap.parse_args()

    options = pl.load_options()
    if args.on is None:
        on = {o["id"] for o in options if o["default"]}
    else:
        on = set() if args.on.strip() in ("", "none") else {x.strip() for x in args.on.split(",")}
    kits = pl.load_yaml("plan", "kits.yaml")
    phases = pl.load_phases()
    pindex = {p["id"]: n for n, p in enumerate(phases)}
    pname = {p["id"]: p["name"] for p in phases}
    bins = [b for b in kits["bins"] if pl.visible(b, on)]
    for b in bins:
        b.setdefault("size", "1x1")
        if b["phase"] not in pindex:
            print(f"kits.yaml: bin {b['id']} names unknown phase {b['phase']}", file=sys.stderr)
            return 1
    known_rows = {s["id"] for p in phases for s in p["steps"]}
    bad = [(b["id"], r) for b in bins for r in b.get("rows") or [] if r not in known_rows]
    if bad:
        print("kits.yaml names rows that do not exist: " + ", ".join(f"{b}:{r}" for b, r in bad), file=sys.stderr)
        return 1

    by_phase: dict[str, list[dict]] = {}
    for b in bins:
        by_phase.setdefault(b["phase"], []).append(b)
    order = [p["id"] for p in phases if p["id"] in by_phase]

    # ---- divided trays: a 1x4 bin with 8 compartments replaces up to eight 1x1 bins of one phase ----
    trays_left = 10 ** 6 if args.trays == "all" else int(args.trays)
    trays: list[dict] = []
    if trays_left:
        for pid in order:
            small = [b for b in by_phase[pid] if b["size"] == "1x1" and b.get("tray", True)]
            while len(small) >= 5 and trays_left:
                group, small = small[:8], small[8:]
                trays_left -= 1
                tray = {"id": f"t{pid[1:]}{chr(ord('a') + sum(1 for x in trays if x['phase'] == pid))}", "phase": pid, "size": "1x4",
                        "part": "Divided tray", "label": f"Tray {chr(ord('A') + sum(1 for x in trays if x['phase'] == pid))}",
                        "kind": "tray", "source": "", "compartments": group, "text": f"{len(group)} compartments"}
                trays.append(tray)
                for b in group:
                    b["in_tray"] = tray["id"]
            # the tray takes the place of its first bin, so the phase's order stays readable
        for pid in order:
            rebuilt = []
            seen = set()
            for b in by_phase[pid]:
                if b.get("in_tray"):
                    if b["in_tray"] not in seen:
                        seen.add(b["in_tray"]); rebuilt.append(next(tr for tr in trays if tr["id"] == b["in_tray"]))
                else:
                    rebuilt.append(b)
            by_phase[pid] = rebuilt

    # ---- box plan: a phase's bins all sit in one box; a box may hold several phases, not
    #      necessarily consecutive, since only the current phase's box is open. Largest phase
    #      first, into the first box with room (first-fit decreasing), then the boxes are
    #      numbered by the earliest phase they hold. ----
    need = {pid: sum(slots(b["size"]) for b in by_phase[pid]) for pid in order}
    boxes: list[dict] = []
    for pid in sorted(order, key=lambda x: (-need[x], pindex[x])):
        home = next((bx for bx in boxes if bx["used"] + need[pid] <= args.box), None)
        if home is None:
            home = {"phases": [], "used": 0}
            boxes.append(home)
        home["phases"].append(pid); home["used"] += need[pid]
    for bx in boxes:
        bx["phases"].sort(key=lambda x: pindex[x])
    boxes.sort(key=lambda bx: pindex[bx["phases"][0]])

    # ---- guide ----
    on_text = ", ".join(sorted(on)) or "none"
    tray_note = (f" {len(trays)} of the bins are 1x4 trays with 8 compartments, each standing in for up to eight 1x1 bins of one phase." if trays else "")
    md = [f"# {kits['title']}", "", f"Options on: {on_text}. Generated by `tools/kitting.py` from `plan/kits.yaml`; do not edit by hand.", "",
          " ".join(kits["note"].split()), "",
          f"**{sum(len(v) for v in by_phase.values())} bins, {sum(slots(b['size']) for v in by_phase.values() for b in v)} slots of 1x1.** Sizes are Gridfinity units (1x1 = 42 × 42 mm).{tray_note}",
          "Plus two standing bins: " + " and ".join(f"**{s['label']}** ({s['size']}, {s['part'].lower()})" for s in kits["spares"]) + ".", ""]
    md += ["## What is open on the bench", "", "| Phase | Bins | 1x1 slots |", "|---|---|---|"]
    for pid in order:
        md.append(f"| P{pindex[pid]} {pname[pid]} | {len(by_phase[pid])} | {sum(slots(b['size']) for b in by_phase[pid])} |")
    md += ["", f"## Boxes ({args.box} slots each)", "",
           "Only the current phase's box is open. A box can hold phases that are not next to each other; it is simply opened again when its next phase comes. The Phase 3 bins are filled during the teardown and emptied into the phase bins at the end of it, so from then on their slots are free.", ""]
    for n, bx in enumerate(boxes, 1):
        md.append(f"- **Box {n}** ({bx['used']} of {args.box} slots): " + ", ".join(f"P{pindex[p]} {pname[p]}" for p in bx["phases"]))
    md.append("")
    for pid in order:
        md += [f"## P{pindex[pid]} {pname[pid]}", "", "| Bin | Label | Part | How many | From | Rows and steps | Size | Note |", "|---|---|---|---|---|---|---|---|"]
        for b in by_phase[pid]:
            q = b.get("qty")
            qty = str(q) if q is not None else ""
            note = " ".join(str(b.get("text", "")).split())
            md.append(f"| `{b['id']}` | {line1(b, pindex[pid])} | {b['part']} | {qty} | {b['kind']}{': ' + b['source'] if b.get('source') else ''} | {line2(b)} | {b['size']} | {note} |")
            for n, c in enumerate(b.get("compartments") or [], 1):
                cq = c.get("qty")
                md.append(f"| `{c['id']}` | ↳ {n}: {short(c)} | {c['part']} | {cq if cq is not None else ''} | {c['kind']}: {c.get('source', '')} | {line2(c)} | slot | {' '.join(str(c.get('text', '')).split())} |")
        md.append("")
    md_path = pl.path("docs", f"KITTING{args.suffix}.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    # ---- labels ----
    out = pl.path(args.out)
    os.makedirs(out, exist_ok=True)
    labels = []
    for n, bx in enumerate(boxes, 1):
        labels.append((f"BOX {n}", " + ".join(f"P{pindex[p]} {pname[p]}" for p in bx["phases"]), "box"))
    for s in kits["spares"]:
        labels.append((s["label"], s["part"], s["size"]))
    for pid in order:
        for b in by_phase[pid]:
            if b.get("compartments"):
                labels.append((line1(b, pindex[pid]), f"{len(b['compartments'])} compartments, see the guide", "1x4"))
                for n, c in enumerate(b["compartments"], 1):
                    labels.append((f"{n} {short(c)}", "", "slot"))
            else:
                labels.append((line1(b, pindex[pid]), line2(b), b["size"]))
    with open(os.path.join(out, f"labels{args.suffix}.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["line1", "line2", "size"])
        w.writerows(labels)

    tape, length = args.tape, args.mm
    cells = []
    for l1, l2, size in labels:
        if size == "slot":  # one compartment of a divided tray: half a unit wide, one line
            cells.append(f'<div class="lab one" style="width:{length / 2 + 1:.0f}mm;height:{tape}mm"><b>{html.escape(l1)}</b></div>')
            continue
        units = 1 if size == "box" else int(size.lower().split("x")[1])  # the label sits along the long side
        width = length * units + (units - 1) * 6
        cells.append(f'<div class="lab" style="width:{width}mm;height:{tape}mm"><b>{html.escape(l1)}</b><span>{html.escape(l2)}</span></div>')
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Bin labels</title>
<style>
@page{{margin:10mm}}
body{{font-family:"Atkinson Hyperlegible Next","Atkinson Hyperlegible",Arial,sans-serif;margin:10mm;color:#000;background:#fff}}
h1{{font-size:14pt;margin:0 0 4mm}} p{{font-size:9pt;margin:0 0 5mm;max-width:160mm}}
.sheet{{display:flex;flex-wrap:wrap;gap:3mm}}
.lab{{box-sizing:border-box;border:0.2mm dashed #999;padding:0.8mm 1.5mm;display:flex;flex-direction:column;justify-content:center;overflow:hidden;line-height:1.05;break-inside:avoid}}
.lab.one b{{font-size:{tape * 0.42:.1f}mm}}
.lab b{{font-size:{tape * 0.34:.1f}mm;white-space:nowrap;display:block}} .lab span{{font-size:{tape * 0.22:.1f}mm;white-space:nowrap;color:#222;display:block}}
@media print{{h1,p{{display:none}} body{{margin:0}} .lab{{border-color:#bbb}}}}
</style></head><body>
<h1>Bin labels</h1>
<p>Options on: {html.escape(on_text)}. Each label is drawn at {tape:g} mm tall and {length:g} mm per 1x1 unit, which is what 12 mm label tape gives on a Gridfinity bin.
Print at 100 % and cut, or type the two lines into a label maker; <code>labels.csv</code> has the same text for a label printer's import.</p>
<div class="sheet">{"".join(cells)}</div>
<script>
/* shrink a line until it fits its label, the way a label printer's auto-fit does */
document.querySelectorAll(".lab b, .lab span").forEach(function (el) {{
  var size = parseFloat(getComputedStyle(el).fontSize);
  while (el.scrollWidth > el.clientWidth && size > 4) {{ size -= 0.5; el.style.fontSize = size + "px"; }}
}});
</script></body></html>
'''
    with open(os.path.join(out, f"labels{args.suffix}.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    long1 = [l1 for l1, _, size in labels if size == "1x1" and len(l1) > 18]
    print(f"{sum(len(v) for v in by_phase.values())} bins ({len(trays)} trays) in {len(order)} phases, {len(boxes)} boxes of {args.box}; "
          f"wrote docs/KITTING{args.suffix}.md, {args.out}/labels{args.suffix}.csv, {args.out}/labels{args.suffix}.html")
    if long1:
        print(f"{len(long1)} line-1 labels are over 18 characters and will print small on a 1x1 bin: " + "; ".join(long1[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
