// Beetle Box - "Kaefer eintragen" (POST /api/beetles).
//
// Sichtbar nur fuer eingeloggte researcher/admin (Backend erzwingt die Rolle
// zusaetzlich). Nutzt window.Auth.apiFetch (Bearer + Auto-Refresh). Das
// Formular wird aus FIELD_SPECS gerendert; Pflicht sind nur scientific_name
// und family, alles andere optional (siehe backend BeetleCreateRequest).

(function () {
  "use strict";

  var cfg = window.BeetleFormConfig || {};
  var LATAM_BOUNDS = cfg.LATAM_BOUNDS || {
    minLat: -56.0,
    maxLat: 33.5,
    minLon: -118.5,
    maxLon: -30.0,
  };
  var FIELD_SPECS = cfg.FIELD_SPECS || [];
  var NUMBER_FIELDS = cfg.NUMBER_FIELDS || { latitude: 1, longitude: 1 };

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

  // Baut eine stabile Feld-ID aus dem Konfigurations-Key.
  function fieldId(key) {
    return "bf_" + key;
  }

  // Erstellt ein Label-Element fuer ein Feld inkl. Pflichtmarker.
  function createFieldLabel(spec) {
    var label = document.createElement("label");
    label.className = "beetle-field" + (spec.type === "textarea" ? " beetle-field--wide" : "");
    label.setAttribute("for", fieldId(spec.key));
    label.appendChild(document.createTextNode(spec.label + (spec.required ? " *" : "")));
    return label;
  }

  // Baut ein Select-Feld inklusive leerer Default-Option.
  function createSelectInput(spec) {
    var input = document.createElement("select");
    var blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "- (keine Angabe) -";
    input.appendChild(blank);
    (spec.options || []).forEach(function (opt) {
      var option = document.createElement("option");
      option.value = opt;
      option.textContent = opt;
      input.appendChild(option);
    });
    return input;
  }

  // Erstellt das passende Input-Element je nach Feldtyp.
  function createFieldInput(spec) {
    if (spec.type === "textarea") {
      var textarea = document.createElement("textarea");
      textarea.rows = 2;
      return textarea;
    }
    if (spec.type === "select") {
      return createSelectInput(spec);
    }

    var input = document.createElement("input");
    input.type = spec.type === "number" ? "number" : spec.type === "url" ? "url" : "text";
    if (spec.min !== undefined) input.min = spec.min;
    if (spec.max !== undefined) input.max = spec.max;
    if (spec.step !== undefined) input.step = spec.step;
    return input;
  }

  // Uebernimmt gemeinsame Basisattribute fuer alle Feldtypen.
  function applyFieldAttributes(input, spec) {
    input.id = fieldId(spec.key);
    input.name = spec.key;
    if (spec.required) input.required = true;
    if (spec.placeholder) input.placeholder = spec.placeholder;
  }

  // Rendert optionalen Hilfetext unterhalb eines Feldes.
  function createFieldHint(spec) {
    if (!spec.hint) return null;
    var hint = document.createElement("span");
    hint.className = "beetle-hint";
    hint.textContent = spec.hint;
    return hint;
  }

  // Baut ein <label> mit passendem Eingabefeld fuer eine Feld-Definition.
  function buildField(spec) {
    var label = createFieldLabel(spec);
    var input = createFieldInput(spec);
    applyFieldAttributes(input, spec);
    label.appendChild(input);

    var hint = createFieldHint(spec);
    if (hint) label.appendChild(hint);
    return label;
  }

  // Rendert alle konfigurierten Formularfelder in Core/Advanced-Sektionen.
  function renderForm() {
    var core = $("beetleFieldsCore");
    var advanced = $("beetleFieldsAdvanced");
    if (!FIELD_SPECS.length) {
      console.warn("BeetleFormConfig fehlt oder ist leer.");
      return;
    }
    FIELD_SPECS.forEach(function (spec) {
      var target = spec.section === "advanced" ? advanced : core;
      target.appendChild(buildField(spec));
    });
  }

  // Prueft, ob Koordinaten innerhalb der LATAM-Grenzen liegen.
  function isInLatamBounds(lat, lon) {
    return (
      lat >= LATAM_BOUNDS.minLat &&
      lat <= LATAM_BOUNDS.maxLat &&
      lon >= LATAM_BOUNDS.minLon &&
      lon <= LATAM_BOUNDS.maxLon
    );
  }

  // Liest den Rohwert eines Feldes (trimmed) oder null.
  function readFieldValue(key) {
    var el = $(fieldId(key));
    if (!el) return null;
    var raw = el.value.trim();
    return raw === "" ? null : raw;
  }

  // Wandelt Feldwerte bei Bedarf in Zahlen um.
  function parsePayloadValue(key, raw) {
    if (!NUMBER_FIELDS[key]) return raw;
    var num = Number(raw);
    return Number.isNaN(num) ? null : num;
  }

  // Zerlegt einen Mehrzeilen-Text in eine Liste getrimmter, nicht-leerer Zeilen.
  function splitLines(raw) {
    return String(raw)
      .split(/\r?\n/)
      .map(function (line) { return line.trim(); })
      .filter(function (line) { return line !== ""; });
  }

  // Liest ausgefuellte Felder und erzeugt das API-Payload.
  function collectPayload() {
    var payload = {};
    FIELD_SPECS.forEach(function (spec) {
      var raw = readFieldValue(spec.key);
      if (raw == null) return;
      var value = parsePayloadValue(spec.key, raw);
      if (value != null) payload[spec.key] = value;
    });
    // Mehrbild: eine Bild-URL pro Zeile -> media_items (1:N).
    var imageRaw = payload.image_url;
    delete payload.image_url;
    if (imageRaw) {
      var urls = splitLines(imageRaw);
      if (urls.length) {
        payload.media_items = urls.map(function (url) {
          return {
            image_url: url,
            media_references: payload.media_references || null,
            media_creator: payload.media_creator || null,
            media_publisher: payload.media_publisher || null,
            media_rights_holder: payload.media_rights_holder || null,
            media_license: payload.media_license || null,
          };
        });
        payload.image_available = true;
      }
    }
    return payload;
  }

  // Setzt Erfolgs- und Fehlerhinweise zurueck.
  function clearMessages(errorEl, successEl) {
    hide(errorEl);
    hide(successEl);
    errorEl.textContent = "";
    successEl.textContent = "";
  }

  // Zeigt eine Fehlermeldung an und blendet Success aus.
  function showError(errorEl, successEl, msg) {
    hide(successEl);
    errorEl.textContent = msg;
    show(errorEl);
  }

  // Oeffnet das Eingabe-Modal und fokussiert das Hauptfeld.
  function openModal(modal) {
    show(modal);
    var first = $(fieldId("scientific_name"));
    if (first) first.focus();
  }

  // Schliesst das Eingabe-Modal.
  function closeModal(modal) {
    hide(modal);
  }

  // Prueft, ob Breiten-/Laengengrad entweder beide oder keiner gesetzt sind.
  function hasCompleteCoordinatePair(lat, lon) {
    return (lat === "") === (lon === "");
  }

  // Steuert Sichtbarkeit des Add-Buttons nach aktueller Rolle.
  function syncVisibility(addButton) {
    var role = window.Auth.getRole();
    if (role === "researcher" || role === "admin") show(addButton);
    else hide(addButton);
  }

  // Validiert optionale Koordinaten auf Vollstaendigkeit und LATAM-Bereich.
  function validateCoordinates(errorEl, successEl) {
    var lat = $(fieldId("latitude")).value.trim();
    var lon = $(fieldId("longitude")).value.trim();
    if (!hasCompleteCoordinatePair(lat, lon)) {
      showError(errorEl, successEl, "Breitengrad und Laengengrad bitte nur gemeinsam angeben.");
      return false;
    }
    if (lat !== "" && lon !== "") {
      var latNum = Number(lat);
      var lonNum = Number(lon);
      if (!isInLatamBounds(latNum, lonNum)) {
        showError(
          errorEl,
          successEl,
          "Koordinaten muessen in Lateinamerika liegen (Breite -56.0 bis 33.5, Laenge -118.5 bis -30.0)."
        );
        return false;
      }
    }
    return true;
  }

  // Schaltet den Submit-Button in den Lade- bzw. Normalzustand.
  function setSubmittingState(submitBtn, busy) {
    submitBtn.disabled = busy;
    submitBtn.textContent = busy ? "Speichern ..." : "Kaefer speichern";
  }

  // Erzeugt eine lesbare Fehlermeldung aus einer fehlgeschlagenen API-Antwort.
  async function responseErrorMessage(res) {
    var message = "Speichern fehlgeschlagen (" + res.status + ").";
    try {
      var body = await res.json();
      if (body && body.message) message = body.message;
    } catch (e2) {
      /* keine JSON-Antwort */
    }
    if (res.status === 401) return "Sitzung abgelaufen - bitte neu anmelden.";
    return message;
  }

  // Sendet einen Beetle-POST und liefert die Response zurueck.
  function postBeetle(payload) {
    return window.Auth.apiFetch("/api/beetles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  // Rendert die Erfolgsmeldung nach erfolgreichem Speichern.
  function showSubmitSuccess(successEl, created) {
    successEl.textContent =
      "Kaefer angelegt: " + created.scientific_name + " (ID " + created.id + ").";
    show(successEl);
  }

  // Prueft Format/Plausibilitaet weiterer Felder vor dem Absenden.
  function validateExtraFields(errorEl, successEl) {
    var dateEl = $(fieldId("event_date"));
    var dateVal = dateEl ? dateEl.value.trim() : "";
    if (dateVal) {
      var m = dateVal.match(/^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/);
      if (!m) {
        showError(errorEl, successEl, "Funddatum bitte als JJJJ, JJJJ-MM oder JJJJ-MM-TT angeben.");
        return false;
      }
      var year = Number(m[1]);
      var month = m[2] ? Number(m[2]) : null;
      var day = m[3] ? Number(m[3]) : null;
      var nextYear = new Date().getFullYear() + 1;
      if (year < 1700 || year > nextYear) {
        showError(errorEl, successEl, "Funddatum-Jahr unplausibel (1700-" + nextYear + ").");
        return false;
      }
      if (month !== null && (month < 1 || month > 12)) {
        showError(errorEl, successEl, "Funddatum: Monat muss zwischen 01 und 12 liegen.");
        return false;
      }
      if (day !== null && (day < 1 || day > 31)) {
        showError(errorEl, successEl, "Funddatum: Tag muss zwischen 01 und 31 liegen.");
        return false;
      }
    }

    var urlEl = $(fieldId("image_url"));
    var urlVal = urlEl ? urlEl.value.trim() : "";
    if (urlVal) {
      var imageUrls = splitLines(urlVal);
      for (var i = 0; i < imageUrls.length; i++) {
        if (!/^https?:\/\/.+/i.test(imageUrls[i])) {
          showError(errorEl, successEl, "Jede Bild-URL muss mit http:// oder https:// beginnen.");
          return false;
        }
      }
    }

    var elevEl = $(fieldId("elevation"));
    var elevVal = elevEl ? elevEl.value.trim() : "";
    if (elevVal !== "") {
      var elevNum = Number(elevVal);
      if (!isFinite(elevNum) || elevNum < -500 || elevNum > 9000) {
        showError(errorEl, successEl, "Hoehe muss zwischen -500 und 9000 m liegen.");
        return false;
      }
    }
    return true;
  }

  // Fuehrt Vorab-Validierung vor dem API-Submit aus.
  function canSubmit(form, errorEl, successEl) {
    if (!form.checkValidity()) {
      showError(errorEl, successEl, "Bitte Wissenschaftlichen Namen und Familie ausfuellen.");
      return false;
    }
    return validateCoordinates(errorEl, successEl) && validateExtraFields(errorEl, successEl);
  }

  // Validiert und sendet das Formular als POST an die Beetle-API.
  async function submitForm(form, submitBtn, errorEl, successEl) {
    if (!canSubmit(form, errorEl, successEl)) return;

    setSubmittingState(submitBtn, true);
    try {
      var res = await postBeetle(collectPayload());
      if (!res.ok) {
        showError(errorEl, successEl, await responseErrorMessage(res));
        return;
      }
      var created = await res.json();
      form.reset();
      showSubmitSuccess(successEl, created);
    } catch (err) {
      showError(errorEl, successEl, "Netzwerkfehler - bitte erneut versuchen.");
    } finally {
      setSubmittingState(submitBtn, false);
    }
  }

  // Bindet den Oeffnen-Button des Modals.
  function bindOpenModal(addButton, modal, errorEl, successEl) {
    addButton.addEventListener("click", function () {
      clearMessages(errorEl, successEl);
      openModal(modal);
    });
  }

  // Bindet alle Schliessen-Buttons des Modals.
  function bindModalCloseButtons(modal) {
    modal.querySelectorAll("[data-beetle-close]").forEach(function (el) {
      el.addEventListener("click", function () {
        closeModal(modal);
      });
    });
  }

  // Erlaubt das Schliessen des Modals ueber die Escape-Taste.
  function bindEscapeToClose(modal) {
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.classList.contains("is-hidden")) {
        closeModal(modal);
      }
    });
  }

  // Bindet das Formular an den Submit-Handler.
  function bindFormSubmit(form, submitBtn, errorEl, successEl) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearMessages(errorEl, successEl);
      await submitForm(form, submitBtn, errorEl, successEl);
    });
  }

  // Verknuepft auth:changed mit der Rollen-Sichtbarkeit.
  function bindAuthVisibility(addButton) {
    window.addEventListener("auth:changed", function () {
      syncVisibility(addButton);
    });
    syncVisibility(addButton);
  }

  // Initialisiert Beetle-Modal, Formular-Handling und Auth-gesteuerte Sichtbarkeit.
  function init() {
    var addButton = $("addBeetleButton");
    var modal = $("beetleModal");
    if (!addButton || !modal || !window.Auth) return;

    renderForm();

    var form = $("beetleForm");
    var errorEl = $("beetleError");
    var successEl = $("beetleSuccess");
    var submitBtn = $("beetleSubmit");

    bindOpenModal(addButton, modal, errorEl, successEl);
    bindModalCloseButtons(modal);
    bindEscapeToClose(modal);
    bindFormSubmit(form, submitBtn, errorEl, successEl);
    bindAuthVisibility(addButton);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
