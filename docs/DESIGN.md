# HANCORE profile — historical direction

This page records an earlier design. The approved connected-card profile is
documented in [folio/DIRECTION.md](../folio/DIRECTION.md); see
[Current profile workflow](PUBLISHING.md) for publication instructions.

Approved implementation direction: 2026-09-15. Local review only; no commit, push or profile publication requested.

## Priority

Identity → current work (Shibumi) → other work (Waybar, Rise) → selected themes → marketplace/community → contact.

Keep the constructed H and charcoal / cream / orange identity. The header carries only the wordmark and mark; the personal introduction is readable HTML text.

The latest direction extends the logo's construction lines, orange registration accents and condensed cream lettering into numbered section-title graphics. These are actual README assets, not preview-only CSS. Each graphic sits in a semantic heading with a descriptive image alternative; project headings are also repository links. The archive and credits use the same title system.

Images precede descriptions. Keep descriptions to one short line, rendered with GitHub-supported `sub` markup, with small text links below. Status, descriptions and navigation remain selectable HTML text, not baked into images. Shibumi is labeled Beta, with a link to its live release status rather than a soon-stale version number.

## Images

- Shibumi: one real control-center window from the public repository, not the older mockup.
- Waybar: three different, native-resolution bar details; no claim that these are complete layouts.
- Rise: existing full-resolution V1 carousel capture, cropped to the picker. It is not a new capture or a V2 screenshot. Do not upscale compressed UI details or invent sharpness with generated UI.
- Themes: three actual published desktop screenshots. A landscape selection on desktop becomes a stacked selection below 600 px using GitHub-supported picture/source HTML. The names and repository links also appear as Markdown.
- Raster exports are produced from editable SVGs. The build embeds verified screenshots into a temporary SVG because librsvg restricts sibling-directory file access. No generated screenshot content.
- Section titles are generated from one SVG template in `scripts/build_profile.py`; title and number definitions live in `SECTIONS`. Export them losslessly at 900 × 108. The hero and constructed-H avatar remain unchanged.

## Single sources of truth

- Profile narrative: README.md, except the marked generated theme region.
- Theme catalogue, order, count and palette samples: data/themes.json.
- Original screenshot URLs and checksums: data/sources.json.
- Generated archive and theme graphics: scripts/build_profile.py.
- Export and dependency hashes: assets/provenance.json (generated).
- Preview HTML: scripts/render_previews.py; never edit HTML output manually.

Earlier concepts, retired assets and their build scripts are preserved in .review/archive. They are historical evidence, not current requirements. The complete pre-change working copy is in .review/archive/vor-redesign-20260915-TX4FgJ.

The README, assets, catalogue, scripts and documentation immediately before the logo-layout refinement are preserved in .review/archive/vor-logo-layout-20260915-tUpgvA.

## Preview fidelity

The default renderer is GitHub's Markdown API. The preview uses vendored github-markdown-css without replacing README link colors or typography. Only the surrounding profile frame and theme controls are local UI; they are not published or presented as a pixel-perfect GitHub clone. Offline fallback is explicitly labeled. Check 320/390/900/1440 px, both color schemes, archive navigation and the narrow picture source.
