/**
 * Misbah's Magic — Main Application Logic
 * Handles UI state, file uploads, and results rendering.
 */

// ── State ──────────────────────────────────────────────────────────
const state = {
  mode: "excel",          // "excel" | "pdf"
  bankFile: null,
  qbFile: null,
  result: null,
  activeTab: "matched",
  searchQuery: "",
};

// ── DOM Helpers ─────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function showScreen(id) {
  $$(".screen").forEach((s) => s.classList.remove("active"));
  $(`#${id}`).classList.add("active");
}

function showAlert(msg, type = "error") {
  const el = $("#error-alert");
  el.textContent = msg;
  el.className = `alert alert-${type}`;
  el.style.display = "flex";
  setTimeout(() => (el.style.display = "none"), 6000);
}

function setProgress(pct, label = "") {
  const wrap = $(".progress-wrap");
  wrap.classList.add("visible");
  $(".progress-bar-fill").style.width = `${pct}%`;
  $(".progress-label span:last-child").textContent = `${pct}%`;
  if (label) $(".progress-label span:first-child").textContent = label;
}

function hideProgress() {
  $(".progress-wrap").classList.remove("visible");
  $(".progress-bar-fill").style.width = "0%";
}

// ── Auth ────────────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const password = $("#password-input").value.trim();
  const btn = $("#login-btn");

  if (!password) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Verifying...';

  try {
    const res = await Api.verifyPassword(password);
    if (res.success) {
      showScreen("app-screen");
    } else {
      showAlert("Incorrect password. Please try again.", "error");
    }
  } catch {
    showAlert("Cannot connect to server. Is the backend running?", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔓 Access Dashboard";
  }
}

function handleLogout() {
  state.result = null;
  state.bankFile = null;
  state.qbFile = null;
  resetUploadUI();
  showScreen("login-screen");
}

// ── Mode Toggle ─────────────────────────────────────────────────────
function setMode(mode) {
  state.mode = mode;
  $$(".mode-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });

  if (mode === "excel") {
    $("#bank-upload-label").textContent = "Bank Statement (Excel/CSV)";
    $("#bank-upload-hint").textContent = "Supports .xlsx, .xls, .csv";
    $("#bank-file-input").accept = ".xlsx,.xls,.csv";
  } else {
    $("#bank-upload-label").textContent = "Bank Statement (PDF)";
    $("#bank-upload-hint").textContent = "AI will extract transactions via Gemini";
    $("#bank-file-input").accept = ".pdf";
  }

  // Reset files if mode changes
  state.bankFile = null;
  state.qbFile = null;
  resetUploadUI();
}

// ── File Upload ─────────────────────────────────────────────────────
function initUpload(inputId, areaId, filenameId, stateKey) {
  const input = $(`#${inputId}`);
  const area = $(`#${areaId}`);
  const nameEl = $(`#${filenameId}`);

  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;
    state[stateKey] = file;
    area.classList.add("has-file");
    nameEl.textContent = `✅ ${file.name}`;
  });

  area.addEventListener("dragover", (e) => {
    e.preventDefault();
    area.classList.add("dragover");
  });

  area.addEventListener("dragleave", () => area.classList.remove("dragover"));

  area.addEventListener("drop", (e) => {
    e.preventDefault();
    area.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (!file) return;
    state[stateKey] = file;
    area.classList.add("has-file");
    nameEl.textContent = `✅ ${file.name}`;
  });
}

function resetUploadUI() {
  ["#bank-upload-area", "#qb-upload-area"].forEach((sel) => {
    $(sel).classList.remove("has-file");
  });
  ["#bank-filename", "#qb-filename"].forEach((sel) => {
    $(sel).textContent = "";
  });
  $("#bank-file-input").value = "";
  $("#qb-file-input").value = "";
  hideProgress();
  $("#error-alert").style.display = "none";
}

