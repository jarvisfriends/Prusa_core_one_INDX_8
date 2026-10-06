# Manuals

Put Prusa's PDFs here. They are ignored by git on purpose: the pictures and step text
belong to Prusa Research, so each builder downloads their own copy and the build pulls
the pictures straight out of it. Nothing is screenshotted.

| Manual | Download PDF from |
|---|---|
| Prusa INDX Conversion kit for the Prusa CORE One/+ | https://help.prusa3d.com/manual/prusa-indx-conversion-kit-for-the-prusa-core-one_2432 |
| Prusa CORE One+ to (Gen 2) upgrade | https://help.prusa3d.com/manual/prusa-core-one-to-gen-2-upgrade_2435/core-one-plus |

File names do not matter as long as they still contain `indx-conversion-kit` and
`gen-2-upgrade`. A manual split into several PDFs (`...-pages-1.pdf`, `...-pages-2.pdf`)
works too.

If Prusa revises a manual and step numbers move, update the step counts in
`manuals.yaml` and fix the `refs` in `plan/` until `python tools/check.py` passes.
