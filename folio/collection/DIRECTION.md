# Unified theme-card series

The user prefers the first three project frames over the earlier folder-register theme frames. All 27 themes now share that neutral, single-chamfer frame and its shadow. The profile still shows only six cards, while `folio/THEMES.md` contains all 27 on a separate GitHub Markdown page. “Two large rows” is implemented as two large cards beside each other, followed by the next pair. On phones the native images wrap to one column. No website-only layout is inserted into the Markdown.

## Repeated geometry

- Export: 1248 × 984 PNG; 624 × 492 SVG viewBox.
- Profile: 248 × 196. Archive: 396 × 312; 13 pairs and a final single card.
- Full 16:9 preview window: x32/y24, 560 × 315; unchanged rendering size, no blur, retouching or destructive crop.
- Name is below the image at x44, baseline382, in 38px Plex Sans Medium. ANSI color00–07 remains left-aligned at x44/y420. Eight 22 × 30 swatches retain their exact source values.
- A single neutral mount with a cut lower-right corner, fine edge and floating shadow. No colored folder tab or rear layer. Only separate shadow shapes are filtered.
- Surface, edge and shadow settings are identical to Shibumi/OmaQ/Marketplace. Text contrast is checked at 4.5:1 or better; long titles keep the same size and left edge.
- Banish alone carries the orange `NEW` badge right-aligned directly above Stars: x520/y374, 60 × 24, sharing the Stars box's x580 right edge with a visible gap below. This supersedes the earlier subscript placement at the h. Its shadow is clipped to the caption region, never the screenshot or palette. Black lettering meets 4.5:1 contrast. Image alternative text also includes NEW; `THEME_LABELS` in `folio_register.py` controls this explicit editorial label.
- All 27 black/orange Stars badges now have a four-pixel 45-degree cut at the lower-right corner, echoing the larger card's cut. The separate shadow uses the same clipped silhouette. Original Shields SVGs, counts and dated snapshots remain unchanged; no digit or label is cropped. Badges scale with the larger archive cards. `folio_badges.py` is the shared geometry source for all 54 dark/light exports.

Original local screenshots are never edited. The six known public previews reuse their verified Git blob sources. The other 21 are downloaded from each public repository's `HEAD/preview.png`, checked as high-resolution 16:9 PNGs and recorded with SHA-256 and retrieval date. These records describe the fetched snapshots, not a guarantee that upstream never changes.

## HANCORE direction

The default profile uses an independent interlocking HC signet above a smaller HANCORE name, both in #DF6124. See `scripts/folio_identity.py` and `folio/wordmark-core-{dark,light}.svg`. The symbol alone is `folio/mark-core-{dark,light}.svg`; corresponding transparent PNGs are in `folio/assets/`. The previous seven-letter drawn wordmark and H mark remain archived comparisons. The public avatar is unchanged. `identity.html` retains the earlier thin-outline lettering study, explicitly labeled as a historical comparison. The wide profile uses two connection groups: projects through Waybar/QS-Dots to the three highlights, then a fresh group through the six popular themes, merging into the “All 27 themes” archive link. Fifteen separate circuit-slice images retain individual links; narrow views use the base cards. Project and info-card texts are centered, while all theme names and palettes remain unchanged and left-aligned. These are profile-only wrappers: all 27 archive cards, their original exports and the archive Markdown are unchanged and have no added connectors. The footer also links to a separate Acknowledgements page via the book/heart icon after Ko-fi. See the profile's `DIRECTION.md` for implementation and verification details.

The archive heading is now a matching shallow tile with the series' cut lower-right corner, fine outline and floating shadow. “Theme archive” uses orange (#DF6124 on dark mounts, contrast-adjusted #AC450F on light mounts); “27 themes · color00–07 · A–Z” stays neutral. Both lines retain centered, approximately 16px IBM Plex Sans Semibold. `label-archive-{dark,light}.png` exports at 1408 × 384 and displays at 280 × 76, leaving room for the complete metadata and alternative text. All 27 theme-card exports, footprints and their two-column wrapping remain unchanged; the archive still contains 28 images and the same 29 links. The commit/push request is paused during this final design adjustment.

## Build and verification

`build_folio.py` exports the original assets first, then calls `build_theme_registers.build()`, then composes the independent connection wrappers from those current exports. `render_folio.py` renders the main profile, archive, identity study, compatibility profile route and Acknowledgements page with GitHub's Markdown API. Run the separate historical study renderer afterwards if needed.

```sh
python scripts/build_folio.py
python scripts/render_folio.py
python scripts/build_register_study.py --render
python scripts/check_folio.py
python scripts/build_register_study.py --check
node scripts/review_folio.mjs
```

`build_theme_registers.py --fetch` deliberately refreshes the 21 additional source previews/badges; it is not run during a normal build. Review fetched inputs before rebuilding. Badge and ranking snapshots are separate; this iteration preserves the original top-six selection.

Checks cover source/export hashes, exact frame/shadow agreement with project cards, screenshot and badge pixel presence, exact palettes, readable labels, logo path-only geometry, 27 canonical repository links, real two-column desktop wrapping, mobile wrapping, keyboard navigation, dark/light selection and the preview's private-file boundaries. `scripts/review_folio.mjs` delegates to the current collection review; the old inline-table review is preserved with the prior design backup.

Only port 8767 is used. `/collection.html` and `/identity.html` serve previews; raw source files and manifests are not served by the preview. The user approved publication after the final title-color review on 2026-09-15; `export_profile.py` now promotes the approved folio pages to the root. Public avatar, account settings and pins remain unchanged. Earlier local-only statements above refer to their respective design iterations.
