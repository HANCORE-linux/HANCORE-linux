# Editorial concept — upper profile only

Local draft for visual approval. This is not the publication README and does not replace it.

Priority: quiet identity → one atmospheric, real desktop → current project → compact work index.

The H is a small signature, not a repeated decorative system. A compact wordmark replaces the oversized hero. Rose of Dune supplies the opening image and is explicitly labeled as a theme, not Shibumi. Shibumi stays visible as the current project with a smaller, genuine control-center image. Normal descriptions remain readable; only metadata uses small text. No numbered title bands, new wallpaper, fabricated UI, or custom CSS inside the README.

Sources: the existing verified Rose of Dune and Shibumi exports. The signature reuses the paths of the constructed-H logo without modifying the original avatar or hero. The new wordmark uses Nimbus Sans.

The preview uses GitHub's Markdown renderer and the existing GitHub stylesheet. The preview toolbar and draft/comparison navigation are local UI only. Light/dark source selection is synchronized with the preview controls; the actual Markdown uses `prefers-color-scheme` picture sources.

## Run

```bash
python scripts/render_concept.py
python scripts/serve_concept.py --port 8766
node scripts/review_preview.mjs --concept
```

Open http://127.0.0.1:8766/concept.html?view=readme . The previous design remains at http://127.0.0.1:8765/ and is also linked from the draft. An offline render can use `--offline`; non-GitHub fallback is visibly labeled.

Generated signature PNGs and HTML are built from the script and this Markdown. Build hashes live in `.review/concept-manifest.json`; browser evidence lives in `.review/concept/`. No commit, push, or publication is requested.
