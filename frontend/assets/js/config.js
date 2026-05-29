/**
 * config.js — App-level constants.
 */

const CONFIG = Object.freeze({
  API_BASE     : (location.hostname === "localhost" || location.hostname === "127.0.0.1")
                   ? "http://localhost:8080/api"
                   : "/api",
  APP_NAME     : "Misbah's Magic",
  VERSION      : "2.0.0",
  TOAST_TIMEOUT: 5000,
});
