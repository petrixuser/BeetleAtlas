// Beetle Box — Auth-UI: verdrahtet die Auth-Box + das Anmelden/Registrieren-
// Modal mit dem Auth-Layer (window.Auth aus auth.js). Reines DOM-Wiring.

(function () {
  "use strict";

  var ROLE_LABELS = {
    admin: "Admin",
    researcher: "Researcher",
    viewer: "Viewer",
  };

  function $(id) {
    return document.getElementById(id);
  }

  function show(el) {
    if (el) el.classList.remove("is-hidden");
  }

  function hide(el) {
    if (el) el.classList.add("is-hidden");
  }

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
    var tabs = modal.querySelectorAll(".auth-tab");

    // ---- Box-Zustand rendern -------------------------------------------

    function renderAuthState() {
      var user = window.Auth.getCurrentUser();
      if (user) {
        emailEl.textContent = user.email;
        roleEl.textContent = ROLE_LABELS[user.role] || user.role;
        roleEl.className = "auth-band-label";
        hide(anon);
        show(userState);
      } else {
        hide(userState);
        show(anon);
      }
    }

    // ---- Modal ----------------------------------------------------------

    function selectTab(name) {
      tabs.forEach(function (tab) {
        tab.classList.toggle("is-active", tab.dataset.tab === name);
      });
      loginForm.classList.toggle("is-hidden", name !== "login");
      registerForm.classList.toggle("is-hidden", name !== "register");
    }

    function clearErrors() {
      hide(loginError);
      hide(registerError);
      loginError.textContent = "";
      registerError.textContent = "";
    }

    function openModal(tab) {
      clearErrors();
      selectTab(tab || "login");
      show(modal);
      var firstInput = modal.querySelector(
        ".auth-form:not(.is-hidden) input"
      );
      if (firstInput) firstInput.focus();
    }

    function closeModal() {
      hide(modal);
      loginForm.reset();
      registerForm.reset();
      clearErrors();
    }

    function showError(el, message) {
      el.textContent = message;
      show(el);
    }

    function setSubmitting(button, busy, idleLabel) {
      button.disabled = busy;
      button.textContent = busy ? "Bitte warten …" : idleLabel;
    }

    // ---- Events ---------------------------------------------------------

    $("loginButton").addEventListener("click", function () {
      openModal("login");
    });

    $("registerButton").addEventListener("click", function () {
      openModal("register");
    });

    $("logoutButton").addEventListener("click", function () {
      window.Auth.logout();
    });

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        clearErrors();
        selectTab(tab.dataset.tab);
      });
    });

    // Schliessen via X, Klick auf Backdrop, oder ESC.
    modal.querySelectorAll("[data-auth-close]").forEach(function (el) {
      el.addEventListener("click", closeModal);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.classList.contains("is-hidden")) {
        closeModal();
      }
    });

    loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearErrors();
      var btn = $("loginSubmit");
      setSubmitting(btn, true, "Anmelden");
      try {
        await window.Auth.login(
          $("loginEmail").value.trim(),
          $("loginPassword").value
        );
        closeModal();
      } catch (err) {
        showError(loginError, err.message || "Anmeldung fehlgeschlagen.");
      } finally {
        setSubmitting(btn, false, "Anmelden");
      }
    });

    registerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearErrors();
      var btn = $("registerSubmit");
      setSubmitting(btn, true, "Registrieren");
      try {
        await window.Auth.registerResearcher(
          $("registerEmail").value.trim(),
          $("registerPassword").value,
          $("registerCode").value.trim()
        );
        closeModal();
      } catch (err) {
        showError(registerError, err.message || "Registrierung fehlgeschlagen.");
      } finally {
        setSubmitting(btn, false, "Registrieren");
      }
    });

    window.addEventListener("auth:changed", renderAuthState);

    // Session beim Laden wiederherstellen (feuert auth:changed -> rendert).
    window.Auth.restoreSession();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
