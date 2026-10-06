#!/usr/bin/env python3
"""Assemble the page from plan/, site/ and (if present) the extracted manuals in build/.

Writes:
  dist/index.html      a complete page: open it in a browser
  dist/artifact.html   the same page without <html>/<head>, the form claude.ai artifacts take
  dist/img/            the step pictures the page uses

Run tools/extract_manual.py first to get pictures. Without it the page still builds,
with a link to Prusa's online guide in place of each picture set.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys

import planlib as pl

KIND_LABEL = {"asis": "as printed", "moved": "moved", "gen2": "Gen 2", "added": "added", "opt": "optional", "skip": "skip"}
NOTE_LABEL = {"why": "Why here", "tip": "Tip", "warn": "Watch"}
SUB_LABEL = {"info": "Note", "warn": "Careful"}
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fmt(s: str) -> str:
    """Escape, then apply the three bits of inline markup the data files may use."""
    out = esc(s)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    return out


def ref_text(refs: list[str], manuals: dict) -> str:
    groups: dict[tuple[str, int], list[int]] = {}
    for r in refs:
        key, ch, n = pl.manual_for_ref(r, manuals)
        groups.setdefault((key, ch), []).append(n)
    parts = []
    for (key, ch), nums in groups.items():
        runs, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            runs.append(f"{nums[i]}–{nums[j]}" if j > i else str(nums[i]))
            i = j + 1
        word = "steps" if len(nums) > 1 else "step"
        parts.append(f"{manuals[key]['label']} ch {ch} · {word} {', '.join(runs)}")
    return "  +  ".join(parts)


def manual_block(ref: str, manuals: dict, data: dict, used_images: set) -> str:
    key, ch, n = pl.manual_for_ref(ref, manuals)
    man = manuals[key]
    label = f"{man['label']} {ch}.{n}"
    step = data.get(ref)
    if step is None:
        url = man.get("chapter_urls", {}).get(ch, man["url"])
        return (f'<p class="pending"><span class="mref">{esc(label)}</span> Pictures are not built into this copy. '
                f'<a href="{esc(url)}">Open chapter {ch} of Prusa\'s {esc(man["label"])} guide</a>, step {n}.</p>')
    body = []
    if step["img"]:
        used_images.add(step["img"])
        cells = "".join(
            f'<button type="button" class="pic" data-i="{i}" aria-label="Enlarge picture {i + 1} of {step["n"]}, {esc(label)}"></button>'
            for i in range(step["n"]))
        body.append(f'<div class="pics" data-img="img/{step["img"]}" data-n="{step["n"]}" data-label="{esc(label)} · {esc(step["title"])}">{cells}</div>')
    items = []
    for it in step["items"]:
        text = fmt(it["t"])
        if it["k"] == "b":
            black = it.get("c", "#000000") == "#000000"
            dot = '<span class="dot k"></span>' if black else f'<span class="dot" style="background:{esc(it["c"])}"></span>'
            items.append(f"<li>{dot}<span>{text}</span></li>")
        elif it["k"] in SUB_LABEL:
            items.append(f'<li class="sub {it["k"]}"><span class="mk">{SUB_LABEL[it["k"]]}</span><span>{text}</span></li>')
        else:
            items.append(f'<li class="plain"><span>{text}</span></li>')
    if items:
        body.append('<ul class="mtext">' + "".join(items) + "</ul>")
    return (f'<details class="man" open><summary><span class="mref">{esc(label)}</span>{esc(step["title"])}</summary>'
            f'<div class="man-body">{"".join(body)}</div></details>')


def render_phases(phases: list[dict], manuals: dict, data: dict, used_images: set) -> tuple[str, str, int]:
    out, nav, rows = [], [], 0
    for i, p in enumerate(phases):
        nav.append(f'<a href="#{esc(p["id"])}" data-phase="{esc(p["id"])}">{i} {esc(p["name"])}</a>')
        on = p["power"] == "on"
        out.append(f'<section class="phase" id="{esc(p["id"])}"><div class="phase-head"><span class="phase-num">Phase {i}</span>'
                   f'<h2>{esc(p["title"])}</h2><span class="chip{" pwr-on" if on else ""}">{"Power on" if on else "Unplugged"}</span>'
                   f'<span class="chip">{esc(p["where"])}</span></div>')
        if p.get("note"):
            out.append(f'<p class="phase-note">{fmt(p["note"])}</p>')
        out.append('<ul class="steps">')
        for s in p["steps"]:
            rows += 1
            meta = ""
            if s["refs"]:
                meta += f'<span class="refs">{esc(ref_text(s["refs"], manuals))}</span>'
            meta += f'<span class="tag tag-{s["kind"]}">{KIND_LABEL[s["kind"]]}</span>'
            meta += "".join(f'<span class="tool">{esc(t)}</span>' for t in s.get("tools") or [])
            notes = "".join(
                f'<li class="{n["type"]}"><b>{NOTE_LABEL[n["type"]]}</b>{fmt(n["text"])} <span class="by">({esc(n["by"])})</span></li>'
                for n in s.get("notes") or [])
            blocks = "".join(manual_block(r, manuals, data, used_images) for r in s["refs"])
            out.append(
                f'<li class="step" data-phase="{esc(p["id"])}"><input type="checkbox" id="cb-{esc(s["id"])}" data-id="{esc(s["id"])}" '
                f'aria-label="Done: {esc(p["name"])}, row {esc(s["id"])}"><div class="body"><div class="meta">{meta}</div>'
                f'<div class="text">{fmt(s["text"])}</div>'
                + (f'<ul class="notes">{notes}</ul>' if notes else "") + blocks + "</div></li>")
        out.append("</ul></section>")
    return "\n".join(out), "".join(nav), rows


def render_intro(intro: dict, prints: dict, hardware: dict, sources: dict) -> dict:
    v = {k: esc(intro[k]) for k in ("page_title", "eyebrow", "title", "changes_title")}
    v["lede"] = fmt(intro["lede"])
    v["power"] = "\n".join(
        f'    <div class="{"on" if p["state"] == "on" else "off"}"><b>{esc(p["label"])}</b>{esc(p["text"])}</div>' for p in intro["power"])
    v["changes"] = "\n".join(f"      <li>{fmt(c)}</li>" for c in intro["changes"])
    v["assumptions"] = "\n".join(f"    <p>{fmt(a)}</p>" for a in intro["assumptions"])
    v["pictures_note"] = fmt(intro["pictures_note"])
    v["legend"] = "\n".join(
        f'    <span><span class="tag tag-{esc(l["kind"])}">{KIND_LABEL[l["kind"]]}</span> {esc(l["text"])}</span>' for l in intro["legend"])
    v["prints_title"] = esc(prints["title"])
    v["prints_note"] = fmt(prints["note"])
    cards = []
    for it in prints["items"]:
        models = ' <span class="by">and</span> '.join(
            f'<a href="{esc(m["url"])}">{esc(m["name"])}</a><span class="by">{esc(m["by"])}</span>' for m in it["models"])
        cards.append(f'      <li class="print"><div class="print-head"><span class="pill {esc(it["verdict_class"])}">{esc(it["verdict"])}</span>'
                     f'{models}</div><p>{fmt(it["text"])}</p></li>')
    v["prints"] = "\n".join(cards)
    v["hardware_title"] = esc(hardware["title"])
    v["hardware_note"] = fmt(hardware["note"])
    head = "<thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in hardware["columns"]) + "</tr></thead>"
    body = "".join("<tr>" + "".join(f'<td{" class=\"num\"" if i == 1 else ""}>{fmt(c)}</td>' for i, c in enumerate(r)) + "</tr>" for r in hardware["rows"])
    v["hardware"] = f"        {head}\n        <tbody>{body}</tbody>"
    v["sources_title"] = esc(sources["title"])
    v["sources"] = ("\n".join(f"  <p>{fmt(p)}</p>" for p in sources["paragraphs"]) + "\n  <ul>\n"
                    + "\n".join(f"    <li>{fmt(l)}</li>" for l in sources["links"]) + "\n  </ul>")
    return v


SKELETON = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            "<style>:root{color-scheme:light;box-sizing:border-box}body{margin:0}img{max-width:100%}"
            "[hidden]{display:none!important}</style></head><body>\n")


def main() -> int:
    manuals = pl.load_manuals()
    phases = pl.load_phases()
    data: dict = {}
    for key in manuals:
        f = pl.path("build", "manual", f"{key}.json")
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                data.update(json.load(fh))
    used_images: set = set()
    values = render_intro(pl.load_yaml("plan", "intro.yaml"), pl.load_yaml("plan", "prints.yaml"),
                          pl.load_yaml("plan", "hardware.yaml"), pl.load_yaml("plan", "sources.yaml"))
    values["phases"], values["nav"], rows = render_phases(phases, manuals, data, used_images)
    values["row_count"] = str(rows)
    with open(pl.path("site", "style.css"), encoding="utf-8") as fh:
        values["style"] = fh.read().rstrip()
    with open(pl.path("site", "app.js"), encoding="utf-8") as fh:
        values["script"] = fh.read().rstrip()
    with open(pl.path("site", "template.html"), encoding="utf-8") as fh:
        page = fh.read()
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], page)

    dist = pl.path("dist")
    os.makedirs(os.path.join(dist, "img"), exist_ok=True)
    for old in os.listdir(os.path.join(dist, "img")):
        if old not in used_images:
            os.remove(os.path.join(dist, "img", old))
    for name in sorted(used_images):
        shutil.copyfile(pl.path("build", "img", name), os.path.join(dist, "img", name))
    with open(os.path.join(dist, "artifact.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    with open(os.path.join(dist, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(SKELETON + page + "</body></html>\n")

    missing = sorted({r for p in phases for s in p["steps"] for r in s["refs"] if r not in data})
    print(f"Built dist/index.html: {len(phases)} phases, {rows} rows, {len(used_images)} picture files, {len(page) // 1024} KB of HTML")
    if missing:
        print(f"{len(missing)} referenced steps have no extracted pictures (run tools/extract_manual.py with the PDFs in manuals/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
