#!/usr/bin/env python3
"""Print the build as plain text for one set of options, in order, as a builder would read it.

Meant for reviewing: read it top to bottom, or diff two option sets or two commits.

  python tools/render_text.py                     # the defaults from plan/options.yaml
  python tools/render_text.py --on gen2,dryer     # exactly these options on
  python tools/render_text.py --on none --manual  # no options, with Prusa's step text under each row
"""
from __future__ import annotations

import argparse
import sys
import textwrap

import planlib as pl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--on", help="comma-separated option ids to turn on, or 'none'. Default: the options' defaults.")
    ap.add_argument("--manual", action="store_true", help="also print Prusa's text for every step a row cites")
    ap.add_argument("--no-notes", action="store_true", help="leave the notes out")
    args = ap.parse_args()

    options = pl.load_options()
    known = {o["id"] for o in options}
    if args.on is None:
        on = {o["id"] for o in options if o["default"]}
    else:
        on = set() if args.on.strip() in ("", "none") else {x.strip() for x in args.on.split(",")}
    if on - known:
        print(f"unknown option(s): {', '.join(sorted(on - known))}. Known: {', '.join(sorted(known))}", file=sys.stderr)
        return 2
    groups: dict[str, list[str]] = {}
    for o in options:
        if o.get("group") and o["id"] in on:
            groups.setdefault(o["group"], []).append(o["id"])
    clash = [ids for ids in groups.values() if len(ids) > 1]
    if clash:
        print(f"these options are alternatives, pick one: {', '.join(clash[0])}", file=sys.stderr)
        return 2

    manuals = pl.load_manuals()
    data = pl.load_steps(manuals) if args.manual else {}

    def wrap(text: str, indent: str) -> str:
        return textwrap.fill(" ".join(text.split()), width=100, initial_indent=indent, subsequent_indent=indent)

    print(f"OPTIONS ON: {', '.join(sorted(on)) or 'none'}\n")
    rows = 0
    for n, p in enumerate(pl.load_phases()):
        print(f"{'=' * 100}\nPHASE {n}: {p['title']}   [{'POWER ON' if p['power'] == 'on' else 'unplugged'}; {p['where']}]")
        if p.get("note"):
            print(wrap(p["note"], "  "))
        print()
        for s in p["steps"]:
            if not pl.visible(s, on):
                continue
            rows += 1
            head = f"#{s['id']}  [{s['kind']}]"
            if s["refs"]:
                head += "  " + " ".join(s["refs"])
            if s.get("tools"):
                head += "   tools: " + ", ".join(s["tools"])
            print(head)
            print(wrap(s["text"], "    "))
            if not args.no_notes:
                for note in s.get("notes") or []:
                    if pl.visible(note, on):
                        print(wrap(f"{note['type'].upper()} ({note['by']}): {note['text']}", "      > "))
            if args.manual and s["kind"] != "skip":
                for r in s["refs"]:
                    step = data.get(r)
                    if step:
                        print(f"      | {r} {step['title']}")
                        for it in step["items"]:
                            print(wrap(it["t"].replace("**", ""), "      |   "))
            print()
    print(f"{rows} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
