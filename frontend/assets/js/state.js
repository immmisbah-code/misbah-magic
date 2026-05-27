/**
 * state.js — Centralised reactive state store.
 * Components subscribe to slices; mutations go through setState().
 */

const State = (() => {
  /* ─── Initial state ─── */
  let _state = {
    authenticated : false,
    activeTab     : "matched",        // results tab
    loading       : false,
    results       : null,             // raw API response
    reportFilename: null,
    bankFile      : null,
    qbFile        : null,
    searchQuery   : "",
  };

  /* ─── Subscribers map: key → [callback, …] ─── */
  const _subs = {};

  /** Subscribe to one or more state keys.
   *  @param {string|string[]} keys
   *  @param {function}        fn   called with (newValue, key, fullState)
   *  @returns {function} unsubscribe
   */
  function subscribe(keys, fn) {
    const arr = Array.isArray(keys) ? keys : [keys];
    arr.forEach(k => {
      if (!_subs[k]) _subs[k] = [];
      _subs[k].push(fn);
    });
    return () => arr.forEach(k => {
      _subs[k] = (_subs[k] || []).filter(f => f !== fn);
    });
  }

  /** Merge patch into state and notify subscribers. */
  function setState(patch) {
    const changed = {};
    Object.entries(patch).forEach(([k, v]) => {
      if (_state[k] !== v) {
        _state[k] = v;
        changed[k] = v;
      }
    });
    Object.entries(changed).forEach(([k, v]) => {
      (_subs[k] || []).forEach(fn => fn(v, k, _state));
    });
  }

  /** Read current state (or a single key). */
  function get(key) {
    return key === undefined ? { ..._state } : _state[key];
  }

  /** Convenience reset for a new reconciliation run. */
  function resetRun() {
    setState({
      loading       : false,
      results       : null,
      reportFilename: null,
      searchQuery   : "",
      activeTab     : "matched",
    });
  }

  return { subscribe, setState, get, resetRun };
})();
