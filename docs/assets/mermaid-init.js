(function () {
  let initialized = false;

  function renderMermaid() {
    if (typeof mermaid === "undefined") {
      return;
    }

    if (!initialized) {
      mermaid.initialize({ startOnLoad: true, theme: "base" });
      initialized = true;
    }

    mermaid.run({ querySelector: ".mermaid" });
  }

  if (typeof document$ !== "undefined" && document$ && typeof document$.subscribe === "function") {
    document$.subscribe(renderMermaid);
  }

  if (typeof document !== "undefined" && document.addEventListener) {
    document.addEventListener("DOMContentLoaded", renderMermaid, { once: true });
  }

  renderMermaid();
})();
