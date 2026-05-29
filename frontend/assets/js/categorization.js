/**
 * categorization.js — Magic Cat AI Categorization Module
 * Handles all UI logic for the Magic Cat screen:
 *   - File upload for batch categorization
 *   - Manual single transaction entry
 *   - Results table with approve / override actions
 *   - Memory learning feedback loop
 *
 * Depends on: CONFIG, Api, State, UI
 */

const MagicCat = (() => {
  /* ── State ──────────────────────────────────────────────────── */
  let _results      = [];   // Current batch results
  let _filtered     = [];   // Search-filtered view
  let _activeTab    = "all";
  let _fileZone     = null;

  /* ── DOM refs ───────────────────────────────────────────────── */
  const $ = id => document.getElementById(id);

  const els = {};

  function _cache() {
    els.screen        = $("screen-magiccat");
    els.uploadZone    = $("mc-upload-zone");
    els.fileInput     = $("mc-file-input");
    els.btnRun        = $("mc-btn-run");
    els.btnClear      = $("mc-btn-clear");
    els.btnApproveAll = $("mc-btn-approve-all");
    els.manualForm    = $("mc-manual-form");
    els.manualDesc    = $("mc-manual-desc");
    els.manualAmount  = $("mc-manual-amount");
    els.manualDate    = $("mc-manual-date");
    els.manualSubmit  = $("mc-manual-submit");
    els.searchInput   = $("mc-search");
    els.tabsBar       = $("mc-tabs");
    els.tableWrap     = $("mc-table-wrap");
    els.statsGrid     = $("mc-stats-grid");
    els.emptyState    = $("mc-empty");
    els.loadingCard   = $("mc-loading");
    els.useAiToggle   = $("mc-use-ai");
  }

  /* ── Upload zone setup ──────────────────────────────────────── */
  function _initUploadZone() {
    const zone  = els.uploadZone;
    const input = els.fileInput;
    if (!zone || !input) return;

    zone.addEventListener("click", () => input.click());
    zone.addEventListener("dragover", e => {
      e.preventDefault();
      zone.classList.add("mc-zone--over");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("mc-zone--over"));
    zone.addEventListener("drop", e => {
      e.preventDefault();
      zone.classList.remove("mc-zone--over");
      const file = e.dataTransfer.files[0];
      if (file) _setFile(file);
    });
    input.addEventListener("change", () => {
      if (input.files[0]) _setFile(input.files[0]);
    });
  }

  let _selectedFile = null;

  function _setFile(file) {
    _selectedFile = file;
    const label = els.uploadZone?.querySelector(".mc-zone__label");
    if (label) label.textContent = `📄 ${file.name}`;
    els.uploadZone?.classList.add("mc-zone--has-file");
  }

  /* ── Run batch categorization ───────────────────────────────── */
  async function _runBatch() {
    if (!_selectedFile) {
      UI.toast("Please upload a CSV or Excel file first.", "warning");
      return;
    }

    const useAi  = els.useAiToggle?.checked !== false;
    const fd     = new FormData();
    fd.append("transactions_file", _selectedFile);
    fd.append("use_ai", useAi ? "true" : "false");

    _setLoading(true, `Analyzing ${_selectedFile.name} with Magic Cat AI…`);

    try {
      const data = await Api.catUpload(fd);
      _results  = data.results || [];
      _renderAll(data);
      UI.toast(`Magic Cat categorized ${data.categorized} transactions.`, "success");
    } catch (err) {
      UI.toast(`Error: ${err.message}`, "error");
    } finally {
      _setLoading(false);
    }
  }

  /* ── Run single manual transaction ─────────────────────────── */
  async function _runManual(e) {
    e.preventDefault();
    const desc   = els.manualDesc?.value?.trim();
    const amount = parseFloat(els.manualAmount?.value);
    const date   = els.manualDate?.value || new Date().toISOString().slice(0, 10);

    if (!desc || isNaN(amount)) {
      UI.toast("Description and amount are required.", "warning");
      return;
    }

    const useAi = els.useAiToggle?.checked !== false;
    _setLoading(true, "Categorizing transaction with Magic Cat…");

    try {
      const result = await Api.catSingle({ date, description: desc, amount, use_ai: useAi });
      _results.unshift(result);
      _renderAll({ results: _results, summary: _computeSummary(_results) });
      UI.toast(`Categorized → ${result.selected_gl_name}`, "success");
      els.manualForm?.reset();
    } catch (err) {
      UI.toast(`Error: ${err.message}`, "error");
    } finally {
      _setLoading(false);
    }
  }

  /* ── Approve a single transaction ───────────────────────────── */
  async function _approve(idx, overriddenGl) {
    const tx = _results[idx];
    if (!tx) return;

    const selectedGl = overriddenGl || tx.selected_gl_code;
    const overridden = !!overriddenGl && overriddenGl !== tx.selected_gl_code;

    try {
      await Api.catApprove({ transaction: tx, selected_gl: selectedGl, overridden });
      _results[idx] = { ...tx, status: "Approved", human_override: overridden, approved_gl: selectedGl };
      _renderTable(_activeTab);
      UI.toast(`Approved — GL ${selectedGl}`, "success");
    } catch (err) {
      UI.toast(`Approve failed: ${err.message}`, "error");
    }
  }

  /* ── Approve all pending ────────────────────────────────────── */
  async function _approveAll() {
    const pending = _results
      .map((r, i) => ({ idx: i, r }))
      .filter(({ r }) => r.status === "Pending Approval");

    if (!pending.length) {
      UI.toast("No pending transactions.", "info");
      return;
    }

    const approvals = pending.map(({ r }) => ({
      transaction: r,
      selected_gl: r.selected_gl_code,
      overridden : false,
    }));

    _setLoading(true, `Approving ${pending.length} transactions…`);
    try {
      await Api.catApproveBulk({ approvals });
      pending.forEach(({ idx }) => {
        _results[idx].status = "Approved";
      });
      _renderTable(_activeTab);
      UI.toast(`${pending.length} transactions approved.`, "success");
    } catch (err) {
      UI.toast(`Bulk approve failed: ${err.message}`, "error");
    } finally {
      _setLoading(false);
    }
  }

  /* ── Render all sections ────────────────────────────────────── */
  function _renderAll(data) {
    _renderStats(data.summary || _computeSummary(data.results || []));
    _renderTabs(data.results || []);
    _renderTable("all");
    if (els.emptyState)
      els.emptyState.style.display = (data.results?.length) ? "none" : "";
  }

  function _computeSummary(results) {
    const avg = results.length
      ? Math.round(results.reduce((s, r) => s + r.confidence, 0) / results.length)
      : 0;
    return {
      avg_confidence : avg,
      high_risk      : results.filter(r => r.risk_level === "High").length,
      medium_risk    : results.filter(r => r.risk_level === "Medium").length,
      low_risk       : results.filter(r => r.risk_level === "Low").length,
      ai_categorized : results.filter(r => r.source === "gemini_ai").length,
      rules_fallback : results.filter(r => r.source !== "gemini_ai").length,
    };
  }

  /* ── Stats grid ─────────────────────────────────────────────── */
  function _renderStats(summary) {
    if (!els.statsGrid) return;
    const stats = [
      { label: "Avg Confidence",  value: `${summary.avg_confidence}%`, icon: "🎯" },
      { label: "High Risk",       value: summary.high_risk,            icon: "🔴" },
      { label: "Medium Risk",     value: summary.medium_risk,          icon: "🟡" },
      { label: "Low Risk",        value: summary.low_risk,             icon: "🟢" },
      { label: "AI Categorized",  value: summary.ai_categorized,       icon: "🤖" },
      { label: "Rules Fallback",  value: summary.rules_fallback,       icon: "📏" },
    ];
    els.statsGrid.innerHTML = stats.map(s => `
      <div class="stat-card pop-in">
        <div class="stat-card__icon">${s.icon}</div>
        <div class="stat-card__body">
          <div class="stat-card__value">${s.value}</div>
          <div class="stat-card__label">${s.label}</div>
        </div>
      </div>
    `).join("");
  }

  /* ── Tabs ───────────────────────────────────────────────────── */
  function _renderTabs(results) {
    if (!els.tabsBar) return;
    const tabs = [
      { key: "all",      label: "All",        count: results.length },
      { key: "pending",  label: "Pending",    count: results.filter(r => r.status === "Pending Approval").length },
      { key: "approved", label: "Approved",   count: results.filter(r => r.status === "Approved").length },
      { key: "high",     label: "High Risk",  count: results.filter(r => r.risk_level === "High").length },
    ];

    els.tabsBar.innerHTML = tabs.map(t => `
      <button class="tab-btn ${_activeTab === t.key ? "tab-btn--active" : ""}"
              data-tab="${t.key}">
        ${t.label}
        <span class="tab-badge">${t.count}</span>
      </button>
    `).join("");

    els.tabsBar.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        _activeTab = btn.dataset.tab;
        els.tabsBar.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("tab-btn--active"));
        btn.classList.add("tab-btn--active");
        _renderTable(_activeTab);
      });
    });
  }

  /* ── Results table ──────────────────────────────────────────── */
  function _renderTable(tab) {
    if (!els.tableWrap) return;

    const query = (els.searchInput?.value || "").toLowerCase();
    let rows = _results.filter(r => {
      if (tab === "pending")  return r.status === "Pending Approval";
      if (tab === "approved") return r.status === "Approved";
      if (tab === "high")     return r.risk_level === "High";
      return true;
    });

    if (query) {
      rows = rows.filter(r =>
        r.description.toLowerCase().includes(query) ||
        r.selected_gl_name.toLowerCase().includes(query) ||
        r.ifrs_reference?.toLowerCase().includes(query)
      );
    }

    _filtered = rows;

    if (!rows.length) {
      els.tableWrap.innerHTML = `
        <div class="mc-empty-tab">No transactions in this view.</div>
      `;
      return;
    }

    els.tableWrap.innerHTML = `
      <table class="mc-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>GL Account</th>
            <th>Statement</th>
            <th>IFRS/IAS</th>
            <th>Confidence</th>
            <th>Risk</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((r, i) => _rowHtml(r, _results.indexOf(r))).join("")}
        </tbody>
      </table>
    `;

    /* Wire action buttons */
    els.tableWrap.querySelectorAll("[data-approve]").forEach(btn => {
      btn.addEventListener("click", () => _approve(parseInt(btn.dataset.approve)));
    });

    els.tableWrap.querySelectorAll("[data-detail]").forEach(btn => {
      btn.addEventListener("click", () => _showDetail(parseInt(btn.dataset.detail)));
    });
  }

  function _rowHtml(r, idx) {
    const riskClass = {
      High   : "badge--danger",
      Medium : "badge--warning",
      Low    : "badge--success",
    }[r.risk_level] || "badge--info";

    const statusClass = r.status === "Approved" ? "badge--success" : "badge--warning";
    const amt = r.amount >= 0 ? `+$${r.amount.toFixed(2)}` : `-$${Math.abs(r.amount).toFixed(2)}`;
    const amtClass = r.amount >= 0 ? "mc-amt--credit" : "mc-amt--debit";

    return `
      <tr class="mc-row ${r.status === "Approved" ? "mc-row--approved" : ""}">
        <td class="mc-date">${r.date || "—"}</td>
        <td class="mc-desc" title="${r.description}">${_truncate(r.description, 35)}</td>
        <td class="mc-amt ${amtClass}">${amt}</td>
        <td class="mc-gl">
          <span class="mc-gl-code">${r.selected_gl_code}</span>
          <span class="mc-gl-name">${r.selected_gl_name}</span>
        </td>
        <td><span class="badge badge--info">${r.statement}</span></td>
        <td class="mc-ifrs">${r.ifrs_reference?.split("—")[0]?.trim() || "—"}</td>
        <td>
          <div class="mc-conf">
            <div class="mc-conf__bar" style="--pct:${r.confidence}%;--clr:${_confColor(r.confidence)}"></div>
            <span>${r.confidence}%</span>
          </div>
        </td>
        <td><span class="badge ${riskClass}">${r.risk_level}</span></td>
        <td><span class="badge ${statusClass}">${r.status === "Approved" ? "✓ Approved" : "⏳ Pending"}</span></td>
        <td class="mc-actions">
          <button class="btn btn--xs btn--ghost" data-detail="${idx}" title="View Details">🔍</button>
          ${r.status !== "Approved"
            ? `<button class="btn btn--xs btn--primary" data-approve="${idx}">✓ Approve</button>`
            : ""}
        </td>
      </tr>
    `;
  }

  /* ── Detail modal ───────────────────────────────────────────── */
  function _showDetail(idx) {
    const r = _results[idx];
    if (!r) return;

    const alts = (r.top3_gl || []).map((g, i) => `
      <div class="mc-alt ${i === 0 ? "mc-alt--primary" : ""}">
        <span class="mc-alt__rank">#${g.rank || i+1}</span>
        <span class="mc-alt__code">${g.gl_code}</span>
        <span class="mc-alt__name">${g.gl_name}</span>
        ${i !== 0 ? `<button class="btn btn--xs btn--ghost mc-alt__pick"
          data-idx="${idx}" data-gl="${g.gl_code}"
          title="Use this GL">Use</button>` : ""}
      </div>
    `).join("");

    const modal = document.createElement("div");
    modal.className = "mc-modal-overlay";
    modal.innerHTML = `
      <div class="mc-modal pop-in" role="dialog">
        <div class="mc-modal__header">
          <h3>🔍 Transaction Detail</h3>
          <button class="mc-modal__close">✕</button>
        </div>
        <div class="mc-modal__body">
          <div class="mc-detail-grid">
            <div class="mc-detail-row"><span>Date</span><strong>${r.date || "—"}</strong></div>
            <div class="mc-detail-row"><span>Description</span><strong>${r.description}</strong></div>
            <div class="mc-detail-row"><span>Amount</span><strong>${r.amount >= 0 ? "+" : ""}$${r.amount.toFixed(2)} ${r.currency}</strong></div>
            <div class="mc-detail-row"><span>Selected GL</span><strong>${r.selected_gl_code} — ${r.selected_gl_name}</strong></div>
            <div class="mc-detail-row"><span>Statement</span><strong>${r.statement}</strong></div>
            <div class="mc-detail-row"><span>IFRS/IAS Reference</span><strong>${r.ifrs_reference}</strong></div>
            <div class="mc-detail-row"><span>Confidence</span><strong>${r.confidence}%</strong></div>
            <div class="mc-detail-row"><span>Risk Level</span><strong>${r.risk_level}</strong></div>
            <div class="mc-detail-row"><span>Source</span><strong>${r.source === "gemini_ai" ? "🤖 Gemini AI" : "📏 Rules Engine"}</strong></div>
            ${r.rules_hit ? '<div class="mc-detail-row"><span>IFRS Rule Hit</span><strong>✅ Yes</strong></div>' : ""}
            ${r.memory_hit ? '<div class="mc-detail-row"><span>Memory Match</span><strong>🧠 Yes — company history used</strong></div>' : ""}
          </div>

          <div class="mc-detail-section">
            <h4>CPA Reasoning</h4>
            <p class="mc-reasoning">${r.reasoning || "—"}</p>
          </div>

          ${r.risk_notes ? `
          <div class="mc-detail-section">
            <h4>Risk Notes</h4>
            <p class="mc-reasoning mc-reasoning--risk">${r.risk_notes}</p>
          </div>` : ""}

          ${r.accrual_note ? `
          <div class="mc-detail-section">
            <h4>Accrual / Prepaid Note</h4>
            <p class="mc-reasoning">${r.accrual_note}</p>
          </div>` : ""}

          ${r.tax_note ? `
          <div class="mc-detail-section">
            <h4>Tax Note</h4>
            <p class="mc-reasoning">${r.tax_note}</p>
          </div>` : ""}

          <div class="mc-detail-section">
            <h4>GL Alternatives (Top 3)</h4>
            <div class="mc-alts">${alts || "<p>No alternatives available.</p>"}</div>
          </div>

          ${r.status !== "Approved" ? `
          <div class="mc-detail-actions">
            <button class="btn btn--primary mc-modal-approve" data-idx="${idx}">
              ✓ Approve with Selected GL
            </button>
          </div>` : `
          <div class="mc-detail-actions">
            <span class="badge badge--success">✓ Approved</span>
            ${r.human_override ? '<span class="badge badge--warning">Human Override</span>' : ""}
          </div>`}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector(".mc-modal__close").addEventListener("click", () => modal.remove());
    modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });

    // Approve from modal
    modal.querySelector(".mc-modal-approve")?.addEventListener("click", async () => {
      modal.remove();
      await _approve(idx);
    });

    // Override with alternate GL
    modal.querySelectorAll(".mc-alt__pick").forEach(btn => {
      btn.addEventListener("click", async () => {
        modal.remove();
        await _approve(parseInt(btn.dataset.idx), btn.dataset.gl);
      });
    });
  }

  /* ── Loading state ──────────────────────────────────────────── */
  function _setLoading(active, message = "Magic Cat is thinking…") {
    if (els.loadingCard) {
      els.loadingCard.style.display = active ? "" : "none";
      const msg = els.loadingCard.querySelector(".mc-loading__msg");
      if (msg) msg.textContent = message;
    }
  }

  /* ── Helpers ────────────────────────────────────────────────── */
  function _truncate(str, max) {
    return str.length > max ? str.slice(0, max) + "…" : str;
  }

  function _confColor(pct) {
    if (pct >= 80) return "var(--clr-success)";
    if (pct >= 60) return "var(--clr-warning)";
    return "var(--clr-danger)";
  }

  /* ── Public init ────────────────────────────────────────────── */
  function init() {
    _cache();
    _initUploadZone();

    els.btnRun?.addEventListener("click", _runBatch);
    els.btnClear?.addEventListener("click", () => {
      _results = [];
      _filtered = [];
      _selectedFile = null;
      _activeTab = "all";
      if (els.tableWrap)     els.tableWrap.innerHTML = "";
      if (els.statsGrid)     els.statsGrid.innerHTML = "";
      if (els.tabsBar)       els.tabsBar.innerHTML = "";
      if (els.emptyState)    els.emptyState.style.display = "";
      const label = els.uploadZone?.querySelector(".mc-zone__label");
      if (label) label.textContent = "Drop your CSV / Excel file here, or click to browse";
      els.uploadZone?.classList.remove("mc-zone--has-file");
    });

    els.btnApproveAll?.addEventListener("click", _approveAll);
    els.manualForm?.addEventListener("submit", _runManual);
    els.searchInput?.addEventListener("input", () => _renderTable(_activeTab));
  }

  return { init };
})();


/* ── API Extensions for Magic Cat ───────────────────────────── */
(function () {
  const base = CONFIG.API_BASE;

  async function _upload(path, formData) {
    const res  = await fetch(`${base}${path}`, { method: "POST", body: formData });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Upload failed");
    return json;
  }

  async function _post(path, body) {
    const res  = await fetch(`${base}${path}`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Request failed");
    return json;
  }

  Api.catUpload       = fd   => _upload("/categorize/upload", fd);
  Api.catSingle       = body => _post("/categorize/single", body);
  Api.catApprove      = body => _post("/categorize/approve", body);
  Api.catApproveBulk  = body => _post("/categorize/approve/bulk", body);
  Api.catHistory      = ()   => fetch(`${base}/categorize/history`).then(r => r.json());
  Api.catCoa          = ()   => fetch(`${base}/categorize/coa`).then(r => r.json());
})();
