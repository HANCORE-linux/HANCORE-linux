# Historical profile workflow

This page documents the earlier layout. Use [Current profile workflow](PUBLISHING.md)
for the approved folio, port 8767 and the root publication exporter. Do not run
the historical pipeline below against the current published pages.

The public profile is README.md. This repository is intentionally not a separate frontend application.

## Build and preview

Requirements: Python 3.10+, ImageMagick, librsvg/rsvg-convert, JetBrains Mono and Nimbus Sans Narrow. A clean build is offline; original captures are kept under assets/sources and verified against data/sources.json.

```bash
python scripts/build_profile.py
python scripts/render_previews.py
python scripts/check_profile.py
python scripts/serve_preview.py --port 8765
```

Open http://127.0.0.1:8765/. Choose light/dark and profile frame/README-only in the toolbar. The server binds to loopback only and does not expose .git, .review, source captures or build scripts.

The Markdown renderer sends the three public-facing Markdown documents to GitHub's rendering API. No commit, push or GitHub profile update occurs. Successful renders are cached by content under .review/cache. For offline work, use `python scripts/render_previews.py --offline`; if no exact GitHub render is cached, this needs markdown-it-py and visibly labels the result as an approximation.

Optional browser checks (Node 22+ and Chromium):

```bash
node scripts/review_preview.mjs
```

Screenshots and measurements go to .review/current. The checks cover responsive widths, image loading, theme controls, links and navigation. Headless Chromium needs permission to create its local sockets in restricted environments.

## Sources and generated files

```text
README.md                  Profile copy + one generated theme section
THEMES.md                  Generated theme archive
ACKNOWLEDGEMENTS.md         Public credits
data/                      Theme catalogue + verified screenshot sources
assets/brand/              Editable branding + publication exports
assets/systems/            Editable project framing + publication exports
assets/themes/             Generated selection graphics + desktop previews
assets/sources/            Original, unmodified screenshots
assets/provenance.json     Generated input/output hashes
scripts/                   Build, rendering, serving and checks
docs/                      Current design and maintenance notes
.review/archive/           Previous work, kept locally and ignored by Git
.review/current/           Latest browser evidence
```

Change the catalogue in data/themes.json, not the generated archive. Rebuild after changing a source SVG or catalogue. Render previews again after Markdown or preview-tooling changes. `check_profile.py` detects missing references, stale generated content/previews, altered captures, missing alt text and accidentally empty image exports.

The palette samples are the four selected colors carried forward from the previous theme study assets, not complete ANSI palettes. Their original colors.toml revisions are recorded with the selected themes.

## Running server from the implementation session

The local preview runs as a transient user service (not enabled at login):

```bash
systemctl --user status hancore-profile-preview-20260915.service
systemctl --user stop hancore-profile-preview-20260915.service
```

If it has stopped or the machine has restarted, use the foreground serve command above. Rebuilds are visible on browser refresh.

Before publishing, explicitly approve the design and select the intended files for Git. The current redesign is local; never infer permission to commit or push from starting the preview server.
