#!/usr/bin/env python3
"""Validate the plan. Needs only PyYAML, not the PDFs, so it runs in CI on every pull request.

Structure checks:
  * every row has a unique id, a known kind, text, and well-formed refs, notes, when/unless
  * no ref points at a step that does not exist

Coverage checks, repeated for every combination of the options in plan/options.yaml:
  * every INDX manual step is referenced by exactly one visible row
    (a step whose only row is an optional row hidden by an option counts as covered)
  * with Gen 2 on, every Gen 2 step is referenced by exactly one visible row or listed in
    plan/gen2-unused.yaml; with Gen 2 off, no visible row references a Gen 2 step
"""
from __future__ import annotations

import collections
import itertools
import sys

import planlib as pl


def main() -> int:
    manuals = pl.load_manuals()
    phases = pl.load_phases()
    options = pl.load_options()
    option_ids = [o["id"] for o in options]
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    all_rows: list[dict] = []
    kinds: collections.Counter[str] = collections.Counter()

    if len(set(option_ids)) != len(option_ids):
        errors.append("plan/options.yaml: option ids must be unique")
    for o in options:
        for key in ("id", "label", "text"):
            if not o.get(key):
                errors.append(f"plan/options.yaml: option {o.get('id')!r} is missing '{key}'")
        if not isinstance(o.get("default"), bool):
            errors.append(f"plan/options.yaml: option {o.get('id')!r} needs default: true or false")

    def check_conditions(where: str, item: dict) -> None:
        for key in ("when", "unless"):
            value = item.get(key)
            if value is None:
                continue
            if not isinstance(value, list) or not value:
                errors.append(f"{where}: {key} must be a non-empty list of option ids")
                continue
            for o in value:
                if o not in option_ids:
                    errors.append(f"{where}: {key} names {o!r}, which is not an option in plan/options.yaml")

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
            sid = s.get("id")
            if not sid:
                errors.append(f"{f}: a row has no id")
                continue
            where = f"{f}: {sid}"
            if sid in seen_ids:
                errors.append(f"{where}: row id is already used in {seen_ids[sid]}")
            seen_ids[sid] = f
            if s.get("kind") not in pl.KINDS:
                errors.append(f"{where}: kind {s.get('kind')!r} is not one of {', '.join(pl.KINDS)}")
            kinds[s.get("kind")] += 1
            if not isinstance(s.get("text"), str) or not s["text"].strip():
                errors.append(f"{where}: text is missing")
            check_conditions(where, s)
            if not isinstance(s.get("refs"), list):
                errors.append(f"{where}: refs must be a list (use [] for none)")
                s["refs"] = []
            for r in s["refs"]:
                try:
                    key, ch, n = pl.manual_for_ref(str(r), manuals)
                except ValueError as e:
                    errors.append(f"{where}: {e}")
                    continue
                if n < 1 or n > manuals[key]["chapters"].get(ch, 0):
                    errors.append(f"{where}: {r} is not a step of the {manuals[key]['label']} manual")
                if key == "gen2" and "gen2" not in (s.get("when") or []):
                    errors.append(f"{where}: references Gen 2 step {r} but is not marked when: [gen2]")
            for note in s.get("notes") or []:
                if note.get("type") not in pl.NOTE_TYPES:
                    errors.append(f"{where}: note type {note.get('type')!r} is not one of {', '.join(pl.NOTE_TYPES)}")
                if not note.get("by") or not note.get("text"):
                    errors.append(f"{where}: every note needs 'by' and 'text'")
                check_conditions(where + " (note)", note)
            all_rows.append(s)

    unused: set[str] = set()
    for entry in pl.load_yaml("plan", "gen2-unused.yaml"):
        if not entry.get("reason"):
            errors.append("plan/gen2-unused.yaml: every entry needs a reason")
        for spec in entry["steps"]:
            try:
                unused.update(pl.expand_range(spec))
            except ValueError as e:
                errors.append(f"plan/gen2-unused.yaml: {e}")
    indx = pl.all_steps(manuals, "indx")
    gen2 = pl.all_steps(manuals, "gen2")
    for r in sorted(unused - set(gen2)):
        errors.append(f"plan/gen2-unused.yaml lists {r}, which is not a Gen 2 step")

    combos = 0
    coverage_errors: dict[str, list[str]] = {}
    row_range = [10 ** 9, 0]
    for bits in itertools.product([False, True], repeat=len(option_ids)):
        combos += 1
        on = {o for o, b in zip(option_ids, bits) if b}
        name = " + ".join(sorted(on)) or "no options"
        shown = [s for s in all_rows if pl.visible(s, on)]
        hidden_optional = {r for s in all_rows if not pl.visible(s, on) and s.get("kind") == "opt" for r in s["refs"]}
        row_range = [min(row_range[0], len(shown)), max(row_range[1], len(shown))]
        used: collections.Counter[str] = collections.Counter(r for s in shown for r in s["refs"])
        problems = []
        for r, n in used.items():
            if n > 1:
                problems.append(f"{r} is referenced by {n} visible rows")
        missing = [r for r in indx if r not in used and r not in hidden_optional]
        if missing:
            problems.append("INDX steps with no visible row: " + ", ".join(missing))
        if "gen2" in on:
            for r in gen2:
                if r in used and r in unused:
                    problems.append(f"{r} is used by a row and also listed in plan/gen2-unused.yaml")
                if r not in used and r not in unused:
                    problems.append(f"Gen 2 step {r} is neither used by a visible row nor listed in plan/gen2-unused.yaml")
        for prob in problems:
            coverage_errors.setdefault(prob, []).append(name)

    for prob, names in coverage_errors.items():
        scope = "every option combination" if len(names) == combos else f"{len(names)} of {combos} combinations, e.g. [{names[0]}]"
        errors.append(f"{prob}  ({scope})")

    print(f"{len(phases)} phases, {len(all_rows)} rows in the files  ({', '.join(f'{k}: {v}' for k, v in sorted(kinds.items()))})")
    print(f"{len(option_ids)} options, {combos} combinations checked; a build shows between {row_range[0]} and {row_range[1]} rows")
    print(f"INDX steps: {len(indx)}.  Gen 2 steps: {len(gen2)}, of which {len(unused)} are listed as deliberately unused")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
