# Profile tools

Current instructions: [Profile workflow](../docs/PUBLISHING.md). Current design: [Folio](../folio/DIRECTION.md).

```bash
python scripts/build_folio.py
python scripts/render_folio.py
python scripts/build_register_study.py --render
python scripts/check_folio.py
python scripts/export_profile.py --write
python scripts/export_profile.py --check
# Only if the existing preview has stopped:
python scripts/serve_folio.py --port 8767
```

- `build_folio.py`: builds current cards, labels, archive and connected picture variants from verified sources.
- `render_folio.py`: GitHub-rendered local profile, archive and acknowledgements previews.
- `check_folio.py`: asset, alignment, contrast, palette, link and render-freshness checks.
- `export_profile.py`: explicit root publication export (`--write`) or read-only freshness/link validation (`--check`); never commits or pushes.
- `serve_folio.py`: loopback-only preview server on port 8767.
- `review_folio.mjs`: isolated Chromium layout, navigation and connector checks.
- `refresh_profile_stars.py`: validated, no-op-aware refresh of all theme stars, top-six ranking and total including Marketplace; never pushes itself. Used by the daily `profile-stars.yml` workflow.
- `refresh_folio_totals.py`: shared public-repository collector and standalone total refresh; excludes forks and deduplicates by repository ID.
- `check_folio.py --assets-only`: CI asset/link/provenance checks without local browser caches.

The older `build_profile.py`, `check_profile.py`, `review_preview.mjs` and `export_assets.sh` pipeline is historical, not the current publication workflow. Shared rendering/server helpers remain in use. Local backups are ignored under `.review/archive/`.
