/**
 * uploader.js — Drag-and-drop + click-to-browse file upload zones.
 *
 * Usage:
 *   const zone = Uploader.create({
 *     zoneId   : "zone-bank",
 *     accept   : [".xlsx", ".xls", ".csv"],
 *     label    : "Bank Statement",
 *     onFile   : (file) => State.setState({ bankFile: file }),
 *   });
 */

const Uploader = (() => {
  const ICONS = {
    excel: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="8" y1="13" x2="16" y2="13"/>
              <line x1="8" y1="17" x2="16" y2="17"/>
            </svg>`,
    pdf  : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <path d="M9 15h6M9 18h4"/>
            </svg>`,
    any  : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>`,
  };

  function _iconFor(accept) {
    if (!accept) return ICONS.any;
    const ext = accept.join(" ");
    if (/pdf/i.test(ext))   return ICONS.pdf;
    if (/xlsx|xls|csv/i.test(ext)) return ICONS.excel;
    return ICONS.any;
  }

  function _formatSize(bytes) {
    if (bytes < 1024)        return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  /**
   * Create an upload zone.
   * @param {{zoneId:string, accept:string[], label:string, onFile:function}} opts
   * @returns {{ getFile: function, reset: function }}
   */
  function create({ zoneId, accept = [], label = "File", onFile }) {
    const zone = document.getElementById(zoneId);
    if (!zone) { console.warn(`Uploader: #${zoneId} not found`); return {}; }

    let _file = null;
    const icon    = _iconFor(accept);
    const extList = accept.map(e => e.replace(".", "").toUpperCase()).join(", ");

    /* ── Render initial UI ── */
    zone.innerHTML = `
      <div class="upload-zone__inner">
        <div class="upload-zone__icon">${icon}</div>
        <p class="upload-zone__label">
          <strong>${label}</strong>
        </p>
        <p class="upload-zone__hint">
          Drag &amp; drop or <span class="upload-zone__browse">browse</span>
        </p>
        <p class="upload-zone__ext text-xs text-muted">${extList}</p>
      </div>
      <div class="upload-zone__file" style="display:none">
        <div class="upload-zone__file-icon">${icon}</div>
        <div class="upload-zone__file-info">
          <span class="upload-zone__file-name"></span>
          <span class="upload-zone__file-size text-xs text-muted"></span>
        </div>
        <button class="upload-zone__remove" aria-label="Remove file">✕</button>
      </div>
      <input type="file" class="upload-zone__input" accept="${accept.join(",")}" style="display:none">
    `;

    const inner  = zone.querySelector(".upload-zone__inner");
    const fileEl = zone.querySelector(".upload-zone__file");
    const nameEl = zone.querySelector(".upload-zone__file-name");
    const sizeEl = zone.querySelector(".upload-zone__file-size");
    const input  = zone.querySelector(".upload-zone__input");
    const browse = zone.querySelector(".upload-zone__browse");
    const remove = zone.querySelector(".upload-zone__remove");

    /* ── Accept a file ── */
    function _accept(file) {
      if (!file) return;

      /* Validate extension */
      if (accept.length) {
        const ok = accept.some(ext => file.name.toLowerCase().endsWith(ext));
        if (!ok) {
          UI.toast(`Invalid file type. Accepted: ${extList}`, "error");
          return;
        }
      }

      _file = file;
      nameEl.textContent = file.name;
      sizeEl.textContent = _formatSize(file.size);
      inner.style.display  = "none";
      fileEl.style.display = "";
      zone.classList.add("upload-zone--filled");
      if (onFile) onFile(file);
    }

    /* ── Reset ── */
    function reset() {
      _file = null;
      input.value = "";
      inner.style.display  = "";
      fileEl.style.display = "none";
      zone.classList.remove("upload-zone--filled", "upload-zone--drag");
      if (onFile) onFile(null);
    }

    /* ── Events ── */
    browse.addEventListener("click", () => input.click());
    zone.addEventListener("click", e => {
      if (e.target === zone || e.target === inner) input.click();
    });

    input.addEventListener("change", () => {
      if (input.files[0]) _accept(input.files[0]);
    });

    remove.addEventListener("click", e => {
      e.stopPropagation();
      reset();
    });

    zone.addEventListener("dragover", e => {
      e.preventDefault();
      zone.classList.add("upload-zone--drag");
    });

    zone.addEventListener("dragleave", () => {
      zone.classList.remove("upload-zone--drag");
    });

    zone.addEventListener("drop", e => {
      e.preventDefault();
      zone.classList.remove("upload-zone--drag");
      const file = e.dataTransfer?.files?.[0];
      if (file) _accept(file);
    });

    return {
      getFile: () => _file,
      reset,
    };
  }

  return { create };
})();
