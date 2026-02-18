/**
 * Горячие клавиши платформы.
 * Поддерживает ввод как в английской, так и в русской раскладке,
 * включая смешанные последовательности (например: g m, п ь, g ь, п m).
 */

class HotkeyManager {
  constructor() {
    this.ruToEn = {
      "й": "q", "ц": "w", "у": "e", "к": "r", "е": "t", "н": "y", "г": "u", "ш": "i", "щ": "o", "з": "p",
      "х": "[", "ъ": "]",
      "ф": "a", "ы": "s", "в": "d", "а": "f", "п": "g", "р": "h", "о": "j", "л": "k", "д": "l", "ж": ";", "э": "'",
      "я": "z", "ч": "x", "с": "c", "м": "v", "и": "b", "т": "n", "ь": "m", "б": ",", "ю": ".",
      ".": "/", ",": "?"
    };

    this.hotkeys = {
      // Навигация
      "g h": { action: () => (window.location.href = "/"), description: "Перейти на главную" },
      "g f": { action: () => (window.location.href = "/forum/"), description: "Перейти в форум" },
      "g c": { action: () => (window.location.href = "/learning/"), description: "Перейти в каталог курсов" },
      "g m": { action: () => (window.location.href = "/creator/courses/"), description: "Перейти в Мои курсы" },
      "g p": { action: () => (window.location.href = "/profile/"), description: "Перейти в профиль" },
      "g a": { action: () => (window.location.href = "/analytics/"), description: "Перейти в аналитику" },

      // Действия
      "c": { action: () => this.createNewTopic(), description: "Создать новую тему" },
      "r": { action: () => this.replyToTopic(), description: "Ответить в теме" },
      "b": { action: () => this.openCoursePayment(), description: "Открыть оплату курса" },
      "n": { action: () => this.openNextLesson(), description: "Перейти к следующему уроку" },
      "/": { action: () => this.focusSearch(), description: "Фокус на поиск" },
      "?": { action: () => this.showHotkeyHelp(), description: "Показать список горячих клавиш" },
      "t": { action: () => this.toggleTheme(), description: "Сменить тему" },

      // Модерация
      "m d": { action: () => this.deletePost(), description: "Удалить пост (модератор)" },
      "m p": { action: () => this.pinTopic(), description: "Закрепить/открепить тему (модератор)" },

      // Утилиты
      "escape": { action: () => this.closeModals(), description: "Закрыть модальные окна" },
      "ctrl+k": { action: () => this.quickCommand(), description: "Быстрая команда" }
    };

    this.sequence = [];
    this.sequenceTimer = null;
    this.init();
  }

  init() {
    document.addEventListener("keydown", (e) => this.handleKeyPress(e));
    this.createHelpModal();
  }

  normalizeKey(rawKey) {
    if (!rawKey) return "";
    const key = String(rawKey).toLowerCase();
    if (this.ruToEn[key]) return this.ruToEn[key];
    return key;
  }

  handleKeyPress(e) {
    const inEditable = ["INPUT", "TEXTAREA"].includes(e.target.tagName) || e.target.isContentEditable;
    const rawKey = String(e.key || "").toLowerCase();

    // Спец-клавиши работают всегда
    if (rawKey === "escape") {
      this.hotkeys["escape"].action();
      return;
    }
    if (e.ctrlKey && rawKey === "k") {
      e.preventDefault();
      this.hotkeys["ctrl+k"].action();
      return;
    }

    // В полях ввода блокируем остальные
    if (inEditable) return;

    const key = this.normalizeKey(rawKey);

    // Для "/" и "?" разрешаем оба варианта key
    const isHelp = rawKey === "?" || key === "?";
    const isSearch = rawKey === "/" || key === "/";

    if (isHelp) {
      e.preventDefault();
      this.hotkeys["?"].action();
      this.sequence = [];
      return;
    }
    if (isSearch) {
      e.preventDefault();
      this.hotkeys["/"].action();
      this.sequence = [];
      return;
    }

    const maybeHotkey = this.hotkeys[key] || ["g", "m"].includes(key);
    if (maybeHotkey) e.preventDefault();

    this.sequence.push(key);

    if (this.sequenceTimer) clearTimeout(this.sequenceTimer);
    this.sequenceTimer = setTimeout(() => {
      this.sequence = [];
    }, 1000);

    const sequenceStr = this.sequence.join(" ");

    if (this.hotkeys[key]) {
      this.hotkeys[key].action();
      this.sequence = [];
      return;
    }
    if (this.hotkeys[sequenceStr]) {
      this.hotkeys[sequenceStr].action();
      this.sequence = [];
    }
  }

  createNewTopic() {
    const createBtn = document.querySelector('[data-action="create-topic"], a[href*="/topics/create/"]');
    if (createBtn) createBtn.click();
  }

