# Solitude / register study

This records the original, approved single-card study. It has since been extended to all 27 themes; see [the collection direction](../../collection/DIRECTION.md). The single-card comparison and its PNGs remain unchanged. The previous profile with its inline palette table is preserved in `.review/archive/vor-register-serie-dTJh4y/`.

## Composition

A shallow, chamfered folder tab uses Solitude's own color07 (#CBC2BE). The front is color00 (#101315); the single offset back layer and fine light edge use its gray palette. The real desktop occupies a complete 16:9 window, without blurring or retouching. Eight equal swatches below show exact color00–07 from the verified `colors.toml`. The original black/orange, dated 61-star badge retains its shadow and its 60 × 20 display size in the normal 248 × 196 card.

The title is left-aligned IBM Plex Sans Medium (bundled SIL OFL font). No reference-site fonts or artwork were copied. The larger 496 × 392 display is a review enlargement, not a proposal to enlarge the profile grid. The PNG export is 1248 × 984 with transparent margins. The static link opens the actual Solitude repository; it does not pretend to be an interactive tab stack.

## References

- [Zuji](https://x.com/_zuji/status/2099779205135511967): restrained technical form language and cut corners, not its identifying symbol.
- [Bedirhan](https://x.com/bedirhandogn/status/2098336712812335257): fine edge lighting and restrained depth, not unreadably dark labels or circuitry decoration.
- [Slava Kornilov](https://x.com/slavakornilov/status/2096724597080989846): layered register silhouettes, not the phone mockup, icons or interactive animation.

## Preview and verification

- `http://127.0.0.1:8767/register.html?view=readme` — enlarged card and old/new at actual profile size (stacked in the same order on narrow screens).
- `http://127.0.0.1:8767/register-profile.html` — current GitHub-rendered profile with all six register cards, still at 248 × 196.
- `http://127.0.0.1:8767/` — active compact profile; its archive link opens a separate Markdown page.

```sh
python scripts/render_folio.py
python scripts/build_register_study.py --render
python scripts/build_register_study.py --check
python scripts/check_folio.py
node scripts/review_folio.mjs
```

Sources and exports are hashed in `.review/register-manifest.json`. Native SVGs live at `folio/register-solitude-{dark,light}.svg` so librsvg can load resources below their base directory. An initial nested-path export omitted the screenshot and badge; the corrected exporter uses the existing folio resource layout and checks pixel variation inside both regions to catch silent loading failures. It also checks exact swatch values, source lineage, 16:9 geometry, PNG dimensions and file size.

The original comparison and current profile are rendered by GitHub's Markdown API; only their outer local preview has controls. The current context route is owned by `render_register_pages.py`, while `build_register_study.py --render` renders only the historical comparison. Current runtime checks cover 320, 390, 768 and 1440 widths in light/dark, native image links, source selection, archive separation and private-file route boundaries.

Backup before this study: `.review/archive/vor-register-dJ7jTk/`. No profile publication, account changes or additional servers.
