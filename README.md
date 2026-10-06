# Prusa CORE One → INDX 8-tool + Gen 2: one build order

A single checklist for converting a stock Prusa CORE One to the INDX 8-tool toolchanger
and fitting the Gen 2 upgrade in the same build.

Prusa documents this job across two manuals and a companion article that tells you when to
jump between them. This repo merges all of it into one order, so that:

- nothing is fitted and then taken off again,
- the printer is powered only at the very start and the very end,
- the same tool stays in your hand for as long as possible,
- every row shows Prusa's own pictures and step text, so you never switch documents.

It also carries tips collected from the Prusa forum, each attributed to who reported it.

**This is a community plan, not Prusa's.** Where a picture or Prusa's text disagrees with a
row, trust Prusa. If something looks wrong, open an issue or a pull request.

## Build the page

You need Python 3.10+ and your own copies of the two Prusa PDFs.

```sh
pip install -r requirements.txt

# 1. Download the two PDFs into manuals/  (links in manuals/README.md)
# 2. Pull the pictures and step text out of them
python tools/extract_manual.py

# 3. Check the plan and build the page
python tools/check.py
python tools/build.py

# 4. Open dist/index.html
```

`build.py` also works without the PDFs: you get the full checklist, with a link to Prusa's
online guide where each picture set would be.

### Why the pictures are not in the repo

The photos and the step text are Prusa Research's. Everyone who builds this has the manuals
anyway, so the repo holds only the plan and the tooling, and `extract_manual.py` copies the
embedded JPEGs straight out of your PDFs. No screenshots, no re-hosting. `manuals/*.pdf`,
`build/` and `dist/` are git-ignored.

## Layout

| Path | What it is |
|---|---|
| `plan/00-prepare.yaml` … `plan/13-preflight.yaml` | The build, one file per phase, in order. This is what most pull requests touch. |
| `plan/intro.yaml` | Page title, summary of what the order changes, assumptions, legend. |
| `plan/prints.yaml` | Helper prints to make before teardown, with a verdict on each. |
| `plan/hardware.yaml` | Table of removed hardware that is needed again. |
| `plan/gen2-unused.yaml` | Gen 2 guide steps a combined build skips, and why. |
| `plan/sources.yaml` | Footer: sources and credits. |
| `manuals/manuals.yaml` | The two manuals: links, PDF file patterns, step counts per chapter. |
| `site/template.html`, `site/style.css`, `site/app.js` | Page shell, styles, behaviour (ticks, picture viewer). |
| `tools/check.py` | Validates the plan. Runs in CI on every pull request. |
| `tools/extract_manual.py` | PDFs → `build/manual/*.json` and `build/img/*.jpg`. |
| `tools/build.py` | Everything → `dist/index.html`. |

## Editing the plan

A row looks like this:

```yaml
  - id: p5i
    refs: ["3.11", "3.13"]
    kind: asis
    tools: ["2.5 mm"]
    text: >-
      Rear spacer.
      Loosen the two `M3x18` in the rear trapezoidal nut while holding the old spacer.
    notes:
      - type: tip
        by: "Skirfir, forum"
        text: "One builder refitted the old spacer by mistake."
```

- **`refs`** are the manual steps the row covers: `"3.11"` is INDX chapter 3 step 11,
  `"G3.4"` is Gen 2 chapter 3 step 4. The page shows those steps' pictures and text under the row.
- **`kind`** is one of `asis` (manual order kept), `moved` (same step, different moment),
  `gen2` (from the Gen 2 guide or Prusa's companion article), `added` (not in either manual),
  `opt` (only if it applies), `skip` (deliberately not done).
- **`notes`** have a `type` of `why` (reason for a move), `tip` (community experience) or
  `warn`. Always say who it comes from in `by`.
- Text may use `` `code` `` for part and screw names and `[label](https://…)` for links.
- Long text is written one sentence per line under `>-`, so changing a sentence is a one-line diff.
- **Never rename or reuse a row `id`.** Saved ticks are stored by id.
- To reorder, move the row. To move a row to another phase, move it to that file.

Then run `python tools/check.py`. It fails if:

- an INDX manual step is not covered by exactly one row,
- a Gen 2 step is neither used by a row nor listed in `plan/gen2-unused.yaml`,
- a ref points at a step that does not exist, an id repeats, or a field is malformed.

That check is what lets a reviewer trust that a reshuffle did not drop a step. It cannot
tell whether a new order is physically sensible: say in the pull request why a move is safe,
ideally with the manual step that shows it.

## When Prusa revises a manual

Download the new PDF, run `extract_manual.py` (it warns if the step count changed), update
the chapter counts in `manuals/manuals.yaml`, then fix `refs` until `check.py` passes.

## Scope and assumptions

- Original CORE One, never upgraded, no MMU3. The Gen 2 guide is written for the CORE One+;
  forum builders report doing Gen 2 and INDX together on an original CORE One, but Prusa's
  guide does not state that combination.
- 8-tool kit. The 4-tool branches of the manual are not written out.
- Manual versions: INDX conversion 1.00 (PDF of 2026-10-01), Gen 2 upgrade (PDF of 2026-09-25).

## Sources

See `plan/sources.yaml`. Manuals and the companion article are by Prusa Research; tips are
credited to the forum members who posted them.
