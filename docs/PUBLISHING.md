# Current profile workflow

Approved for commit and publication on 2026-09-15, after the final review of
neutral project titles and orange archive titles. The root `README.md` is the
public GitHub profile; `THEMES.md` and `ACKNOWLEDGEMENTS.md` open separately.
This is native GitHub Markdown, not a website.

## Source and export

Edit `folio/README.md` outside its generated regions and use the generators
for cards, labels and archive content. Edit acknowledgement names, roles and
links in `folio/acknowledgements.json`; `folio/ACKNOWLEDGEMENTS.md` is generated.
Images stay in `folio/assets/` and
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

The daily star-refresh workflow is the explicitly approved exception: once
published to `main`, it may commit and push verified star-only refreshes.

Requirements: Python 3.11+, ImageMagick, librsvg (`rsvg-convert`) and
Fontconfig. Bundled, unmodified fonts carry their SIL OFL notices. A normal
image build is offline and validates original sources by hash. Star counts
and rankings are dated snapshots, not live counters; palettes come from the
actual theme color00–07 configurations.

Small badge and Discord SVGs are embedded as vector geometry, never as SVG
`<image>` resources: Ubuntu 24.04's librsvg otherwise rasterizes them at low
resolution before enlarging them. Badges use bundled Liberation Sans Regular
with an isolated, checksum-verified Fontconfig environment, matching the
approved local font instead of depending on host fallbacks. Shadows, chamfers,
output dimensions and Markdown display sizes remain unchanged.
After building, run `python -m unittest discover -s tests -v`. The rendering
tests compare every shipped badge and both Discord icons with independently
rendered full-resolution vector sources. CI runs these checks before publishing.

Theme cards and the total-star badge are published as self-contained SVG images.
Only the badge lettering remains vector geometry until browser display; all
other card pixels (including Plex captions, palettes, screenshots and shadows)
retain the existing PNG rendering. Liberation Sans glyphs are outlined offline
with the existing librsvg/Cairo toolchain, so no font download or fallback is
needed. Embedded PNG backgrounds contain no badge lettering. Original PNGs stay
as regression references. Image dimensions, independent links, colors and font
weights do not change. Tests verify every card's unchanged background/caption
pixels and compare the outlines to the original badge at 1× and 2× display scale.

## Daily star refresh

`.github/workflows/profile-stars.yml` runs at 04:17 UTC each day (05:17 CET /
06:17 CEST), with a manual **Run workflow** option. It activates after the
workflow is published to the default branch. No local computer, cron job or
personal access token is needed.
Manual runs also exercise the full build when numbers are unchanged, but do not
publish those unchanged snapshots.

- Total: all public, non-fork repositories owned by `HANCORE-linux`, plus
  `omacom/omarchy-plugin-marketplace`. Deduplicate by repository ID. These are
  project stars, not unique people or exclusively account-owned stars.
- All 27 theme counts and the top-six selection use the same GitHub API
  snapshot. Ties sort by repository name; only themes above 30 stars qualify.
- Exact counts are rendered with static black/orange Shields badges, retaining
  the existing shadow and chamfer. The build preserves screenshots and palettes.
- When the ranking changes, existing hash-verified screenshots are reused.
  Only obsolete generated top-six exports are retired; originals remain cached.
- An unchanged snapshot causes no file changes and no commit, including no
  date-only commits. Dates in the README therefore describe the last changed
  snapshot; successful unchanged checks are visible in Actions history.
- All downloads must succeed and validate before source writes. A failed fetch,
  build or check prevents publication and leaves the last published state intact.
- Only the canonical repository's `main` can publish, using the Actions bot's
  noreply email. No PR trigger, persistent checkout credential or force push.
  Concurrent human pushes cause a safe non-fast-forward failure; retry manually
  or wait for the next daily run. Branch rules must permit this bot push.

Local refresh and CI-equivalent checks (no publication):

```bash
python -m unittest discover -s tests -p 'test_profile_stars.py' -v
python scripts/refresh_profile_stars.py
python scripts/build_folio.py
python scripts/check_folio.py --assets-only
python scripts/export_profile.py --write
python scripts/export_profile.py --check
```

The local preview can then be rerendered as above. The bio and total badge are
configured in `folio/profile-summary.json`. The bio uses the same chamfered
mount and IBM Plex Sans as the cards, at about 18 px: two lines on wide screens,
six reflowed lines on narrow screens, with the full wording in image alt text.
The subtitle follows the bio. The total badge (44 px canvas height,
about 13.4 px lettering) sits directly below the archive CTA, before social icons.
These use native Markdown pictures, not README CSS. The total's complete
public repository list and provenance live in `folio/total-stars.json`.
All three return links (archive top/bottom and acknowledgements) target
`https://github.com/HANCORE-linux`, not the repository's README view.

The separate page is titled “Inspired by”; its filename stays
`ACKNOWLEDGEMENTS.md` to preserve existing links. Its eight individually linked
cards form three centered rows (3–3–2) on desktop and wrap on narrow screens.
Their native size stays 248 × 89 px; GitHub may scale them slightly to fit the
smallest mobile content areas. The footer icon uses the same
“Inspired by” tooltip and accessible label. Each card has a square public GitHub
portrait on the left and centered Plex name/role to its right. Names, roles and original
destinations are configured in `folio/acknowledgements.json`. Portrait sources
are preserved and checked by hash; the daily star job does not refetch them.

GitHub can delay scheduled jobs. In public repositories it can disable schedules
after 60 days without repository activity; re-enable the workflow in Actions if
needed. See the [schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Actions are pinned to verified commit SHAs; the only write permission is
`contents: write` on this publishing job.

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
