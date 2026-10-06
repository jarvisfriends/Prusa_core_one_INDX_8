#!/usr/bin/env python3
"""Validate the plan. Needs only PyYAML, not the PDFs, so it runs in CI on every pull request.

Checks:
  * every row has a unique id, a known kind, text, and well-formed refs and notes
  * every INDX manual step is referenced by exactly one row
  * every Gen 2 step is either referenced by exactly one row or listed in plan/gen2-unused.yaml
  * no ref points at a step that does not exist
"""
from __future__ import annotations

import collections
import sys

import planlib as pl


def main() -> int:
    manuals = pl.load_manuals()
    phases = pl.load_phases()
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    used: collections.Counter[str] = collections.Counter()
    where: dict[str, str] = {}
    rows = 0
    kinds: collections.Counter[str] = collections.Counter()

    phase_ids = set()
    for p in phases:
        f = p["_file"]
        for key in ("id", "name", "title", "power", "where", "steps"):
            if key not in p:
                errors.append(f"{f}: phase is missing '{key}'")
        if p.get("id") in phase_ids:
            errors.append(f"{f}: duplicate phase id {p.get('id')}")
        phase_ids.add(p.get("id"))
        if p.get("power") not in ("on", "off"):
            errors.append(f"{f}: power must be \"on\" or \"off\" (quote it, YAML reads bare on/off as booleans)")
        for s in p.get("steps") or []:
            rows += 1
            sid = s.get("id")
            if not sid:
                errors.append(f"{f}: a row has no id")
                continue
            if sid in seen_ids:
                errors.append(f"{f}: row id {sid} is already used in {seen_ids[sid]}")
            seen_ids[sid] = f
            if s.get("kind") not in pl.KINDS:
                errors.append(f"{f}: {sid}: kind {s.get('kind')!r} is not one of {', '.join(pl.KINDS)}")
            kinds[s.get("kind")] += 1
            if not isinstance(s.get("text"), str) or not s["text"].strip():
                errors.append(f"{f}: {sid}: text is missing")
            if not isinstance(s.get("refs"), list):
                errors.append(f"{f}: {sid}: refs must be a list (use [] for none)")
                continue
            for r in s["refs"]:
                try:
                    key, ch, n = pl.manual_for_ref(str(r), manuals)
                except ValueError as e:
                    errors.append(f"{f}: {sid}: {e}")
                    continue
                if n < 1 or n > manuals[key]["chapters"].get(ch, 0):
                    errors.append(f"{f}: {sid}: {r} is not a step of the {manuals[key]['label']} manual")
                used[r] += 1
                where.setdefault(r, sid)
            for note in s.get("notes") or []:
                if note.get("type") not in pl.NOTE_TYPES:
                    errors.append(f"{f}: {sid}: note type {note.get('type')!r} is not one of {', '.join(pl.NOTE_TYPES)}")
                if not note.get("by") or not note.get("text"):
                    errors.append(f"{f}: {sid}: every note needs 'by' and 'text'")

    for r, n in used.items():
        if n > 1:
            errors.append(f"{r} is referenced by {n} rows; each manual step belongs to exactly one row")

    indx = pl.all_steps(manuals, "indx")
    missing = [r for r in indx if r not in used]
    if missing:
        errors.append("INDX steps not referenced by any row: " + ", ".join(missing))

    unused: set[str] = set()
    for entry in pl.load_yaml("plan", "gen2-unused.yaml"):
        if not entry.get("reason"):
            errors.append("plan/gen2-unused.yaml: every entry needs a reason")
        for spec in entry["steps"]:
            try:
                unused.update(pl.expand_range(spec))
            except ValueError as e:
                errors.append(f"plan/gen2-unused.yaml: {e}")
    gen2 = pl.all_steps(manuals, "gen2")
    for r in gen2:
        if r in used and r in unused:
            errors.append(f"{r} is used by row {where[r]} and also listed in plan/gen2-unused.yaml")
        if r not in used and r not in unused:
            errors.append(f"Gen 2 step {r} is neither used by a row nor listed in plan/gen2-unused.yaml")
    for r in sorted(unused - set(gen2)):
        errors.append(f"plan/gen2-unused.yaml lists {r}, which is not a Gen 2 step")

    gen2_used = sum(1 for r in gen2 if r in used)
    print(f"{len(phases)} phases, {rows} rows  ({', '.join(f'{k}: {v}' for k, v in sorted(kinds.items()))})")
    print(f"INDX steps covered: {len(indx) - len(missing)} of {len(indx)}")
    print(f"Gen 2 steps used: {gen2_used}, deliberately unused: {len(unused & set(gen2))}, of {len(gen2)}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
