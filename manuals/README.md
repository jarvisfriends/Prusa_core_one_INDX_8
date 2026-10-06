# Manuals

This folder holds what the build plan shows from Prusa's two manuals.

| Path | What it is |
|---|---|
| `manuals.yaml` | The two manuals: links, how many steps each chapter has, and each step's id on help.prusa3d.com. |
| `img/` | One JPEG per manual step: that step's pictures side by side, 800×600 each. |
| `steps/indx.json`, `steps/gen2.json` | Each step's title and colour-keyed text. |
| `PICTURES.md` | Generated list of every picture file with a link to its step on Prusa's site. |

The pictures and the step text are Prusa Research's. They were copied out of the PDF
manuals by `tools/extract_manual.py` (the JPEGs embedded in the PDF, re-saved side by side;
nothing is screenshotted) and are here so the checklist can show them beside each row.
Every step on the page links back to that step on help.prusa3d.com.

The PDFs themselves are not in the repo (`manuals/*.pdf` is git-ignored).

## When Prusa revises a manual

1. Download the new PDF into this folder. File names only need to contain
   `indx-conversion-kit` or `gen-2-upgrade`; a manual split into `...-pages-1.pdf`,
   `...-pages-2.pdf` works too.

   | Manual | PDF download on |
   |---|---|
   | Prusa INDX Conversion kit for the Prusa CORE One/+ | https://help.prusa3d.com/manual/prusa-indx-conversion-kit-for-the-prusa-core-one_2432 |
   | Prusa CORE One+ to (Gen 2) upgrade | https://help.prusa3d.com/manual/prusa-core-one-to-gen-2-upgrade_2435/core-one-plus |

2. `pip install pymupdf pillow pyyaml`, then `python tools/extract_manual.py`.
   It rewrites `img/`, `steps/` and `PICTURES.md` and warns if a step count changed.
3. If steps were added, removed or moved, update `chapters` and `step_ids` in
   `manuals.yaml` and fix the `refs` in `plan/` until `python tools/check.py` passes.

## Step ids and reader comments

Each step of the online manual has a numeric id. A step's page is its chapter URL plus
`#<id>`, for example
<https://help.prusa3d.com/guide/3-z-axis-upgrade_1096239#1099399> for INDX 3.15.
`manuals.yaml` lists the ids in step order under `step_ids`. They were read on 2026-10-05
from the table of contents embedded in any chapter page of the online guide.

The comments under a step are public. On 2026-10-05 they could be read, from a browser
that has the guide open, at

```
https://help.prusa3d.com//edge/comments?lng=en&page=1&parent=<step id>&per_page=100&status=approve
```

which returns JSON with each comment's author, date, text and replies. That is how the
notes credited to "comment on INDX 4.10" and the like were collected. The comments
themselves are not stored in this repo; the notes retell them in our own words and name
who said what. When you re-read comments for a step, look for new replies from Prusa staff
first: several open questions in the README are waiting for one.
