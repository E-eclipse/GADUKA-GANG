(() => {
  const MODAL_ID = "attachment-viewer-modal";

  function ensureModal() {
    let modal = document.getElementById(MODAL_ID);
    if (modal) return modal;

    modal = document.createElement("div");
    modal.id = MODAL_ID;
    modal.className = "attachment-viewer-modal is-hidden";
    modal.innerHTML = `
      <div class="attachment-viewer-backdrop" data-close="1"></div>
      <div class="attachment-viewer-dialog" role="dialog" aria-modal="true" aria-label="Просмотр вложения">
        <button type="button" class="attachment-viewer-close" data-close="1" aria-label="Закрыть">&times;</button>
        <div class="attachment-viewer-body"></div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.addEventListener("click", (e) => {
      if (e.target && e.target.getAttribute("data-close") === "1") {
        closeModal();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modal.classList.contains("is-hidden")) {
        closeModal();
      }
    });

    return modal;
  }

  function closeModal() {
    const modal = document.getElementById(MODAL_ID);
    if (!modal) return;
    const body = modal.querySelector(".attachment-viewer-body");
    if (body) body.innerHTML = "";
    modal.classList.add("is-hidden");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function openImage(src, title) {
    const modal = ensureModal();
    const body = modal.querySelector(".attachment-viewer-body");
    const safeTitle = escapeHtml(title || "Изображение");
    body.innerHTML = `
      <div class="attachment-viewer-title">${safeTitle}</div>
      <img class="attachment-viewer-image" src="${src}" alt="${safeTitle}">
    `;
    modal.classList.remove("is-hidden");
  }

  function openVideo(src, title) {
    const modal = ensureModal();
    const body = modal.querySelector(".attachment-viewer-body");
    const safeTitle = escapeHtml(title || "Видео");
    body.innerHTML = `
      <div class="attachment-viewer-title">${safeTitle}</div>
      <video class="attachment-viewer-video" controls preload="auto"></video>
    `;
    const video = body.querySelector(".attachment-viewer-video");
    // Load as blob to make seeking more reliable even with limited range support.
    fetch(src)
      .then((r) => {
        if (!r.ok) throw new Error("fetch failed");
        return r.blob();
      })
      .then((blob) => {
        video.src = URL.createObjectURL(blob);
      })
      .catch(() => {
        video.src = src;
      });
    modal.classList.remove("is-hidden");
  }

  function bindAttachments() {
    document.querySelectorAll(".attachment-chip[data-attachment-kind]").forEach((el) => {
      if (el.dataset.viewerBound === "1") return;
      el.dataset.viewerBound = "1";

      el.addEventListener("click", (e) => {
        const kind = el.dataset.attachmentKind;
        const src = el.getAttribute("href");
        const title = el.dataset.attachmentTitle || el.textContent.trim();

        if (!src) return;

        if (kind === "image") {
          e.preventDefault();
          openImage(src, title);
          return;
        }

        if (kind === "video") {
          e.preventDefault();
          openVideo(src, title);
          return;
        }

        // `file` is handled by a dedicated warning page via normal navigation.
      });
    });
  }

  document.addEventListener("DOMContentLoaded", bindAttachments);
})();
