/**
 * api.js — Thin HTTP client for the Flask backend.
 * All network calls live here; nothing else touches fetch().
 */

const Api = (() => {
  const base = CONFIG.API_BASE;

  /** Generic JSON POST */
  async function _post(path, body) {
    const res = await fetch(`${base}${path}`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || json.message || "Request failed");
    return json;
  }

  /** Multipart form POST (file uploads) */
  async function _upload(path, formData) {
    const res = await fetch(`${base}${path}`, {
      method: "POST",
      body  : formData,
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Upload failed");
    return json;
  }

  return {
    /**
     * Verify username and password.
     * @param {string} username
     * @param {string} password
     */
    verifyPassword(username, password) {
      return _post("/auth/verify", { username, password });
    },

    /**
     * Reconcile two Excel / CSV files.
     * @param {File} bankFile
     * @param {File} qbFile
     */
    reconcileExcel(bankFile, qbFile) {
      const fd = new FormData();
      fd.append("bank_file", bankFile);
      fd.append("qb_file",   qbFile);
      return _upload("/reconcile/excel", fd);
    },

    /**
     * Reconcile a PDF bank statement vs a QB Excel file (uses Gemini AI).
     * @param {File} pdfFile
     * @param {File} qbFile
     */
    reconcilePdf(pdfFile, qbFile) {
      const fd = new FormData();
      fd.append("pdf_file", pdfFile);
      fd.append("qb_file",  qbFile);
      return _upload("/reconcile/pdf", fd);
    },

    /**
     * Build the URL to download a generated Excel report.
     * @param {string} filename
     * @returns {string}
     */
    reportUrl(filename) {
      return `${base}/reports/download/${encodeURIComponent(filename)}`;
    },

    /** Health check — resolves true if backend is reachable. */
    async ping() {
      try {
        const res = await fetch(`${base}/health`, { signal: AbortSignal.timeout(3000) });
        return res.ok;
      } catch {
        return false;
      }
    },
  };
})();
