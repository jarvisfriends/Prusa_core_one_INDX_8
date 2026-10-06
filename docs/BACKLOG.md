# Backlog

What is left, most useful first. Each item says what "done" looks like. Open questions
about the printer itself are in the README under "Where we left off"; this file is the
work that can be done at a keyboard.

Last updated 2026-10-06.

## A. Needs a person and a printer

These cannot be closed by reading. Listed here so they are not forgotten.

1. **Our own build choices**: gantry alignment or not, dryer box filament path, which
   camera. Record the decision and the reason in the README.
2. **LED panel cable** (`#p7s`): find where it runs and which ties hold it. Rewrite the row
   with real positions and delete its `unverified` note.
3. **Hinge-base orientation** (`#p11e`): one photo or one sentence from a finished lid.
4. **Dock fan cable ties** (`#p7p`): can they still be reached in Phase 11 with the right
   panel on? If yes, the tighten-and-trim could wait until the fan is plugged in.
5. **Dock fan before belt tension?** (`#p11b`): if the dock fan can be fitted before the
   belts are tensioned in Phase 6, the slacken-and-retension in Phase 11 goes away.
6. **INDX firmware with Gen 2** (`#p13c`, `#p13d`, `#p13dg`): what the model list shows,
   what the belt or edition setting is called, whether the wizard asks for belt tuning.
7. **Left panel, three rivets** (`#g4k`): which three holes.
8. **Build it** and feed every correction back.

## B. Plan content, doable now

1. **"Why here" notes on moved rows.** Rows of kind `moved` without a `why` note:
   `p1a`, `p1c`, `p1e`, `p4b`, `p4c`, `p4d`, `p7o`, `p7p`, `p10j`. Either add one
   line each or state the reason once in the phase intro and say so in `check.py`'s rule
   (see C2). Done when every moved row explains itself or its phase intro does.
2. **Duplicate wording inside a row.** The review found rows whose text and a note say the
   same thing: `p1c` (dock calibration resets the screws), `p1d` (IPA), `g4h`, `p5mg`
   (nine notes). Trim so each fact appears once per row. Keep the attribution.
3. **Gen 2 serial labels** (`#p12b`, `#p12b2`): both manuals say "above the original
   label". Merge into one sentence that covers both labels, or keep as is with the note.
4. **`p0b`**: the tool list says what came with the printer; the manual lists flush cutters
   as optional (step 5.1). Reword once someone confirms what a factory-assembled printer
   ships with.
5. **Second source for single-report notes.** Notes that rest on one comment are worded
   "one builder". When new comments appear on those steps, upgrade or drop them. A list can
   be made with `grep -n "One builder\|one builder" plan/*.yaml`.
6. **Prints list** (`plan/prints.yaml`): two models are "named by builders, not checked".
   Read their Printables pages and give a real verdict, or remove them.
7. **4-tool kit.** The plan is 8-tool only. A `tools4` option would need the 4-tool
   branches of steps 4.4x to 4.6x and 5.2x to 5.9x written out. Large; only if a friend
   has the 4-tool kit.

## C. Tooling

1. **Page tests.** There are none. Add Playwright tests (Python or Node) that build the
   page and check, for the default options and at least `none` and `gen2,dryer`:
   - no console errors, no horizontal scroll at 400 px and 1200 px;
   - ticking a row updates the count and survives a reload (localStorage);
   - toggling an option hides and shows the right rows and updates the total
     (compare with `len(visible rows)` from `planlib`);
   - the camera choice is exclusive;
   - the transfer code round-trips (copy, clear, load);
   - the picture viewer opens, steps and closes with the keyboard.
   Wire them into `.github/workflows/check.yml`. Done when CI runs them on pull requests.
2. **Stricter `check.py`.** Cheap rules that would have caught review findings:
   - every `moved` row has a `why` note (or its phase is exempted explicitly);
   - a note's `when` / `unless` does not merely repeat its row's;
   - "Phase N" in a row or note refers to an existing phase, and warn when it names the
     row's own phase or an earlier one with "later" wording (heuristic, warning only);
   - `by:` is never empty and `unverified` notes are listed in the output so the README's
     list can be kept in step;
   - every `#rowid` mentioned in `README.md` and `docs/` exists.
3. **Link check.** A script (not in CI by default) that requests every external link in
   `plan/` and reports dead ones. Skip help.prusa3d.com paths that robots.txt disallows.
4. **Plain-text diff in pull requests.** A CI step that runs `tools/render_text.py` for
   the default options on the base and head commits and posts the diff, so reviewers read
   the change as build order, not as YAML.
5. **Picture weight.** `manuals/img` is 40 MB of JPEG strips at 800×600 per picture, and
   the page lazy-loads them. Measure real load on a phone over mobile data before changing
   anything. Options: WebP alongside JPEG, or smaller strips for the grid and full size
   only in the viewer.
6. **`requirements.txt` split**: `requirements.txt` for check and build (PyYAML only),
   `requirements-extract.txt` for the PDF tooling.

## D. Page

1. **Look at the real site on a phone and a desktop.** The theme was only ever seen with
   fallback fonts, in a sandbox that could not load Google Fonts. Check the display face
   at the phase numerals and the title, the sticky bar's height on a small phone, and the
   dark theme. Fix what is off.
2. **Print stylesheet.** Builders asked Prusa for a printable combined guide. A `@media
   print` sheet that drops the sticky bar and viewer, keeps pictures small and avoids
   breaking a row across pages would give them one from this page.
3. **Offline use.** A workshop often has poor signal. A service worker that caches the
   page and the pictures once would let the checklist work offline on GitHub Pages.
4. **"What changed since my last visit".** Rows are keyed by id, so the page could mark
   rows whose text changed since the reader's last visit (store a short hash per row).
   Useful once people are mid-build and the plan is still being corrected.
5. **Per-row notes.** Let the builder type a note on a row, kept in `localStorage` and
   included in the transfer code, with a button that formats ticked-and-noted rows as an
   issue report for this repo.
6. **Accessibility pass**: keyboard order through options, focus after "Next open row",
   contrast of the muted text on the mat in both themes, reduced motion.

## E. Housekeeping

1. A second, broken copy of the page exists as a claude.ai artifact (no pictures). The
   user can delete it from their artifact gallery. The original artifact still shows the
   plan as of 2026-10-05.
2. Decide whether to keep the wiki turned on. Nothing uses it.
3. Add a `LICENSE` for our own text and code, and keep the note that Prusa's pictures and
   step text are theirs. Ask the user which licence.
