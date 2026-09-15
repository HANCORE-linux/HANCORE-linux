# Current profile workflow

Approved for commit and publication on 2026-09-15, after the final review of
neutral project titles and orange archive titles. The root `README.md` is the
public GitHub profile; `THEMES.md` and `ACKNOWLEDGEMENTS.md` open separately.
This is native GitHub Markdown, not a website.

## Source and export

Edit `folio/README.md` outside its generated regions and use the generators
for cards, labels and archive content. The source thank-you page is
`folio/ACKNOWLEDGEMENTS.md`. Images stay in `folio/assets/` and
`folio/collection/assets/`. The exporter rebases image paths without changing
the approved images, layout or independent repository links.

```bash
python scripts/build_folio.py
python scripts/render_folio.py
python scripts/build_register_study.py --render
python scripts/check_folio.py
python scripts/build_register_study.py --check
python scripts/export_profile.py --write
python scripts/export_profile.py --check
```

`export_profile.py --write` updates only the three root Markdown files. It
does not commit, push, change GitHub account settings or refresh source data.
Commit and push only after explicit approval. Do not edit the generated root
pages directly; the read-only export check detects drift from the folio.

Requirements: Python 3.11+, ImageMagick, librsvg (`rsvg-convert`) and
Fontconfig. Bundled, unmodified fonts carry their SIL OFL notices. A normal
image build is offline and validates original sources by hash. Star counts
and rankings are dated snapshots, not live counters; palettes come from the
actual theme color00–07 configurations.

## Local preview

Only if the existing preview has stopped:

```bash
python scripts/serve_folio.py --port 8767
```

Open http://127.0.0.1:8767/. The implementation session uses the transient
user service `hancore-profile-folio-20260915.service`; refresh after builds.
Do not start the older services on 8765/8766.

The renderer uses GitHub's Markdown API and caches exact-content responses.
Only public-facing Markdown is sent; preview HTML, caches, screenshots and
backups stay local and ignored by Git. The surrounding profile frame,
theme/font controls and proposed pins are preview-only. Private source paths
and `.git` are not served. This publication does not change the public avatar,
account settings or pinned repositories.

With Node 22+ and Chromium, optional runtime checks cover desktop/mobile
wrapping, image loading, dark/light variants, independent project links,
connection seams and archive/acknowledgements keyboard navigation:

```bash
node scripts/review_folio.mjs
```

## Maintained and historical files

- `folio/`: editable Markdown, SVG compositions, exported PNGs, bundled fonts,
  original screenshots and provenance manifests.
- `folio/collection/`: all 27 theme-card exports and their verified sources.
- `data/`: theme catalogue and earlier source metadata.
- `scripts/`: generators, root exporter and local preview tools.
- `assets/`: original sources still used by the build, plus earlier studies.
- `concept/` and `folio/studies/`: historical comparisons, not the profile.
- `.review/`: ignored local backups, render caches and browser evidence.

The older `build_profile.py` / `export_assets.sh` pipeline describes an earlier
design and must not be used to publish the current profile. Shared rendering
and server helpers remain in use. Detailed current design notes are in
[folio/DIRECTION.md](../folio/DIRECTION.md) and the
[collection notes](../folio/collection/DIRECTION.md). Asset and tooling rights
are preserved in [Asset notices](ASSET-NOTICES.md).
