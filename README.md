# Prusa CORE One → INDX 8-tool + Gen 2: one build order

A single checklist for converting a stock Prusa CORE One to the INDX 8-tool toolchanger,
with the Gen 2 upgrade and other add-ons merged in when you pick them.

**Open the checklist: <https://jarvisfriends.github.io/Prusa_core_one_INDX_8/>**

Prusa documents this job across two manuals and a companion article that tells you when to
jump between them. This repo merges all of it into one order, so that:

- nothing is fitted and then taken off again,
- the printer is powered only at the very start and the very end,
- the same tool stays in your hand for as long as possible,
- every row shows Prusa's own pictures and step text, so you never switch documents,
- what builders wrote in the comments under each manual step is folded in as notes,
- choices at the top of the page (Gen 2, dryer boxes instead of spool holders, Buddy3D or
  Raspberry Pi camera, larger waste bucket, printed light mount, leaving the gantry
  alignment alone) add, change or remove rows.

**This is a community plan, not Prusa's, and nobody here has built it end to end yet.**
Where a picture or Prusa's text disagrees with a row, trust Prusa, unless the row says it
follows an option or a Gen 2 branch. If something looks wrong, open an issue and quote the
row's code (for example `#p6fg`; every row shows its code at the right).

The page remembers your ticks and choices in the browser you use, so you can close it and
come back days later. "Move to another device" on the page turns them into a code you can
paste into the page on your phone or another computer.

---

## Where we left off (read this first when you come back)

Last worked on 2026-10-05. State of things:

- The plan covers all 290 steps of the INDX manual and the 60 Gen 2 steps a combined build
  uses. `tools/check.py` proves that for every combination of options.
- About 1,200 reader comments on Prusa's two online manuals were read on 2026-10-05 and
  turned into notes and several order changes. Gen 2 comments were read only for the steps
  this build uses (chapter 3 up to step 40, chapter 4 steps 1 to 21 and 32 onward).
- Nothing below has been checked on a real printer by us. The first of us to build should
  tick rows on the page, write down every row that was wrong or unclear, and fix it here.
- `tools/check.py` passes and the page builds. The last round of changes has **not** had
  its review pass (next step 1).

### Next steps

1. **Review pass on the reordered rows. Not done yet.** The 2026-10-05 session changed the
   order in about fifteen places (table under "Out of order on purpose") and added about
   190 notes from comments. An independent read-through of every phase, checking each row
   against the manual text in `manuals/steps/` and each note against the comment it cites,
   was started and did not finish. Do this before anyone builds from the page. Things to
   look for: a row that needs something an earlier row has not done yet, a note that still
   describes the old order, a count or a name that does not match the comment.
2. Turn on GitHub Pages (Settings → Pages → Source: GitHub Actions) and check the site
   loads at the address at the top of this file, with fonts and pictures.
3. Answer the questions under "Decide before you start" for our own build: gantry
   alignment or not, dryer box filament path, which camera.
4. Find where the LED panel cable runs on a real printer and fix row `#p7s`.
5. Read the rest of the Gen 2 manual's comments (chapter 3 steps 41 to 64 are skipped by
   this build, but chapter 4 steps 22 to 31 were not read) and the comments on Prusa's
   companion article.
6. Look for a reply from Prusa on: gantry alignment, tight pulleys and short shafts,
   expansion joint direction, tooth counts on 1.5GT belts, the INDX firmware's Gen 2 setting.
7. Build it, tick rows on the page, and send every correction back here as a pull request.

### Decide before you start

