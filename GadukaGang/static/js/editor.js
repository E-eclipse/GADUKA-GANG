window.PCHEditor = window.PCHEditor || {
  createQuill: function (selector, options) {
    if (!window.Quill) return null;
    const host = document.querySelector(selector);
    if (!host) return null;
    return new Quill(selector, options || { theme: "snow" });
  }
};

