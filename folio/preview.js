// Preview controls only. None of this script is included in the README.
(() => {
  function sync() {
    const dark = document.documentElement.dataset.theme === 'dark';
    const control = document.getElementById('preview-wordmark');
    const query = new URLSearchParams(location.search);
    const requested = query.get('wordmark');
    if (control && requested && [...control.options].some(option => option.value === requested)) control.value = requested;
    if (control) {
      const source = document.querySelector('article source[srcset*="wordmark-"]');
      const picture = source?.closest('picture');
      if (picture) {
        source.srcset = './folio/assets/wordmark-' + control.value + '-dark.png';
        picture.querySelector('img').src = './folio/assets/wordmark-' + control.value + '-light.png';
      }
    }
    document.querySelectorAll('article source[media]').forEach(source => {
      // Override only color scheme for the preview control. Keep native width
      // queries intact, so desktop connectors cannot leak into wrapping views.
      if (!source.dataset.originalMedia) source.dataset.originalMedia = source.media;
      source.media = source.dataset.originalMedia.replace(/\(prefers-color-scheme:\s*(dark|light)\)/g,
        (_, mode) => (mode === (dark ? 'dark' : 'light') ? '(min-width: 0px)' : '(max-width: 0px)'));
    });
    for (const a of document.querySelectorAll('nav a[href], article a[href]')) {
      const url = new URL(a.href, location.href);
      if (url.origin === location.origin && /\/(?:folio|register|register-profile|collection|identity|folio-acknowledgements)\.html$/.test(url.pathname)) {
        url.search = location.search;
        if (['/collection.html', '/folio-acknowledgements.html'].includes(url.pathname)) url.searchParams.set('view', 'readme');
        a.href = url.pathname + url.search;
      }
    }
  }
  new MutationObserver(sync).observe(document.documentElement, {attributes:true, attributeFilter:['data-theme','data-view']});
  document.addEventListener('DOMContentLoaded', () => {
    const control = document.getElementById('preview-wordmark');
    if (control) control.addEventListener('change', () => {
      const url = new URL(location.href);
      url.searchParams.set('wordmark', control.value);
      history.replaceState(null, '', url);
      sync();
    });
    sync();
  });
  sync();
})();