| Question | What we know | Where |
|---|---|---|
| Run the gantry aligner and rail re-alignment (INDX 4.4 to 4.8) on a printer that was square? | Prusa's manual does it. Six builders say it left a good printer worse (X-axis or dock calibration failing, one stripped the build back to this step). One skipped it and reports good prints. Prusa has not answered. The page has a choice for it; default is to follow the manual. | `#p6c`, `#p6cx` |
| Gen 2 parts on an original (non-plus) CORE One | Prusa's Gen 2 guide is written for the CORE One+. Builders report it works, but about twelve have a motor shaft roughly 3 mm shorter than pictured and about seventeen found the new pulleys very tight (one ruined a motor). Burrs from the old set screws are one known cause. No reply from Prusa. | `#g3d`, `#g3k` |
| Dryer boxes instead of spool holders | Our own idea plus two commenters who said they would skip the spool holders. Nobody has reported a finished printer without them. How a tube is held at the sensor inlet (a bare hole on the underside) is unsolved. | `#p0j`, `#p10x`, `#p12dd` |
| Power up once before the side panels are trapped? | With puck holders on, a side panel only comes off by undoing their nuts. One builder found an X/Y fault at the first self-test and had to. We kept "power it twice" because nobody has said how far the INDX wizard runs without dock and tools. | `#p10a` |
| Larger waste bucket on an 8-tool machine | Not confirmed how it sits beside the right-hand spool holders. | `#p0g` |
| Raspberry Pi camera | No report of any Pi camera mount on an INDX printer. Corner position, ribbon route and heat (Camera Module 3 is rated to 50 °C) are all guesses. | `#p0k`, `#p11jp` |

### Things in the plan that nobody has confirmed

These are rows where we chose something from comments, arithmetic or inference. Each needs
a builder to confirm or correct it.

- **LED panel cable slack** (`#p7s`). Five builders found the cable too short at INDX 5.89.
  We added a row to free slack before any zip tie is tightened, but we do not know where the
  cable runs, which ties hold it or how many centimetres are needed.
- **Tooth counts on 1.5GT belts** (`#p6fg`, `#p6gg`). The manual's 4 to 5 and 6 to 7 teeth
  are for 2 mm pitch. We use 6 to 7 and 8 to 9, from six builders' arithmetic. Not from Prusa.
- **Belt tensioning screws left out during the Gen 2 belt routing** (`#g3r`, `#g3t`).
  Prusa's article fits them at Gen 2 3.32 and 3.36. About fifteen builders had to take them
  out again to get the belt ends into the head plate, so we leave them out until INDX 4.13.
  Unknown: whether an idler stays in its rails without the screw while you route the belt.
- **Offset sensor sticker on the bench** (`#p11n`, now in Phase 5). Five builders prefer it.
  We do not know why Prusa fits it last; possibly only to keep it clean.
- **Dock fan cable routed before the sensors, ties closed in two visits** (`#p7n` to `#p7p`,
  `#p9e`). Three builders did the routing early. The "just closed, final pull in Phase 9"
  detail is ours.
- **X and Y motor cables plugged back in during Phase 7** (`#g4j`), before the box's zip
  ties are closed. Prusa's article does it after the heatbed alignment.
- **Expansion joints**: groove facing out as the guide says, though five builders say the
  aligner then pushes joints off their screws and two turned them inward (`#g4e`). Screw
  first or joint first is also disputed (`#g4b`). No ruling from Prusa on either.
- **INDX firmware on Gen 2 hardware** (`#p13c`, `#p13dg`, `#p13f`). One builder was offered
  only COREONEGEN2 in the model list; another was never asked for belt tuning. What the
  edition or belt setting is called in the INDX firmware is unknown.
- **Left side panel with three rivets** (`#g4k`). We could not see the picture in Prusa's
  article that shows which three holes.
- **Right-hand top puck holders before the tilt** (`#p10i`, `#p10j`). One builder
  recommends it; nobody commented on those two steps' photos.
- **Puck-holder tool photos** (`#p10d`, `#p10e`). Five builders say the manual's photos at
  5.36 are wrong or swapped, one says they are right. Rows now say: sight the nuts through
  the holes and turn the tool over if they are off.
- **Hinge-base orientation** (`#p11e`). Not shown anywhere; six builders asked. Needs a
  photo from a finished lid.
- **Small magnets in the filament sensors** (`#p8c`). Screwed down as the photos show, or
  left with 0.5 mm of float as one early builder says? Unanswered.
- **Dock screws for calibration** (`#p13g`). Snug as the manual says, or one to two turns
  loose as two builders needed?
- **`M3x12` for the Head-cable-clip** (`#p7j`). Five builders swapped the `M3x10` for one.
  The kit has no socket-head `M3x12`, so it is bring-your-own.
