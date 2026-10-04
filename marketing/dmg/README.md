# kurtz installer artwork

The installer uses a close, expressive black pug portrait inspired by the
owner's original branding sheet. The photograph is monochrome against Graphite;
the exact Ivory wordmark, Sora typography and two Electric Yellow rays carry
the kurtz identity. The claim remains “Good videos go further.”

`kurtz-pug-art.png` is the untouched built-in Imagegen output. Its exact prompt,
input roles and generation provenance are in `kurtz-art-prompt.txt`.
`Tools/marketing/build-kurtz-dmg.cjs` composes the checked-in vector wordmark,
Sora, label backgrounds, yellow arrow and rays over that image. `background.svg`
and `background@2x.png` are the reproducible 1536 × 1024 composition and Retina
Finder background.

The installation action occupies the quiet left half, facing the pug portrait.
Finder draws the real app icon, Applications link and their filenames; those
items are not baked into the artwork. The window is 768 × 512 points, with
112-point icons at **(128, 254)** and **(316, 254)**. Only `kurtz.app` and
`Applications` are visible. License/source records stay under `.licenses`; the
app also exposes its notices. The background lives inside `.background`.
Support items have explicit icon positions beyond the right edge of the initial
window, including Finder/system metadata. This prevents overlap with the design
when Finder shows hidden files. The layout writer verifies these saved positions.
Styling the volume does not modify the signed app.

Rebuild with the build-only environment containing `Tools/kurtz/dmg-requirements.txt`:

```sh
node Tools/marketing/build-kurtz-dmg.cjs
build/dmg-tools/bin/python Tools/kurtz/package-dmg.py \
  build/release/0.9.7/notarized/kurtz.app \
  --output build/release/0.9.7/installer-r3 --revision 3
```

This is packaging revision 3 of the same notarized 0.9.7 (9) application. The
packager requires a universal, Developer-ID-signed app with a stapled ticket for
production and refuses to overwrite an existing output. Published previous
installers keep their original filenames and checksums.

The current artwork preview is `background@2x.png`; the completed DMG was also
inspected in the actual Finder window with its native icons and filenames,
both with hidden files concealed and shown. Revision 3 is the published website download. The app binary remains
0.9.7 (9), without the newer local player fixes.

The previous curled-ribbon raster remains at `kurtz-background-art.png`; its
prompt and Finder capture are preserved in `archive-kurtz-r1/`. The older
`installer-preview.png` also remains as a historical capture for existing release
record links. Its complete composition remains in Git history and the original
DMG. Vela-era prompts and capture remain in `archive-vela/` as historical provenance.
