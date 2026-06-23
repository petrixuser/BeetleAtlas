// Beetle Box — Auth-Layer (Session, API, Anmelde-/Registrier-Modal).
//
// Spricht Bastis Backend-Auth (siehe backend/routers/auth_router.py):
//   POST /auth/login | /auth/register | /auth/refresh | /auth/logout
//   GET  /auth/me
// Basis-URL = window.API_BASE_URL. Ohne sie laeuft die Seite im Demo-Modus
// (kein Backend) -> Auth wird ausgeblendet.
//
// Token-Modell: Access-Token (JWT, ~30 min) lebt nur im Speicher; der
// Refresh-Token (~14 Tage) liegt in localStorage, damit die Session einen
// Reload ueberlebt. Das zwischengespeicherte User-Objekt erlaubt sofortiges
// UI-Rendering, bevor /auth/me antwortet. (localStorage ist fuer eine rein
// statische Seite ohne httpOnly-Cookie-Backend der pragmatische Kompromiss.)

(function () {
  "use strict";

  var STORAGE_REFRESH = "bb_refresh";
  var STORAGE_USER = "bb_user";

  var accessToken = null; // nur im Speicher
  var currentUser = null;

  function apiBase() {
    return window.API_BASE_URL || "";
  }

  function authEnabled() {
    return Boolean(apiBase());
  }

  // ---- Persistenz -------------------------------------------------------

  function getRefreshToken() {
    try {
      return localStorage.getItem(STORAGE_REFRESH);
    } catch (e) {
      return null;
    }
  }

  function setRefreshToken(token) {
    try {
      if (token) localStorage.setItem(STORAGE_REFRESH, token);
      else localStorage.removeItem(STORAGE_REFRESH);
    } catch (e) {
      /* localStorage nicht verfuegbar -> Session ist dann nicht persistent */
    }
  }

  function cacheUser(user) {
    currentUser = user || null;
    try {
      if (user) localStorage.setItem(STORAGE_USER, JSON.stringify(user));
      else localStorage.removeItem(STORAGE_USER);
    } catch (e) {
      /* ignore */
    }
  }

  function readCachedUser() {
    try {
      var raw = localStorage.getItem(STORAGE_USER);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function clearSession() {
    accessToken = null;
    setRefreshToken(null);
    cacheUser(null);
  }

  function emitChange() {
    window.dispatchEvent(new CustomEvent("auth:changed"));
  }

  // ---- HTTP-Helfer ------------------------------------------------------

  // Liest die Backend-Fehlermeldung ({error, message}) aus einer Response
  // und wirft einen Error mit lesbarem Text.
  async function throwApiError(res) {
    var message = "Anfrage fehlgeschlagen (" + res.status + ").";
    try {
      var body = await res.json();
      if (body && body.message) message = body.message;
    } catch (e) {
      /* keine JSON-Antwort */
    }
    var err = new Error(message);
    err.status = res.status;
    throw err;
  }

  async function postJson(path, payload) {
    var res = await fetch(apiBase() + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) await throwApiError(res);
    return res.json();
  }

  function storeTokens(tokenResponse) {
    accessToken = tokenResponse.access_token || null;
    if (tokenResponse.refresh_token) setRefreshToken(tokenResponse.refresh_token);
  }

  // ---- Auth-Operationen -------------------------------------------------

  async function fetchMe() {
    if (!accessToken) return null;
    var res = await fetch(apiBase() + "/auth/me", {
      headers: { Authorization: "Bearer " + accessToken },
    });
    if (!res.ok) return null;
    var user = await res.json();
    cacheUser(user);
    return user;
  }

  async function authLogin(email, password) {
    var tokens = await postJson("/auth/login", { email: email, password: password });
    storeTokens(tokens);
    var user = await fetchMe();
    emitChange();
    return user;
  }

  // Registrierung nur fuer Researcher (Viewer = anonym, Admin nur per Backend-
  // Bootstrap). Legt den Account an und meldet danach direkt an.
  async function authRegisterResearcher(email, password, code) {
    await postJson("/auth/register", {
      email: email,
      password: password,
      role: "researcher",
      researcher_signup_code: code,
    });
    return authLogin(email, password);
  }

  // Rotiert den Refresh-Token und holt einen neuen Access-Token. true bei Erfolg.
  async function authRefresh() {
    var refresh = getRefreshToken();
    if (!refresh) return false;
    try {
      var res = await fetch(apiBase() + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        clearSession();
        return false;
      }
      storeTokens(await res.json());
      return true;
    } catch (e) {
      return false;
    }
  }

  async function authLogout() {
    var refresh = getRefreshToken();
    if (accessToken) {
      try {
        await fetch(apiBase() + "/auth/logout", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + accessToken,
          },
          body: JSON.stringify(refresh ? { refresh_token: refresh } : {}),
        });
      } catch (e) {
        /* lokal trotzdem ausloggen */
      }
    }
    clearSession();
    emitChange();
  }

  // Beim Laden: vorhandenen Refresh-Token einloesen + Profil holen.
  async function restoreSession() {
    if (!authEnabled()) {
      emitChange();
      return;
    }
    currentUser = readCachedUser(); // optimistisch fuer sofortiges Rendering
    if (getRefreshToken()) {
      var ok = await authRefresh();
      if (ok) await fetchMe();
      else clearSession();
    }
    emitChange();
  }

  // Zentraler Wrapper fuer geschuetzte Endpunkte (kuenftige Schreib-UI):
  // haengt Bearer-Header an, erneuert bei 401 genau einmal und wiederholt.
  async function apiFetch(path, options) {
    options = options || {};
    function withAuth() {
      var headers = Object.assign({}, options.headers || {});
      if (accessToken) headers.Authorization = "Bearer " + accessToken;
      return Object.assign({}, options, { headers: headers });
    }
    var res = await fetch(apiBase() + path, withAuth());
    if (res.status === 401 && getRefreshToken()) {
      var ok = await authRefresh();
      if (ok) {
        res = await fetch(apiBase() + path, withAuth());
      } else {
        clearSession();
        emitChange();
      }
    }
    return res;
  }

  // ---- oeffentliche API -------------------------------------------------

  window.Auth = {
    authEnabled: authEnabled,
    login: authLogin,
    registerResearcher: authRegisterResearcher,
    logout: authLogout,
    refresh: authRefresh,
    restoreSession: restoreSession,
    apiFetch: apiFetch,
    isLoggedIn: function () {
      return Boolean(currentUser);
    },
    getCurrentUser: function () {
      return currentUser;
    },
    getRole: function () {
      return currentUser ? currentUser.role : null;
    },
  };
})();