- **Bed height and unload order** (`#p2c`, `#p2b`). 200 mm exactly; one builder's bed
  dropped further when unloading afterwards.
- **Helper prints**. Verdicts come from each model's description, not from printing them.
- **A nozzle tool's sensing area that got touched**. Two builders asked how to clean it;
  the only answer (soapy water, no IPA) is from another user.

### Confusing in Prusa's documents (it is not you)

- The INDX manual's photos show a CORE One+. The Gen 2 guide's photos show the Nextruder
  still fitted, and its heatbed chapter assumes the bed is still in the printer.
- INDX 5.17 says "return to the Prusa INDX Gen 2 article now" with nowhere to go. In this
  plan it is simply the next row.
- "Left" and "right" motor: the X motor is the left rear one, the Y motor the right rear
  one. INDX 2.19 and 4.32 describe the same corner from different sides.
- Bag and box names that do not match the kit:
  - "Tool Dock Fan bag" (5.59, 5.96): most kits have none. The two `M3x35` are in
    Fasteners 2/2 INDX; the offset sensor sticker is in the Electronics box.
  - Offset sensor "in the Filament Sensors box" (3.14): it is in the Electronics box. Its
    cable is the all-black one, part 25229-56, in the Cables bag.
  - "Pucks bag" (5.33): the pucks are in the Telescopic Spoolholder Set bags.
  - `3x12sT` "in Fasteners 1/2" (4.53, 4.62): found in Fasteners 2/2, not on its label.
    Both steps list two; you need one per side.
  - Nylon string (4.25): in the bag labelled Top Door Seal & Nylon String.
  - "Filament holder L/R" bags (4.41): labelled Filament Sensor Holder Left / Right. The
    8-tool kit has two identical Fasteners Tools INDX bags.
  - Springs "15×5" (5.84): the bag says Spring 0,8x5x15x10.
  - Gen 2 guide: `M3x14cT` and `M3x4cT` are the `M3x14bT` and `M3x4bT`; the `M3nN` at
    Gen 2 3.14 looks like a square nut in the picture.
- INDX 2.5: the picture shows the steel sheet going on; the instruction is to take it off.
- INDX 2.17: says lower opening; on most printers the sensor cable is in the upper one.
- INDX 3.26: the text leaves the thermistor cable out of the sleeve; the photos include it.
- INDX 4.6: the aligner tool covers the lowest gantry screw. The manual does not say so.
- INDX 4.10 and 4.11: tooth counts are for the old 2 mm belts.
- INDX 4.28: a photo shows a silver screw; use the black `3x8sT`.
- INDX 5.36 and 5.38: disputed photos of the puck-holder tool.
- INDX 5.67: "barely perceptible wiggle" cannot be judged; dock calibration resets it.
- INDX 6.11: belt tuning may not be offered by the wizard. INDX 6.20: the Y calibration of
  the nozzle cleaner no longer exists in current firmware.
- Gen 2 4.19: "move the offset sensor out of the way". Its screw is underneath.
- Gen 2 5.4 to 5.6: the Edition menu needs firmware 6.8.1 or newer.

### Out of order on purpose (and what is still awkward)

Where this plan departs from Prusa's order. Each row carries a "Why here" note.

| Change | Rows |
|---|---|
| Firmware download, kit inventory and helper prints before anything comes apart | Phase 0 |
| Nozzle cleaner, puck holders and the whole tool dock built at the bench first | Phase 1 |
| Old spool holder out early; right steel panel off at the end of teardown, not in chapter 5 | `#p3e`, `#p3q` |
| Gen 2: left panel and both transparent covers off straight after the door; X/Y motor cables unplugged while the box is open | `#p3s`, `#p3i2` |
| Lid, side handle and wiper fitted to parts on the bench | Phase 4 |
| Bed cable cover and all three of its nuts done the moment the bed is on the bench | `#p5e` |
| Rear bed stop swapped next to the rear spacer | `#p5j` |
| Gen 2: expansion joints swapped before the offset sensor goes on beside them | `#g4a`, `#g4b` |
| Offset sensor sticker applied on the bench | `#p11n` |
| Zip ties threaded through the electronics box before it fills with cables | `#p5p` |
| Nuts into the head plate before the belts; tensioning screws stay out until the plate is on, Gen 2 included | `#p6f`, `#g3r`, `#p6i` |
| LED panel cable slack freed early | `#p7s` |
| Gen 2: X/Y motor cables reconnected before the box's ties close | `#g4j` |
| Dock fan cable routed straight after the head cable, with the right side open | `#p7n` to `#p7p` |
| Electronics covers before the left side panel | `#g4k` |
| Right-hand top puck holders before the single tilt | `#p10i`, `#p10j` |
| Door sticker applied with the door flat on the bench | `#p12b` |

