// Controls belong to the local preview, never to the GitHub README.
(() => {
  const query = new URLSearchParams(location.search);
  const system = matchMedia("(prefers-color-scheme: dark)");
  let preference = query.get("theme") || "dark";
  if (!["dark", "light", "auto"].includes(preference)) preference = "dark";
  let view = query.get("view") === "readme" ? "readme" : "profile";
  function apply() {
    const theme = preference === "auto" ? (system.matches ? "dark" : "light") : preference;
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.view = view;
    document.querySelectorAll(".markdown-body").forEach(el => el.dataset.theme = theme);
    for (const a of document.querySelectorAll('a[href]')) {
      const url = new URL(a.getAttribute("href"), location.href);
      if (url.origin === location.origin && /\/(?:preview|themes|acknowledgements)\.html$/.test(url.pathname)) {
        url.searchParams.set("theme", preference);
        url.searchParams.set("view", view);
        a.href = url.pathname + url.search + url.hash;
      }
    }
  }
  apply();
  system.addEventListener("change", apply);
  document.addEventListener("DOMContentLoaded", () => {
    const themeControl = document.getElementById("preview-theme");
    const viewControl = document.getElementById("preview-view");
    themeControl.value = preference;
    viewControl.value = view;
    const update = () => {
      preference = themeControl.value; view = viewControl.value;
      const url = new URL(location.href);
      url.searchParams.set("theme", preference); url.searchParams.set("view", view);
      history.replaceState(null, "", url); apply();
    };
    themeControl.addEventListener("change", update);
    viewControl.addEventListener("change", update);
    apply();
  });
})();