// ── Reconcile ───────────────────────────────────────────────────────
async function handleReconcile() {
  if (!state.bankFile) return showAlert("Please upload a Bank Statement file.");
  if (!state.qbFile) return showAlert("Please upload a QuickBooks file.");

  const btn = $("#reconcile-btn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Processing...';

  setProgress(10, "Reading files...");

  try {
    let result;
    setProgress(30, "Sending to server...");

    if (state.mode === "excel") {
      result = await Api.reconcileExcel(state.bankFile, state.qbFile);
    } else {
      setProgress(40, "Extracting PDF via Gemini AI...");
      result = await Api.reconcilePdf(state.bankFile, state.qbFile);
    }

    setProgress(80, "Matching transactions...");
    state.result = result;
    setProgress(100, "Done!");

    setTimeout(() => {
      hideProgress();
      renderResults(result);
    }, 600);

  } catch (err) {
    hideProgress();
    showAlert(err.message || "An error occurred during reconciliation.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "▶ Run Reconciliation";
  }
}

// ── Results ─────────────────────────────────────────────────────────
function renderResults(result) {
  const summary = result.summary;

  // Stats
  $("#stat-matched").textContent    = summary.matched_count;
  $("#stat-missing-qb").textContent = summary.missing_in_qb_count;
  $("#stat-missing-bank").textContent = summary.missing_in_bank_count;
  $("#stat-duplicates").textContent = summary.duplicates_count;
  $("#stat-discrepancies").textContent = summary.discrepancies_count;

  // Tab badges
  $("#badge-matched").textContent      = summary.matched_count;
  $("#badge-missing-qb").textContent   = summary.missing_in_qb_count;
  $("#badge-missing-bank").textContent = summary.missing_in_bank_count;
  $("#badge-duplicates").textContent   = summary.duplicates_count;
  $("#badge-discrepancies").textContent = summary.discrepancies_count;

  // Show download button
  if (result.report_filename) {
    const dlBtn = $("#download-btn");
    dlBtn.style.display = "inline-flex";
    dlBtn.onclick = () => {
      window.location.href = Api.getDownloadUrl(result.report_filename);
    };
  }

  // Render tables
  renderTab("matched");

  // Scroll to results
  $("#results-section").scrollIntoView({ behavior: "smooth" });
}

function renderTab(tabName) {
  state.activeTab = tabName;
  const result = state.result;
  if (!result) return;

  const query = state.searchQuery.toLowerCase();

  switch (tabName) {
    case "matched":
      renderTable(
        "#table-matched",
        ["Bank Description", "QB Description", "Bank Date", "QB Date", "Bank Amount ($)", "QB Amount ($)", "Similarity"],
        result.matched.filter((r) =>
          !query || r.bank_description.toLowerCase().includes(query) || r.qb_description.toLowerCase().includes(query)
        ),
        (r) => [
          r.bank_description, r.qb_description,
          r.bank_date, r.qb_date,
          formatAmount(r.bank_amount), formatAmount(r.qb_amount),
          `<span class="badge badge-green">${r.similarity}%</span>`,
        ]
      );
      break;

    case "missing-qb":
      renderTable(
        "#table-missing-qb",
        ["Description", "Date", "Amount ($)"],
        result.missing_in_qb.filter((r) =>
          !query || r.description.toLowerCase().includes(query)
        ),
        (r) => [r.description, r.date, formatAmount(r.amount)]
      );
      break;

    case "missing-bank":
      renderTable(
        "#table-missing-bank",
        ["Description", "Date", "Amount ($)"],
        result.missing_in_bank.filter((r) =>
          !query || r.description.toLowerCase().includes(query)
        ),
        (r) => [r.description, r.date, formatAmount(r.amount)]
      );
      break;

    case "duplicates":
      renderTable(
        "#table-duplicates",
        ["Description", "Date", "Amount ($)"],
        result.duplicates.filter((r) =>
          !query || r.description.toLowerCase().includes(query)
        ),
        (r) => [r.description, r.date, formatAmount(r.amount)]
      );
      break;

    case "discrepancies":
      renderTable(
        "#table-discrepancies",
        ["Bank Description", "QB Description", "Bank Date", "QB Date", "Bank Amount ($)", "QB Amount ($)", "Difference ($)"],
        result.discrepancies.filter((r) =>
          !query || r.bank_description.toLowerCase().includes(query)
        ),
        (r) => [
          r.bank_description, r.qb_description,
          r.bank_date, r.qb_date,
          formatAmount(r.bank_amount), formatAmount(r.qb_amount),
          `<span class="badge badge-yellow">${formatAmount(r.difference)}</span>`,
        ]
      );
      break;
  }
}

function renderTable(selector, headers, rows, rowFn) {
  const container = $(selector);

  if (!rows.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>No records found</p>
      </div>`;
    return;
  }

  const thead = `<thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows
    .map((r) => `<tr>${rowFn(r).map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;

  container.innerHTML = `<div class="table-wrap"><table>${thead}${tbody}</table></div>`;
}

function formatAmount(val) {
  if (val === null || val === undefined) return "-";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Tab Switching ────────────────────────────────────────────────────
function switchTab(tabName) {
  $$(".tab-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabName));
  $$(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.tab === tabName));
  renderTab(tabName);
}

// ── Search ───────────────────────────────────────────────────────────
function handleSearch(e) {
  state.searchQuery = e.target.value;
  renderTab(state.activeTab);
}

// ── Init ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Login
  $("#login-form").addEventListener("submit", handleLogin);
  $("#logout-btn").addEventListener("click", handleLogout);

  // Mode toggle
  $$(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });

  // File uploads
  initUpload("bank-file-input", "bank-upload-area", "bank-filename", "bankFile");
  initUpload("qb-file-input", "qb-upload-area", "qb-filename", "qbFile");

  // Reconcile
  $("#reconcile-btn").addEventListener("click", handleReconcile);

  // Tabs
  $$(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Search
  $("#search-input").addEventListener("input", handleSearch);

  // Check backend health
  Api.ping().then((ok) => {
    if (!ok) console.warn("⚠️ Backend not reachable. Start with: python backend/app.py");
  });
});
