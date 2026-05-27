/**
 * app.js — Entry point.
 * Bootstraps the application: initialises modules, wires event listeners,
 * and kicks off the initial state.
 *
 * Load order (see index.html):
 *   config.js → api.js → state.js → ui.js → uploader.js → results.js → app.js
 */

(async () => {
  /* ─────────────────────────────────────────
     1. Upload zone instances
  ───────────────────────────────────────── */
  let bankZone, qbZone;

  /* ─────────────────────────────────────────
     2. DOM references
  ───────────────────────────────────────── */
  const $ = id => document.getElementById(id);

  const loginForm      = $("login-form");
  const usernameInput  = $("username-input");
  const passwordInput  = $("password-input");
  const loginBtn       = $("btn-login");
  const loginError     = $("login-error");

  const btnRun      = $("btn-run");
  const btnNewRun   = $("btn-new-run");
  const btnDownload = $("btn-download");
  const searchInput = $("search-input");
  const pdfAiHint   = $("pdf-ai-hint");

  /* ─────────────────────────────────────────
     3. Backend health check
  ───────────────────────────────────────── */
  async function checkBackend() {
    const ok  = await Api.ping();
    const cls = `backend-dot ${ok ? "backend-dot--ok" : "backend-dot--err"}`;
    const title = ok ? "Backend connected" : "Cannot reach backend";
    ["backend-status", "backend-status-dash"].forEach(id => {
      const el = $(id);
      if (el) { el.className = cls; el.title = title; }
    });
  }
  checkBackend();
  setInterval(checkBackend, 30_000);

  /* ─────────────────────────────────────────
     4. Screen routing
  ───────────────────────────────────────── */
  function goLogin()     { UI.showScreen("screen-login"); }
  function goDashboard() { UI.showScreen("screen-dashboard"); }

  /* ─────────────────────────────────────────
     5. Login flow
  ───────────────────────────────────────── */
  async function handleLogin(e) {
    e.preventDefault();
    const username = usernameInput?.value?.trim();
    const password = passwordInput?.value?.trim();
    if (!username || !password) return;

    loginBtn.disabled    = true;
    loginBtn.textContent = "Verifying…";
    if (loginError) loginError.style.display = "none";

    try {
      await Api.verifyPassword(username, password);
      State.setState({ authenticated: true });
      goDashboard();
      initDashboard();
    } catch {
      if (loginError) {
        loginError.textContent   = "Incorrect password. Please try again.";
        loginError.style.display = "";
      }
      passwordInput?.focus();
    } finally {
      loginBtn.disabled    = false;
      loginBtn.textContent = "Sign In";
    }
  }

  loginForm?.addEventListener("submit", handleLogin);

  /* ─────────────────────────────────────────
     6. Dashboard initialisation (run once after auth)
  ───────────────────────────────────────── */
  let _dashboardInit = false;
  function initDashboard() {
    if (_dashboardInit) return;
    _dashboardInit = true;

    /* Bank zone — accepts PDF, Excel, or CSV */
    bankZone = Uploader.create({
      zoneId : "zone-bank",
      accept : [".pdf", ".xlsx", ".xls", ".csv"],
      label  : "Bank Statement",
      onFile : f => {
        State.setState({ bankFile: f });
        /* Show PDF hint banner if a PDF was selected */
        if (pdfAiHint) {
          pdfAiHint.style.display = (f && f.name.toLowerCase().endsWith(".pdf")) ? "" : "none";
        }
      },
    });

    /* QuickBooks zone — accepts Excel or CSV */
    qbZone = Uploader.create({
      zoneId : "zone-qb",
      accept : [".xlsx", ".xls", ".csv"],
      label  : "QuickBooks Export",
      onFile : f => State.setState({ qbFile: f }),
    });

    /* Run button */
    btnRun?.addEventListener("click", _run);

    /* New run */
    btnNewRun?.addEventListener("click", () => {
      _resetRun();
      bankZone?.reset();
      qbZone?.reset();
    });

    /* Download */
    btnDownload?.addEventListener("click", () => {
      const fn = State.get("reportFilename");
      if (!fn) return;
      const a    = document.createElement("a");
      a.href     = Api.reportUrl(fn);
      a.download = fn;
      a.click();
    });

    /* Search */
    searchInput?.addEventListener("input", () => {
      State.setState({ searchQuery: searchInput.value });
    });

    /* Hide results section initially */
    const rs = $("results-section");
    if (rs) rs.style.display = "none";
  }

  /* ─────────────────────────────────────────
     7. Unified reconciliation run
     Auto-routes: PDF bank → Gemini AI endpoint
                  CSV/Excel bank → Excel endpoint
  ───────────────────────────────────────── */
  async function _run() {
    const bankFile = State.get("bankFile");
    const qbFile   = State.get("qbFile");

    if (!bankFile || !qbFile) {
      UI.toast("Please upload both files before running.", "warning");
      return;
    }

    const isPdf = bankFile.name.toLowerCase().endsWith(".pdf");

    State.setState({ loading: true });
    UI.setLoading(true, isPdf ? "Extracting PDF with Gemini AI…" : "Reconciling files…");
    Results.clear();

    try {
      const data = isPdf
        ? await Api.reconcilePdf(bankFile, qbFile)
        : await Api.reconcileExcel(bankFile, qbFile);

      State.setState({ results: data, reportFilename: data.report_filename, loading: false });
      UI.setLoading(false);
      Results.render(data);
      if (btnDownload) btnDownload.style.display = data.report_filename ? "" : "none";
      UI.toast(`Reconciliation complete — ${data.summary?.matched ?? 0} matches found.`, "success");
    } catch (err) {
      UI.setLoading(false);
      State.setState({ loading: false });
      UI.toast(`Error: ${err.message}`, "error");
    }
  }

  /* ─────────────────────────────────────────
     8. Reset run state
  ───────────────────────────────────────── */
  function _resetRun() {
    State.resetRun();
    Results.clear();
    if (btnDownload) btnDownload.style.display = "none";
    if (searchInput) searchInput.value = "";
    if (pdfAiHint)   pdfAiHint.style.display = "none";
  }

  /* ─────────────────────────────────────────
     9. Bootstrap
  ───────────────────────────────────────── */
  function boot() {
    document.querySelectorAll("[data-app-name]").forEach(el => {
      el.textContent = CONFIG.APP_NAME;
    });
    goLogin();
  }

  boot();
})();
