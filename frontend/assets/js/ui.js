/**
 * ui.js — DOM helpers, toast system, progress bar, screen transitions.
 * All direct DOM manipulation lives here.
 */

const UI = (() => {
  /* ── Toast container (injected once) ─────────────────────── */
  let _toastContainer = null;

  function _getToastContainer() {
    if (!_toastContainer) {
      _toastContainer = document.createElement("div");
      _toastContainer.id = "toast-container";
      _toastContainer.setAttribute("aria-live", "polite");
      document.body.appendChild(_toastContainer);
    }
    return _toastContainer;
  }

  /**
   * Show a toast notification.
   * @param {string} message
   * @param {"success"|"error"|"info"|"warning"} type
   * @param {number} duration  ms before auto-dismiss (0 = sticky)
   */
  function toast(message, type = "info", duration = CONFIG.TOAST_TIMEOUT) {
    const icons = {
      success: "✓",
      error  : "✕",
      warning: "⚠",
      info   : "ℹ",
    };

    const el = document.createElement("div");
    el.className = `toast toast--${type} fade-in`;
    el.innerHTML = `
      <span class="toast__icon">${icons[type] || icons.info}</span>
      <span class="toast__msg">${message}</span>
      <button class="toast__close" aria-label="Dismiss">✕</button>
    `;

    const dismiss = () => {
      el.classList.add("toast--out");
      el.addEventListener("animationend", () => el.remove(), { once: true });
    };

    el.querySelector(".toast__close").addEventListener("click", dismiss);
    _getToastContainer().appendChild(el);

    if (duration > 0) setTimeout(dismiss, duration);
    return dismiss;
  }

  /* ── Screen transitions ───────────────────────────────────── */

  /**
   * Activate a screen by ID; deactivate all others.
   * @param {string} id  — e.g. "screen-login" | "screen-dashboard"
   */
  function showScreen(id) {
    document.querySelectorAll(".screen").forEach(s => {
      s.classList.toggle("active", s.id === id);
    });
  }

  /* ── Progress bar ─────────────────────────────────────────── */
  let _progressEl = null;
  let _progressTimer = null;

  function _getProgress() {
    if (!_progressEl) _progressEl = document.getElementById("progress-bar");
    return _progressEl;
  }

  function showProgress(pct = 0) {
    const bar = _getProgress();
    if (!bar) return;
    bar.style.width   = `${Math.min(pct, 100)}%`;
    bar.style.opacity = "1";
  }

  function tickProgress(targetPct = 85, stepMs = 300) {
    let current = 0;
    clearInterval(_progressTimer);
    _progressTimer = setInterval(() => {
      current = Math.min(current + Math.random() * 6, targetPct);
      showProgress(current);
    }, stepMs);
  }

  function finishProgress() {
    clearInterval(_progressTimer);
    showProgress(100);
    setTimeout(() => {
      const bar = _getProgress();
      if (bar) bar.style.opacity = "0";
      setTimeout(() => showProgress(0), 400);
    }, 500);
  }

  /* ── Loading overlay ─────────────────────────────────────── */
  function setLoading(isLoading, label = "Processing…") {
    const overlay = document.getElementById("loading-overlay");
    const msg     = document.getElementById("loading-message");
    if (!overlay) return;
    if (msg) msg.textContent = label;
    overlay.classList.toggle("active", isLoading);
    if (isLoading) tickProgress(80);
    else           finishProgress();
  }

  /* ── Stat counters ───────────────────────────────────────── */

  /**
   * Animate a counter from 0 to value.
   * @param {HTMLElement} el
   * @param {number}      value
   */
  function animateCount(el, value) {
    if (!el) return;
    const duration = 600;
    const start    = performance.now();
    const from     = parseInt(el.textContent, 10) || 0;

    const step = now => {
      const t = Math.min((now - start) / duration, 1);
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      el.textContent = Math.round(from + (value - from) * ease);
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  /* ── Generic helpers ─────────────────────────────────────── */

  /** Set visibility (display none / block). */
  function show(el, visible = true) {
    if (!el) return;
    el.style.display = visible ? "" : "none";
  }

  /** Toggle a class on an element. */
  function toggleClass(el, cls, force) {
    if (!el) return;
    el.classList.toggle(cls, force);
  }

  /** Remove all children from a node. */
  function empty(el) {
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  /** Create an element with optional attrs / text. */
  function el(tag, attrs = {}, text = "") {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    if (text) node.textContent = text;
    return node;
  }

  /** Escape HTML special chars (for safe innerHTML injection). */
  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  return {
    toast,
    showScreen,
    showProgress,
    tickProgress,
    finishProgress,
    setLoading,
    animateCount,
    show,
    toggleClass,
    empty,
    el,
    escHtml,
  };
})();