Still awkward, and worth improving once someone has built it:

- The belts are tensioned in Phase 6 and slackened again in Phase 11 to take two screws out
  of the right Belt-tensioner for the dock fan (`#p11b`). Could the dock fan go on before the
  belts are tensioned? Nobody has tried.
- With Gen 2 the offset sensor still has to be swung aside once, for the front right
  expansion joint (`#g4g`).
- The dock fan cable ties are closed in Phase 7 and pulled tight in Phase 9.
- First power-on comes after everything is closed (see "Decide before you start").

### Good to remember

- Row ids are permanent: saved ticks are stored by id. Ids `g4c`, `p6hg` and `p6ig` were
  retired on 2026-10-05; do not reuse them.
- Firmware: builders reported 6.9.0 failing tool offset calibration on a slightly dirty
  nozzle and 6.9.1 fixing it. Use the newest INDX firmware.
- The kit has no spares of: `M3x12cT`, expansion joint screws, `M3nS` (some kits), `M3x35`.
  Count before teardown, while support can still post parts and the printer still prints.
- To re-read Prusa's comments later, see `manuals/README.md`. Step ids are in
  `manuals/manuals.yaml`.
- The pictures are plain files in git (about 40 MB), not Git LFS: GitHub Pages cannot serve
  LFS files without extra steps, and nothing here is near GitHub's size limits.
- The same page is also published as a private claude.ai artifact. GitHub Pages is the copy
  to share.
- The repo's wiki is on but unused. Everything lives in this README and in the plan files.

---

## Build the page

You need Python 3.10+ and PyYAML. The manual pictures and text are already in the repo.

```sh
pip install pyyaml
python tools/check.py     # every manual step accounted for, for every mix of options
python tools/build.py     # writes dist/index.html and dist/img/
```

Open `dist/index.html` in a browser. Every push to `main` runs the same two commands and
publishes `dist/` to GitHub Pages (`.github/workflows/pages.yml`). That needs one setting,
once: repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.

## Layout

| Path | What it is |
|---|---|
| `plan/00-prepare.yaml` … `plan/13-preflight.yaml` | The build, one file per phase, in order. This is what most pull requests touch. |
| `plan/intro.yaml` | Page title, title block, summary of what the order changes, assumptions, legend. |
| `plan/options.yaml` | The "Your build" choices at the top of the page. |
| `plan/prints.yaml` | Helper prints to make before teardown, with a verdict on each. |
| `plan/hardware.yaml` | Table of removed hardware that is needed again. |
| `plan/gen2-unused.yaml` | Gen 2 guide steps a combined build skips, and why. |
| `plan/sources.yaml` | Footer: sources and credits. |
| `manuals/manuals.yaml` | The two manuals: links, step counts and step ids per chapter. |
| `manuals/img/`, `manuals/steps/` | Prusa's step pictures and step text, copied out of the PDF manuals. |
| `manuals/PICTURES.md` | Generated: every picture file with a link to its step on Prusa's site. |
| `site/template.html`, `site/style.css`, `site/app.js` | Page shell, theme, behaviour (ticks, choices, picture viewer). |
| `tools/check.py` | Validates the plan. Runs on every pull request. |
| `tools/build.py` | Everything → `dist/`. |
| `tools/extract_manual.py` | Prusa's PDFs → `manuals/img/` and `manuals/steps/`. Only needed when a manual is revised. |

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
        by: "langjai, comment on INDX 3.11"
        text: >-
          Prop the Z-carriage while the old spacer is out.