  replyToTopic() {
    const replyArea = document.querySelector("#reply-textarea, textarea[name=\"content\"], .ql-editor");
    if (replyArea) {
      replyArea.focus();
      replyArea.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  openCoursePayment() {
    const buyBtn = document.querySelector('a[href*="/purchase/"], button[data-action="buy-course"]');
    if (buyBtn) buyBtn.click();
  }

  openNextLesson() {
    const nextBtn = document.querySelector(".next-lesson-button");
    if (nextBtn) nextBtn.click();
  }

  focusSearch() {
    const searchInput = document.querySelector(
      "input[type=\"search\"], input[name=\"search\"], #search-input, input[name=\"q\"]"
    );
    if (searchInput) {
      searchInput.focus();
      if (searchInput.select) searchInput.select();
    }
  }

  toggleTheme() {
    const btn = document.getElementById("theme-toggle");
    if (btn) btn.click();
  }

  showHotkeyHelp() {
    const modal = document.getElementById("hotkey-help-modal");
    if (modal) modal.style.display = "flex";
  }

  deletePost() {
    const allowed = ["moderator", "admin_level_1", "admin_level_2", "admin_level_3", "super_admin"];
    const role = document.body.dataset.userRole;
    if (!role || !allowed.includes(role)) {
      this.showNotification("Недостаточно прав для удаления постов", "error");
      return;
    }
    const deleteBtn = document.querySelector(".post:focus .delete-btn, .post:hover .delete-btn");
    if (deleteBtn) deleteBtn.click();
  }

  pinTopic() {
    const allowed = ["moderator", "admin_level_1", "admin_level_2", "admin_level_3", "super_admin"];
    const role = document.body.dataset.userRole;
    if (!role || !allowed.includes(role)) {
      this.showNotification("Недостаточно прав для закрепления тем", "error");
      return;
    }
    const pinBtn = document.querySelector('[data-action="pin-topic"]');
    if (pinBtn) pinBtn.click();
  }

  closeModals() {
    document.querySelectorAll(".modal, [role=\"dialog\"]").forEach((modal) => {
      modal.style.display = "none";
    });
    document.querySelectorAll(".dropdown.open").forEach((dropdown) => {
      dropdown.classList.remove("open");
    });
  }

  quickCommand() {
    this.showNotification("Палитра команд в разработке", "info");
  }

  showNotification(message, type = "info") {
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 16px;
      background: ${type === "error" ? "#ff6b6b" : "#33c6d6"};
      color: #0f1720;
      border-radius: 8px;
      z-index: 10000;
      animation: slideIn 0.25s ease;
    `;
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.style.animation = "slideOut 0.25s ease";
      setTimeout(() => notification.remove(), 250);
    }, 2000);
  }

  createHelpModal() {
    const modal = document.createElement("div");
    modal.id = "hotkey-help-modal";
    modal.style.cssText = `
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.75);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      padding: 20px;
    `;

    const content = document.createElement("div");
    content.style.cssText = `
      background: var(--bg-card, #1a1a2e);
      color: var(--text-primary, #fff);
      padding: 24px;
      border-radius: 12px;
      width: min(760px, 100%);
      max-height: 80vh;
      overflow-y: auto;
      border: 1px solid var(--border-color, #2a3347);
    `;

    let html = "<h2 style=\"margin-top:0; margin-bottom:14px;\">Горячие клавиши</h2>";
    html += "<div style=\"display:grid; grid-template-columns: minmax(120px, 180px) 1fr; gap:10px 14px;\">";
    Object.entries(this.hotkeys).forEach(([key, config]) => {
      html += `
        <div style="font-family: var(--font-mono, monospace); background: rgba(127,127,127,0.15); border: 1px solid var(--border-color, #2a3347); border-radius: 6px; padding: 6px 8px; text-align:center;">
          ${key}
        </div>
        <div style="padding: 6px 0;">${config.description}</div>
      `;
    });
    html += "</div>";
    html += "<p style=\"margin-top:14px; color: var(--text-secondary, #aaa);\">Поддерживается русская и английская раскладка, включая смешанный ввод.</p>";
    html += "<p style=\"margin-top:6px; color: var(--text-secondary, #aaa);\"><kbd>?</kbd> — открыть справку, <kbd>Esc</kbd> — закрыть.</p>";

    content.innerHTML = html;
    modal.appendChild(content);
    document.body.appendChild(modal);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.style.display = "none";
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.hotkeyManager = new HotkeyManager();
  });
} else {
  window.hotkeyManager = new HotkeyManager();
}

const style = document.createElement("style");
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
  kbd {
    background: rgba(127,127,127,0.2);
    border: 1px solid rgba(127,127,127,0.35);
    border-radius: 4px;
    padding: 2px 6px;
    font-family: var(--font-mono, monospace);
  }
`;
document.head.appendChild(style);
