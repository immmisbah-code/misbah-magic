/**
 * results.js — Renders reconciliation results into the dashboard.
 *
 * Depends on: State, UI
 */

const Results = (() => {
  /* ── Column configs per tab ─────────────────────────────── */
  const TAB_CONFIG = {
    matched: {
      label  : "Matched",
      badge  : "badge--success",
      columns: ["Date", "Description", "Bank Amount", "QB Amount", "Similarity"],
      map    : r => [r.date, r.description, _money(r.bank_amount), _money(r.qb_amount), _pct(r.similarity)],
    },
    missing_in_qb: {
      label  : "Missing in QB",
      badge  : "badge--warning",
      columns: ["Date", "Description", "Amount", "Note"],
      map    : r => [r.date, r.description, _money(r.amount), "Not found in QuickBooks"],
    },
    missing_in_bank: {
      label  : "Missing in Bank",
      badge  : "badge--info",
      columns: ["Date", "Description", "Amount", "Note"],
      map    : r => [r.date, r.description, _money(r.amount), "Not found in bank statement"],
    },
    discrepancies: {
      label  : "Discrepancies",
      badge  : "badge--danger",
      columns: ["Date", "Description", "Bank Amount", "QB Amount", "Difference"],
      map    : r => [r.date, r.description, _money(r.bank_amount), _money(r.qb_amount), _money(r.difference)],
    },
    duplicates: {
      label  : "Duplicates",
      badge  : "badge--warning",
      columns: ["Date", "Description", "Amount", "Occurrences"],
      map    : r => [r.date, r.description, _money(r.amount), r.occurrences ?? "—"],
    },
  };

  /* ── Formatters ─────────────────────────────────────────── */
  function _money(v) {
    if (v == null || v === "") return "—";
    const n = parseFloat(v);
    if (isNaN(n)) return v;
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
  }

  function _pct(v) {
    if (v == null) return "—";
    return `${(parseFloat(v) * 100).toFixed(0)}%`;
  }

  /* ── Internal references ────────────────────────────────── */
  const _els = {};

  function _cache() {
    _els.statsGrid   = document.getElementById("stats-grid");
    _els.tabsBar     = document.getElementById("results-tabs");
    _els.tableWrap   = document.getElementById("table-wrap");
    _els.searchInput = document.getElementById("search-input");
    _els.emptyState  = document.getElementById("empty-state");
    _els.downloadBtn = document.getElementById("btn-download");
    _els.resultsView = document.getElementById("results-section");
  }

  /* ── Stats cards ─────────────────────────────────────────── */
  function _renderStats(summary) {
    if (!_els.statsGrid) return;

    const stats = [
      { key: "total",           label: "Total Transactions", icon: "📊" },
      { key: "matched",         label: "Matched",            icon: "✅" },
      { key: "missing_in_qb",   label: "Missing in QB",      icon: "⚠️"  },
      { key: "missing_in_bank", label: "Missing in Bank",    icon: "🏦" },
      { key: "discrepancies",   label: "Discrepancies",      icon: "🔍" },
      { key: "duplicates",      label: "Duplicates",         icon: "🔁" },
    ];

    _els.statsGrid.innerHTML = stats.map(({ key, label, icon }) => `
      <div class="stat-card pop-in">
        <div class="stat-card__icon">${icon}</div>
        <div class="stat-card__body">
          <div class="stat-card__value count-up" data-key="${key}">
            ${summary[key] ?? 0}
          </div>
          <div class="stat-card__label">${label}</div>
        </div>
      </div>
    `).join("");

    /* Animate each counter */
    _els.statsGrid.querySelectorAll(".stat-card__value").forEach(el => {
      const target = parseInt(el.textContent, 10) || 0;
      el.textContent = "0";
      UI.animateCount(el, target);
    });
  }

  /* ── Tab bar ─────────────────────────────────────────────── */
  function _renderTabs(data) {
    if (!_els.tabsBar) return;

    _els.tabsBar.innerHTML = Object.entries(TAB_CONFIG).map(([key, cfg]) => {
      const count = (data[key] || []).length;
      return `
        <button class="tab-btn ${State.get("activeTab") === key ? "active" : ""}"
                data-tab="${key}">
          ${cfg.label}
          <span class="tab-badge ${cfg.badge}">${count}</span>
        </button>
      `;
    }).join("");

    _els.tabsBar.addEventListener("click", e => {
      const btn = e.target.closest("[data-tab]");
      if (!btn) return;
      State.setState({ activeTab: btn.dataset.tab, searchQuery: "" });
      if (_els.searchInput) _els.searchInput.value = "";
    });
  }

  /* ── Data table ─────────────────────────────────────────── */
  function _renderTable(data, tabKey, query = "") {
    if (!_els.tableWrap) return;

    const cfg  = TAB_CONFIG[tabKey];
    if (!cfg) return;

    let rows = data[tabKey] || [];

    /* Search filter */
    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(r =>
        Object.values(r).some(v => String(v).toLowerCase().includes(q))
      );
    }

    if (rows.length === 0) {
      _els.tableWrap.innerHTML = "";
      if (_els.emptyState) _els.emptyState.style.display = "";
      return;
    }
    if (_els.emptyState) _els.emptyState.style.display = "none";

    const thead = `<tr>${cfg.columns.map(c => `<th>${c}</th>`).join("")}</tr>`;
    const tbody = rows.map(r => {
      const cells = cfg.map(r).map(v => `<td>${UI.escHtml(String(v ?? "—"))}</td>`).join("");
      return `<tr>${cells}</tr>`;
    }).join("");

    _els.tableWrap.innerHTML = `
      <div class="table-scroll fade-in">
        <table class="data-table">
          <thead>${thead}</thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>
      <p class="table-footer text-xs text-muted">
        ${rows.length.toLocaleString()} record${rows.length !== 1 ? "s" : ""}
        ${query ? ` matching "${UI.escHtml(query)}"` : ""}
      </p>
    `;
  }

  /* ── Public: render full results ─────────────────────────── */
  function render(data) {
    _cache();
    if (!data) return;

    const summary = data.summary || {};

    _renderStats(summary);
    _renderTabs(data);
    _renderTable(data, State.get("activeTab"), State.get("searchQuery"));

    /* Show results section */
    if (_els.resultsView) _els.resultsView.style.display = "";

    /* Subscribe to tab + search changes to re-render table */
    State.subscribe(["activeTab", "searchQuery"], () => {
      _renderTabs(data);
      _renderTable(data, State.get("activeTab"), State.get("searchQuery"));
    });
  }

  /* ── Public: clear results ───────────────────────────────── */
  function clear() {
    _cache();
    if (_els.statsGrid)   _els.statsGrid.innerHTML   = "";
    if (_els.tabsBar)     _els.tabsBar.innerHTML     = "";
    if (_els.tableWrap)   _els.tableWrap.innerHTML   = "";
    if (_els.resultsView) _els.resultsView.style.display = "none";
  }

  return { render, clear };
})();
