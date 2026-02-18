(() => {
  const STORAGE_KEY = "pch_theme";
  const root = document.documentElement;
  const media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function getStoredTheme() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return value === "dark" || value === "light" ? value : null;
    } catch (_) {
      return null;
    }
  }

  function getResolvedTheme() {
    const stored = getStoredTheme();
    if (stored) return stored;
    return media && media.matches ? "dark" : "light";
  }

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
  }

  function persistTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {
      // ignore localStorage write errors
    }
  }

  function updateToggleButton() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;
    const current = root.getAttribute("data-theme") || getResolvedTheme();
    const next = current === "dark" ? "light" : "dark";
    button.setAttribute("aria-pressed", current === "dark" ? "true" : "false");
    button.setAttribute("aria-label", `Переключить тему. Сейчас: ${current === "dark" ? "темная" : "светлая"}`);
    button.dataset.nextTheme = next;

    const label = button.querySelector(".theme-toggle__label");
    const icon = button.querySelector(".theme-toggle__icon");
    if (label) label.textContent = current === "dark" ? "Темная" : "Светлая";
    if (icon) icon.textContent = current === "dark" ? "🌙" : "☀";
  }

  function toggleTheme() {
    const current = root.getAttribute("data-theme") || getResolvedTheme();
    const next = current === "dark" ? "light" : "dark";
    const reduceMotion =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!reduceMotion) {
      root.classList.add("theme-smooth");
    }
    setTheme(next);
    persistTheme(next);
    updateToggleButton();
    if (!reduceMotion) {
      setTimeout(() => root.classList.remove("theme-smooth"), 420);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    setTheme(getResolvedTheme());
    const button = document.getElementById("theme-toggle");
    if (button) {
      button.addEventListener("click", toggleTheme);
    }
    updateToggleButton();
  });

  if (media && media.addEventListener) {
    media.addEventListener("change", () => {
      if (!getStoredTheme()) {
        setTheme(getResolvedTheme());
        updateToggleButton();
      }
    });
  }
})();
