#!/usr/bin/env python3
"""Render the compact README through GitHub; preserve previous drafts."""
import argparse
import hashlib
import html
import json
from render_previews import ROOT, page_html, render_markdown, source_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    markdown = (ROOT / 'folio/README.md').read_text()
    resolved = markdown.replace('"./assets/', '"./folio/assets/').replace('"./collection/', '"./folio/collection/').replace('"./THEMES.md"', '"./collection.html?view=readme"')
    resolved = resolved.replace('"./ACKNOWLEDGEMENTS.md"', '"./folio-acknowledgements.html?view=readme"')
    rendered, renderer = render_markdown(resolved, args.offline)
    page = page_html('README.md', 'folio.html', 'HANCORE · Compact GitHub profile', rendered, renderer, source_hash(markdown))
    page = page.replace('scripts/render_previews.py.', 'scripts/render_folio.py.')
    page = page.replace('</head>', '<link rel="stylesheet" href="folio/preview.css">\n<script src="folio/preview.js" defer></script>\n</head>')
    page = page.replace('src="./assets/brand/avatar-h-construct.png"', 'src="./folio/public-avatar.png"').replace('HANCORE constructed H avatar', 'Current public HANCORE GitHub avatar')
    page = page.replace('HANCORE-linux / Profilvorschau', 'HANCORE / README-Entwurf')
    identity = json.loads((ROOT / 'folio/identity.json').read_text())
    options = ''.join(f'<option value="{v["id"]}"' + (' selected' if v['id'] == identity['selected'] else '') + f'>{html.escape(v["label"])}</option>' for v in identity['variants'])
    page = page.replace('      <label for="preview-view">', f'      <label for="preview-wordmark">Wortmarke</label><select id="preview-wordmark">{options}</select>\n      <label for="preview-view">')
    start = page.index('  <nav class="preview-tabs"')
    end = page.index('</nav>', start) + len('</nav>')
    page = page[:start] + '''  <nav class="preview-tabs" aria-label="Draft comparison">
    <a href="./folio.html" aria-current="page">Kompaktes Profil</a>
    <a href="./collection.html?view=readme">Alle Themes</a>
    <a href="./identity.html">Namensstudie</a>
    <a href="./register.html">Registerstudie</a>
    <a href="./preview.html">Bisheriger Stand</a>
  </nav>''' + page[end:]
    cards = []
    for pin in json.loads((ROOT / 'folio/pins.json').read_text()):
        language = '' if not pin['language'] else f'<span class="language"><i style="background:{pin["color"]}"></i>{html.escape(pin["language"])}</span>'
        owner = pin.get('owner', 'HANCORE-linux')
        cards.append(f'<li><a href="https://github.com/{html.escape(owner)}/{html.escape(pin["repo"])}">{html.escape(pin["repo"])}</a><p>{html.escape(pin["description"])}</p>{language}</li>')
    pins = '<section class="folio-pins" aria-label="Proposed pinned repositories"><h2>Pinned <small>Lokaler Vorschlag</small></h2><ul>' + ''.join(cards) + '</ul></section>'
    page = page.replace('<main id="main-content" class="profile-frame">', '<div class="profile-column"><main id="main-content" class="profile-frame">')
    page = page.replace('    </main>', '    </main>' + pins + '</div>')
    page = page.replace('Lokale Designvorschau mit GitHub-Markdown. Der Profilrahmen ist angenähert; dein veröffentlichtes GitHub-Profil bleibt unverändert.',
                        'GitHub-gerendertes README. Profilrahmen angenähert, Pins als lokaler Vorschlag. Dein veröffentlichtes Profil und die bisherigen Entwürfe bleiben unverändert.')
    (ROOT / 'folio.html').write_text(page)
    names = ['folio/README.md','folio/identity.json','folio/highlights.json','folio/popular-themes.json','data/themes.json','folio/pins.json','folio/preview.css','folio/preview.js','folio/public-avatar.png','scripts/render_folio.py','scripts/render_previews.py',
             'scripts/preview/preview.css','scripts/preview/preview.js','scripts/preview/github-markdown.min.css','scripts/preview/github-markdown-themes.css']
    names.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / 'folio/assets').glob('*.png')))
    names.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / 'folio/collection/assets').glob('*.png')))
    names.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / 'folio/assets').glob('*.svg')))
    names.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / 'folio/collection/assets').glob('*.svg')))
    checksum = lambda name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    manifest = {'renderer':renderer,'inputs':{p:checksum(p) for p in names},'outputs':{'folio.html':checksum('folio.html')}}
    (ROOT / '.review/folio-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    from render_register_pages import render_pages
    render_pages()
    print(f'folio/README.md → folio.html ({renderer})')


if __name__ == '__main__':
    main()