```

- **`refs`** are the manual steps the row covers: `"3.11"` is INDX chapter 3 step 11,
  `"G3.4"` is Gen 2 chapter 3 step 4. The page shows those steps' pictures and text under the row.
- **`kind`** is one of `asis` (manual order kept), `moved` (same step, different moment),
  `gen2` (from the Gen 2 guide or Prusa's companion article), `added` (not in either manual),
  `opt` (only if it applies), `skip` (deliberately not done).
- **`when`** and **`unless`** tie a row (or a single note) to the options in
  `plan/options.yaml`. `when: [gen2]` shows it only with Gen 2 picked; `unless: [dryer]` hides
  it when dryer boxes are picked. Where an option changes an instruction, write two rows with
  different ids, one `when` and one `unless`, both citing the same manual step.
- **`notes`** have a `type` of `why` (reason for a move), `tip` (builders' experience) or
  `warn`. Always say who it comes from in `by`: a name and the step they commented on, the
  manual, or `unverified` when it is our own guess. When builders disagree, say so.
- **`tools`** show as chips. A name containing `mm` gets the hex key mark, `T10` the Torx
  mark, `PH2` the cross, `Cutters` the cutter mark.
- Text may use `` `code` `` for part and screw names and `[label](https://…)` for links.
- Long text is written one sentence per line under `>-`, so changing a sentence is a one-line diff.
- **Never rename or reuse a row `id`.** Saved ticks are stored by id.
- To reorder, move the row. To move a row to another phase, move it to that file.

Then run `python tools/check.py`. For every combination of options it fails if:

- an INDX manual step is not covered by exactly one visible row
  (rows of kind `opt` that an option hides are exempt),
- with Gen 2 on, a Gen 2 step is neither used by a row nor listed in `plan/gen2-unused.yaml`,
- a ref points at a step that does not exist, an id repeats, or a field is malformed.

That check is what lets a reviewer trust that a reshuffle did not drop a step. It cannot
tell whether a new order is physically sensible: say in the pull request why a move is safe,
ideally with the manual step or the comment that shows it.

### Adding an option

Add it to `plan/options.yaml`, then mark the rows it adds with `when: [your-id]` and the rows
it replaces with `unless: [your-id]`. If it makes a manual step unnecessary, add a `skip` row
under `when` that cites the step and says why. Options that are alternatives (the two
cameras) share a `group`; the page then shows them as one pick-one question and `check.py`
never turns two of them on together.

## When Prusa revises a manual

Download the new PDF into `manuals/`, run `pip install pymupdf pillow` and
`python tools/extract_manual.py` (it warns if the step count changed), update the chapter
counts and step ids in `manuals/manuals.yaml`, then fix `refs` until `check.py` passes.
Details are in `manuals/README.md`.

## Scope and assumptions

- Original CORE One, never upgraded, no MMU3.
- 8-tool kit. The 4-tool branches of the manual are not written out.
- Manual versions: INDX conversion 1.00 (PDF of 2026-10-01), Gen 2 upgrade (PDF of 2026-09-25).

## Credits

The step pictures in `manuals/img/` and the step text in `manuals/steps/` are Prusa
Research's, from the two manuals below; they are reproduced here so the checklist can show
them beside each row, and every step on the page links back to its page on
help.prusa3d.com. `manuals/PICTURES.md` lists the source of every picture file. If Prusa
asks for them to be removed, delete those two folders: the page still builds and links to
Prusa's site instead.

- [Prusa INDX Conversion kit for the Prusa CORE One/+](https://help.prusa3d.com/manual/prusa-indx-conversion-kit-for-the-prusa-core-one_2432)
- [Prusa CORE One+ to (Gen 2) upgrade](https://help.prusa3d.com/manual/prusa-core-one-to-gen-2-upgrade_2435/core-one-plus)
- [Prusa: assembling the INDX with the Gen 2 upgrade](https://help.prusa3d.com/article/assemblling-the-prusa-indx-core-one-with-the-gen-2-upgrade_1147602)

Tips are credited on the page to the builders who posted them, in the manuals' comment
threads and on the Prusa forum. The rest of the sources are in `plan/sources.yaml`.
