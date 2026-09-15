// Preview-only: keep image sources in sync with the local theme selector.
// The README itself retains ordinary prefers-color-scheme picture sources.
(() => {
  function sync() {
    const dark = document.documentElement.dataset.theme === 'dark';
    document.querySelectorAll('article source[srcset*="signature-dark"]').forEach(source => {
      source.media = dark ? 'all' : 'not all';
    });
    const query = new URLSearchParams(location.search);
    const draft = document.querySelector('nav a[href*="concept.html"]');
    if (draft) draft.href = './concept.html?' + query;
  }
  new MutationObserver(sync).observe(document.documentElement, {attributes:true, attributeFilter:['data-theme', 'data-view']});
  document.addEventListener('DOMContentLoaded', sync);
  sync();
})();
