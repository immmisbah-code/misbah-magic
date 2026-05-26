/**
 * Misbah's Magic — API Client
 * Handles all communication with the Python Flask backend.
 */

const API_BASE = "http://localhost:5000/api";

const Api = {

  /**
   * Verify access password
   * @param {string} password
   * @returns {Promise<{success: boolean}>}
   */
  async verifyPassword(password) {
    const res = await fetch(`${API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    return res.json();
  },

  /**
   * Reconcile two Excel/CSV files
   * @param {File} bankFile
   * @param {File} qbFile
   * @returns {Promise<object>} reconciliation result
   */
  async reconcileExcel(bankFile, qbFile) {
    const form = new FormData();
    form.append("bank_file", bankFile);
    form.append("qb_file", qbFile);

    const res = await fetch(`${API_BASE}/reconcile/excel`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Reconciliation failed");
    }

    return res.json();
  },

  /**
   * Reconcile PDF bank statement + QuickBooks Excel using Gemini AI
   * @param {File} pdfFile
   * @param {File} qbFile
   * @returns {Promise<object>} reconciliation result
   */
  async reconcilePdf(pdfFile, qbFile) {
    const form = new FormData();
    form.append("pdf_file", pdfFile);
    form.append("qb_file", qbFile);

    const res = await fetch(`${API_BASE}/reconcile/pdf`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "PDF reconciliation failed");
    }

    return res.json();
  },

  /**
   * Get URL to download generated report
   * @param {string} filename
   * @returns {string} download URL
   */
  getDownloadUrl(filename) {
    return `${API_BASE}/download/${filename}`;
  },

  /**
   * Health check
   * @returns {Promise<boolean>}
   */
  async ping() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return res.ok;
    } catch {
      return false;
    }
  },
};
