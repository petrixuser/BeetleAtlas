// Beetle Box - Auth-UI: verdrahtet die Auth-Box + das Anmelden/Registrieren-
// Modal mit dem Auth-Layer (window.Auth aus auth.js). Reines DOM-Wiring.

(function () {
  "use strict";

  var ROLE_LABELS = {
    admin: "Admin",
    researcher: "Researcher",
    viewer: "Viewer",
  };

  // Liefert ein DOM-Element per ID.
  function $(id) {
    return document.getElementById(id);
  }

  // Blendet ein Element ein.
  function show(el) {
    if (el) el.classList.remove("is-hidden");
  }

  // Blendet ein Element aus.
  function hide(el) {
    if (el) el.classList.add("is-hidden");
  }

  // Prueft grob, ob ein Wert wie eine E-Mail-Adresse aussieht.
  function isLikelyEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  // Validiert Passwortstaerke gemaess Frontend-Regeln und liefert Fehlertext.
  function validateStrongPassword(value) {
    if (value.length < 12) return "Passwort muss mindestens 12 Zeichen haben.";
    if (!/[A-Z]/.test(value)) return "Passwort muss mindestens einen Grossbuchstaben enthalten.";
    if (!/[a-z]/.test(value)) return "Passwort muss mindestens einen Kleinbuchstaben enthalten.";
    if (!/\d/.test(value)) return "Passwort muss mindestens eine Zahl enthalten.";
    if (!/[^A-Za-z0-9]/.test(value)) return "Passwort muss mindestens ein Sonderzeichen enthalten.";
    return null;
  }

  // Verdrahtet den Passwort-Sichtbarkeitstoggle fuer ein Eingabefeld.
  function setupPasswordToggle(inputId, buttonId) {
    var input = $(inputId);
    var button = $(buttonId);
    if (!input || !button) return;
    var srLabel = button.querySelector(".sr-only");

    // Uebernimmt alle visuellen und ARIA-Zustaende des Toggle-Buttons.
    function applyState(isVisible) {
      input.type = isVisible ? "text" : "password";
      button.classList.toggle("is-visible", isVisible);
      button.setAttribute("aria-pressed", String(isVisible));
      button.setAttribute("aria-label", isVisible ? "Passwort verbergen" : "Passwort anzeigen");
      if (srLabel) {
        srLabel.textContent = isVisible ? "Passwort verbergen" : "Passwort anzeigen";
      }
    }

    applyState(false);
    button.addEventListener("click", function () {
      applyState(input.type === "password");
      input.focus();
    });
  }

  // Erzeugt eine benutzerfreundliche Fehlermeldung aus API-/Netzwerkfehlern.
  function authErrorMessage(err, mode) {
    if (!err) {
      return mode === "login" ? "Anmeldung fehlgeschlagen." : "Registrierung fehlgeschlagen.";
    }
    if (err.status === 401) return "E-Mail oder Passwort ist falsch.";
    if (err.status === 403 && mode === "register") return "Researcher-Code ist ungueltig.";
    if (err.status === 409 && mode === "register") return "Diese E-Mail ist bereits registriert.";
    if (err.status === 422 && mode === "register") {
      return "Bitte E-Mail, Passwortregeln und Researcher-Code pruefen.";
    }
    if (err.status === 422 && mode === "login") {
      return "Bitte eine gueltige E-Mail und ein Passwort eingeben.";
    }
    if (/failed to fetch|network|netzwerk/i.test(String(err.message || ""))) {
      return "Netzwerkfehler: Backend nicht erreichbar. Bitte erneut versuchen.";
    }
    return err.message || (mode === "login" ? "Anmeldung fehlgeschlagen." : "Registrierung fehlgeschlagen.");
  }

  // Rendert den Login-Status in der Auth-Box (anon vs. eingeloggt).
  function renderAuthState(ctx) {
    var user = window.Auth.getCurrentUser();
    if (user) {
      ctx.emailEl.textContent = user.email;
      ctx.roleEl.textContent = ROLE_LABELS[user.role] || user.role;
      ctx.roleEl.className = "auth-band-label";
      hide(ctx.anon);
      show(ctx.userState);
    } else {
      hide(ctx.userState);
      show(ctx.anon);
    }
  }

  // Schaltet zwischen Login- und Register-Tab um.
  function selectTab(ctx, name) {
    ctx.tabs.forEach(function (tab) {
      tab.classList.toggle("is-active", tab.dataset.tab === name);
    });
    ctx.loginForm.classList.toggle("is-hidden", name !== "login");
    ctx.registerForm.classList.toggle("is-hidden", name !== "register");
  }

  // Setzt beide Fehlerbereiche zurueck.
  function clearErrors(ctx) {
    hide(ctx.loginError);
    hide(ctx.registerError);
    ctx.loginError.textContent = "";
    ctx.registerError.textContent = "";
  }

  // Oeffnet das Auth-Modal und fokussiert das erste sichtbare Eingabefeld.
  function openModal(ctx, tab) {
    clearErrors(ctx);
    selectTab(ctx, tab || "login");
    show(ctx.modal);
    var firstInput = ctx.modal.querySelector(".auth-form:not(.is-hidden) input");
    if (firstInput) firstInput.focus();
  }

  // Schliesst das Auth-Modal und setzt Form-Zustaende zurueck.
  function closeModal(ctx) {
    hide(ctx.modal);
    ctx.loginForm.reset();
    ctx.registerForm.reset();
    clearErrors(ctx);
  }

  // Zeigt eine Fehlermeldung im Zielbereich an.
  function showError(el, message) {
    el.textContent = message;
    show(el);
  }

  // Schaltet den Submit-Zustand eines Buttons inkl. Label um.
  function setSubmitting(button, busy, idleLabel) {
    button.disabled = busy;
    button.textContent = busy ? "Bitte warten ..." : idleLabel;
  }

  // Prueft Login-Eingaben und liefert die bereinigte E-Mail.
  function validateLoginInput(ctx) {
    var loginEmail = $("loginEmail").value.trim();
    if (!isLikelyEmail(loginEmail)) {
      showError(ctx.loginError, "Bitte eine gueltige E-Mail-Adresse eingeben.");
      return null;
    }
    return loginEmail;
  }

  // Prueft Register-Eingaben und liefert E-Mail + Passwort.
  function validateRegisterInput(ctx) {
    var registerEmail = $("registerEmail").value.trim();
    if (!isLikelyEmail(registerEmail)) {
      showError(ctx.registerError, "Bitte eine gueltige E-Mail-Adresse eingeben.");
      return null;
    }

    var registerPassword = $("registerPassword").value;
    var passwordError = validateStrongPassword(registerPassword);
    if (passwordError) {
      showError(ctx.registerError, passwordError);
      return null;
    }

    return { email: registerEmail, password: registerPassword };
  }

  // Fuehrt den Login-Submit aus.
  async function submitLogin(ctx) {
    var loginEmail = validateLoginInput(ctx);
    if (!loginEmail) return;

    var btn = $("loginSubmit");
    setSubmitting(btn, true, "Anmelden");
    try {
      await window.Auth.login(loginEmail, $("loginPassword").value);
      closeModal(ctx);
    } catch (err) {
      showError(ctx.loginError, authErrorMessage(err, "login"));
    } finally {
      setSubmitting(btn, false, "Anmelden");
    }
  }

  // Fuehrt den Register-Submit aus.
  async function submitRegister(ctx) {
    var registerInput = validateRegisterInput(ctx);
    if (!registerInput) return;

    var btn = $("registerSubmit");
    setSubmitting(btn, true, "Registrieren");
    try {
      var result = await window.Auth.registerResearcher(
        registerInput.email,
        registerInput.password,
        $("registerCode").value.trim()
      );
      if (result && result.status === "pending_verification") {
        showError(
          ctx.registerError,
          "Fast geschafft! Wir haben dir eine Bestaetigungs-Mail an " + registerInput.email +
          " geschickt. Bitte klicke den Link darin und melde dich danach an."
        );
        return;
      }
      closeModal(ctx);
    } catch (err) {
      showError(ctx.registerError, authErrorMessage(err, "register"));
    } finally {
      setSubmitting(btn, false, "Registrieren");
    }
  }

  // Bindet Login/Register/Logout-Buttons.
  function bindMainButtons(ctx) {
    $("loginButton").addEventListener("click", function () {
      openModal(ctx, "login");
    });

    $("registerButton").addEventListener("click", function () {
      openModal(ctx, "register");
    });

    $("logoutButton").addEventListener("click", function () {
      window.Auth.logout();
    });
  }

  // Bindet Tab-Umschaltung im Modal.
  function bindTabEvents(ctx) {
    ctx.tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        clearErrors(ctx);
        selectTab(ctx, tab.dataset.tab);
      });
    });
  }

  // Bindet Schliessen ueber Buttons/Backdrop.
  function bindModalCloseEvents(ctx) {
    ctx.modal.querySelectorAll("[data-auth-close]").forEach(function (el) {
      el.addEventListener("click", function () {
        closeModal(ctx);
      });
    });
  }

  // Erlaubt Schliessen per Escape-Taste.
  function bindEscapeClose(ctx) {
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !ctx.modal.classList.contains("is-hidden")) {
        closeModal(ctx);
      }
    });
  }

  // Bindet Submit-Handler fuer Login und Registrierung.
  function bindFormSubmits(ctx) {
    ctx.loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearErrors(ctx);
      await submitLogin(ctx);
    });

    ctx.registerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearErrors(ctx);
      await submitRegister(ctx);
    });
  }

  // Bindet den globalen Auth-Change-Event auf die Box-Darstellung.
  function bindAuthChanged(ctx) {
    window.addEventListener("auth:changed", function () {
      renderAuthState(ctx);
    });
  }

  // Initialisiert Auth-Box, Modal, Formulare und Event-Handler.
  function init() {
    var authBox = $("authBox");
    if (!authBox || !window.Auth) return;

    // Ohne Backend (Demo-Modus) macht Login keinen Sinn -> Box ausblenden.
    if (!window.Auth.authEnabled()) {
      hide(authBox);
      return;
    }

    var anon = $("authAnon");
    var userState = $("authUser");
    var emailEl = $("authEmail");
    var roleEl = $("authRole");

    var modal = $("authModal");
    var loginForm = $("loginForm");
    var registerForm = $("registerForm");
    var loginError = $("loginError");
    var registerError = $("registerError");
    if (!modal || !loginForm || !registerForm || !loginError || !registerError) return;

    var tabs = modal.querySelectorAll(".auth-tab");

    var ctx = {
      anon: anon, userState: userState, emailEl: emailEl, roleEl: roleEl, modal: modal,
      loginForm: loginForm, registerForm: registerForm, loginError: loginError,
      registerError: registerError, tabs: tabs,
    };

    setupPasswordToggle("loginPassword", "loginPasswordToggle");
    setupPasswordToggle("registerPassword", "registerPasswordToggle");

    bindMainButtons(ctx);
    bindTabEvents(ctx);
    bindModalCloseEvents(ctx);
    bindEscapeClose(ctx);
    bindFormSubmits(ctx);
    bindAuthChanged(ctx);

    // Session beim Laden wiederherstellen (feuert auth:changed -> rendert).
    window.Auth.restoreSession();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
