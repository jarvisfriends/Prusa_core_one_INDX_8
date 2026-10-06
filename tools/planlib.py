"""Shared loaders for the plan data. No third-party imports beyond PyYAML."""
from __future__ import annotations

import glob
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ("asis", "moved", "gen2", "added", "opt", "skip")
NOTE_TYPES = ("why", "tip", "warn")
REF_RE = re.compile(r"^(G?)(\d+)\.(\d+)$")


def path(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def load_yaml(*parts: str):
    with open(path(*parts), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_manuals() -> dict:
    """manuals/manuals.yaml, keyed by manual id ('indx', 'gen2')."""
    return load_yaml("manuals", "manuals.yaml")


def load_phases() -> list[dict]:
    """plan/NN-*.yaml in file-name order."""
    files = sorted(glob.glob(path("plan", "[0-9][0-9]-*.yaml")))
    phases = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            p = yaml.safe_load(fh)
        p["_file"] = os.path.relpath(f, ROOT)
        phases.append(p)
    return phases


def load_options() -> list[dict]:
    """plan/options.yaml: the choices a builder ticks at the top of the page."""
    return load_yaml("plan", "options.yaml")["options"]


def visible(item: dict, on: set) -> bool:
    """A row or note shows if every `when` option is on and no `unless` option is on."""
    return all(o in on for o in item.get("when") or []) and not any(o in on for o in item.get("unless") or [])


def manual_for_ref(ref: str, manuals: dict) -> tuple[str, int, int]:
    """'G3.4' -> ('gen2', 3, 4); '3.4' -> ('indx', 3, 4)."""
    m = REF_RE.match(ref)
    if not m:
        raise ValueError(f"bad ref {ref!r}: expected like '3.17' or 'G3.4'")
    for key, man in manuals.items():
        if man["prefix"] == m.group(1):
            return key, int(m.group(2)), int(m.group(3))
    raise ValueError(f"no manual with prefix {m.group(1)!r} for ref {ref!r}")


def all_steps(manuals: dict, key: str) -> list[str]:
    man = manuals[key]
    return [f"{man['prefix']}{ch}.{n}" for ch, count in man["chapters"].items() for n in range(1, count + 1)]


def expand_range(spec: str) -> list[str]:
    """'G4.21-G4.31' -> ['G4.21', ..., 'G4.31']; 'G4.33' -> ['G4.33']."""
    if "-" not in spec:
        return [spec]
    a, b = spec.split("-")
    ma, mb = REF_RE.match(a), REF_RE.match(b)
    if not ma or not mb or ma.group(1) != mb.group(1) or ma.group(2) != mb.group(2):
        raise ValueError(f"bad range {spec!r}: both ends must be in the same manual and chapter")
    return [f"{ma.group(1)}{ma.group(2)}.{n}" for n in range(int(ma.group(3)), int(mb.group(3)) + 1)]
