
// Auth-Management: Login, Token-Handling, Session-Persistenz, API-Hilfsfunktion mit automatischer Token-Erneuerung etc.
(function () {
  "use strict";

  var STORAGE_REFRESH = "bb_refresh";
  var STORAGE_USER = "bb_user";

  var accessToken = null; // nur im Speicher
  var currentUser = null;

  // ---- Hilfsfunktionen ---------------------------------------------------
    // API_BASE_URL wird nur in Umgebungen mit Authentifizierung gesetzt
  function apiBase() {
    return window.API_BASE_URL || "";
  }

  // Aktiviert Auth-Features nur, wenn eine API-URL vorhanden ist.
  function authEnabled() {
    return Boolean(apiBase());
  }

  // ---- Persistenz -------------------------------------------------------

  // Liest den Refresh-Token aus localStorage (fehlertolerant).
  function getRefreshToken() {
    try {
      return localStorage.getItem(STORAGE_REFRESH);
    } catch (e) {
      return null;
    }
  }

  // Schreibt oder entfernt den Refresh-Token in localStorage.
  function setRefreshToken(token) {
    try {
      if (token) localStorage.setItem(STORAGE_REFRESH, token);
      else localStorage.removeItem(STORAGE_REFRESH);
    } catch (e) {
    }
  }

  // Haelt den aktuellen User im Speicher und im localStorage synchron.
  function cacheUser(user) {
    currentUser = user || null;
    try {
      if (user) localStorage.setItem(STORAGE_USER, JSON.stringify(user));
      else localStorage.removeItem(STORAGE_USER);
    } catch (e) {
      /* ignore */
    }
  }

  // Laedt den gecachten User aus localStorage.
  function readCachedUser() {
    try {
      var raw = localStorage.getItem(STORAGE_USER);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  // Loescht alle lokalen Session-Daten (Access, Refresh, User).
  function clearSession() {
    accessToken = null;
    setRefreshToken(null);
    cacheUser(null);
  }

  // Sendet ein globales Event, damit UI/Auth-Status aktualisiert wird.
  function emitChange() {
    window.dispatchEvent(new CustomEvent("auth:changed"));
  }

  // Baut aus einer API-Fehlantwort eine einheitliche Error-Exception.
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

  // Baut Request-Optionen mit JSON-Body fuer POST-Endpunkte.
  function buildJsonPostOptions(payload) {
    return {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    };
  }

  // Fuehrt POST-Requests mit JSON-Payload aus und validiert Fehler.
  async function postJson(path, payload) {
    var res = await fetch(apiBase() + path, buildJsonPostOptions(payload));
    if (!res.ok) await throwApiError(res);
    return res.json();
  }

  // Uebernimmt Access-/Refresh-Token aus Login-/Refresh-Antworten.
  function storeTokens(tokenResponse) {
    accessToken = tokenResponse.access_token || null;
    if (tokenResponse.refresh_token) setRefreshToken(tokenResponse.refresh_token);
  }

  // ---- Auth-Operationen -------------------------------------------------

  // Baut Header fuer authentifizierte Requests aus dem aktuellen Access-Token.
  function authHeaders() {
    return accessToken ? { Authorization: "Bearer " + accessToken } : {};
  }

  // Versucht, einen 401-Request nach Token-Refresh exakt einmal zu wiederholen.
  async function retryAfterRefresh(path, withAuth) {
    var ok = await authRefresh();
    if (ok) {
      return fetch(apiBase() + path, withAuth());
    }
    clearSession();
    emitChange();
    return null;
  }

  // Laedt den aktuell eingeloggten Nutzer ueber /auth/me.
  async function fetchMe() {
    if (!accessToken) return null;
    var res = await fetch(apiBase() + "/auth/me", {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    var user = await res.json();
    cacheUser(user);
    return user;
  }

  // Fuehrt Login aus, speichert Tokens und laedt anschliessend den User.
  async function authLogin(email, password) {
    var tokens = await postJson("/auth/login", { email: email, password: password });
    storeTokens(tokens);
    var user = await fetchMe();
    emitChange();
    return user;
  }


  // Registriert einen Researcher und loggt danach direkt ein.
  async function authRegisterResearcher(email, password, code) {
    await postJson("/auth/register", {
      email: email,
      password: password,
      role: "researcher",
      researcher_signup_code: code,
    });
    return authLogin(email, password);
  }

  // Holt per Refresh-Token einen neuen Access-Token.
  async function authRefresh() {
    var refresh = getRefreshToken();
    if (!refresh) return false;
    try {
      var res = await fetch(apiBase() + "/auth/refresh", buildJsonPostOptions({ refresh_token: refresh }));
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

  // Meldet den Nutzer serverseitig ab und loescht lokal die Session.
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

  // Stellt eine Session aus lokalem Cache + Refresh-Token wieder her.
  async function restoreSession() {
    if (!authEnabled()) {
      emitChange();
      return;
    }
    currentUser = readCachedUser();
    if (getRefreshToken()) {
      var ok = await authRefresh();
      if (ok) await fetchMe();
      else clearSession();
    }
    emitChange();
  }


  // Fuehrt API-Requests mit Bearer-Token aus und versucht bei 401 ein Refresh.
  async function apiFetch(path, options) {
    options = options || {};

    function withAuth() {
      var headers = Object.assign({}, options.headers || {});
      if (accessToken) headers.Authorization = authHeaders().Authorization;
      return Object.assign({}, options, { headers: headers });
    }

    var res = await fetch(apiBase() + path, withAuth());
    if (res.status === 401 && getRefreshToken()) {
      var retryRes = await retryAfterRefresh(path, withAuth);
      if (retryRes) res = retryRes;
    }
    return res;
  }


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
