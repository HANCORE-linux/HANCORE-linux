#!/usr/bin/env python3
"""Render the separate native Markdown archive and an unselected identity study."""
import json
import re
from build_folio import ROOT, FOLIO, checksum
from render_previews import render_markdown, source_hash


def render_pages():
    frame = (ROOT / 'folio.html').read_text()
    profile = (FOLIO / 'README.md').read_text()
    identity = re.sub(r'\./assets/wordmark-[a-z]+-(dark|light)\.png', r'./collection/assets/identity-\1.png', profile)
    identity = identity.replace('<!-- BEGIN GENERATED: identity -->', '<p align="center"><sub>Frühere Namensstudie · vollständig gezeichnete Buchstaben · zum Vergleich</sub></p>\n\n<!-- BEGIN GENERATED: identity -->')
    source = FOLIO / 'collection/IDENTITY.md'
    source.write_text(identity.replace('"./assets/', '"../assets/').replace('"./collection/assets/', '"./assets/').replace('"./THEMES.md"', '"../THEMES.md"').replace('"./ACKNOWLEDGEMENTS.md"', '"../ACKNOWLEDGEMENTS.md"'))
    outputs = [source]
    renderers = []
    for route, title, markdown in [
        ('collection.html', 'THEMES.md', (FOLIO / 'THEMES.md').read_text()),
        ('identity.html', 'HANCORE · Namensstudie', identity),
        ('register-profile.html', 'README · Registerserie', profile),
        ('folio-acknowledgements.html', 'ACKNOWLEDGEMENTS.md', (FOLIO / 'ACKNOWLEDGEMENTS.md').read_text()),
    ]:
        resolved = markdown.replace('"./assets/', '"./folio/assets/').replace('"./collection/', '"./folio/collection/')
        resolved = resolved.replace('"./README.md"', '"./folio.html"').replace('"./THEMES.md"', '"./collection.html?view=readme"')
        resolved = resolved.replace('"./ACKNOWLEDGEMENTS.md"', '"./folio-acknowledgements.html?view=readme"')
        rendered, renderer = render_markdown(resolved)
        page = re.sub(r'(<article class="markdown-body"[^>]*>).*?(</article>)', lambda m: m[1] + '\n' + rendered + '\n' + m[2], frame, count=1, flags=re.S)
        page = re.sub(r'(<meta name="profile-source-sha256" content=")[^"]+', lambda m: m[1] + source_hash(markdown), page)
        page = page.replace('<title>HANCORE · Compact GitHub profile</title>', f'<title>HANCORE · {title}</title>')
        page = page.replace('HANCORE-linux / README.md', f'HANCORE-linux / {title}')
        page = page.replace(' aria-current="page"', '')
        page = page.replace(f'href="./{route}' + ('?view=readme' if route == 'collection.html' else '') + '"', f'href="./{route}' + ('?view=readme' if route == 'collection.html' else '') + '" aria-current="page"')
        if route != 'register-profile.html':
            page = re.sub(r'<label for="preview-wordmark">.*?</select>', '', page, count=1, flags=re.S)
        if route in ('collection.html', 'folio-acknowledgements.html'):
            page = re.sub(r'<section class="folio-pins".*?</section>', '', page, count=1, flags=re.S)
        output = ROOT / route
        output.write_text(page)
        outputs.append(output)
        renderers.append(renderer)
    inputs = [FOLIO / 'README.md', FOLIO / 'THEMES.md', FOLIO / 'ACKNOWLEDGEMENTS.md', ROOT / 'folio.html', ROOT / 'scripts/render_register_pages.py']
    manifest = {'renderers': renderers, 'inputs': {str(p.relative_to(ROOT)): checksum(p) for p in inputs},
                'outputs': {str(p.relative_to(ROOT)): checksum(p) for p in outputs}}
    (ROOT / '.review/register-pages-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('OK GitHub-rendered theme archive, identity study, complete register profile and acknowledgements')


if __name__ == '__main__':
    render_pages()
