// Beetle Box — "Kaefer eintragen" (POST /api/beetles).
//
// Sichtbar nur fuer eingeloggte researcher/admin (Backend erzwingt die Rolle
// zusaetzlich). Nutzt window.Auth.apiFetch (Bearer + Auto-Refresh). Das
// Formular wird aus FIELD_SPECS gerendert; Pflicht sind nur scientific_name
// und family, alles andere optional (siehe backend BeetleCreateRequest).

(function () {
  "use strict";

  // GBIF basisOfRecord (muss exakt zur Backend-Whitelist passen).
  var BASIS_OF_RECORD = [
    "HUMAN_OBSERVATION",
    "MACHINE_OBSERVATION",
    "PRESERVED_SPECIMEN",
    "LIVING_SPECIMEN",
    "MATERIAL_SAMPLE",
    "MATERIAL_CITATION",
    "FOSSIL_SPECIMEN",
    "OCCURRENCE",
  ];

  // type: text | url | number | textarea | select ; section: core | advanced
  var FIELD_SPECS = [
    { key: "scientific_name", label: "Wissenschaftlicher Name", type: "text", section: "core", required: true },
    { key: "family", label: "Familie", type: "text", section: "core", required: true },
    { key: "genus", label: "Gattung", type: "text", section: "core" },
    { key: "specific_epithet", label: "Art-Epitheton", type: "text", section: "core" },
    { key: "event_date", label: "Funddatum", type: "text", section: "core", placeholder: "JJJJ-MM-TT", hint: "Format: JJJJ, JJJJ-MM oder JJJJ-MM-TT" },
    { key: "country", label: "Land", type: "text", section: "core" },
    { key: "latitude", label: "Breitengrad", type: "number", section: "core", min: -90, max: 90, step: "any" },
    { key: "longitude", label: "Längengrad", type: "number", section: "core", min: -180, max: 180, step: "any" },
    { key: "image_url", label: "Bild-URL", type: "url", section: "core" },
    { key: "notes", label: "Notizen", type: "textarea", section: "core" },

    { key: "scientific_name_authorship", label: "Autorschaft", type: "text", section: "advanced" },
    { key: "taxon_id", label: "Taxon-ID", type: "text", section: "advanced" },
    { key: "recorded_by", label: "Gesammelt von", type: "text", section: "advanced" },
    { key: "identified_by", label: "Bestimmt von", type: "text", section: "advanced" },
    { key: "identification_id", label: "Bestimmungs-ID", type: "text", section: "advanced" },
    { key: "basis_of_record", label: "Art des Nachweises", type: "select", section: "advanced", options: BASIS_OF_RECORD },
    { key: "gbif_id", label: "GBIF-ID", type: "number", section: "advanced", min: 1, step: "1" },
    { key: "catalogue_number", label: "Katalognummer", type: "text", section: "advanced" },
    { key: "institution_code", label: "Institution", type: "text", section: "advanced" },
    { key: "dataset_name", label: "Datensatz", type: "text", section: "advanced" },
    { key: "region", label: "Region", type: "text", section: "advanced" },
    { key: "city", label: "Ort / Stadt", type: "text", section: "advanced" },
    { key: "verbatim_locality", label: "Fundort (Text)", type: "textarea", section: "advanced" },
    { key: "location", label: "Standort", type: "text", section: "advanced" },
    { key: "coordinate_uncertainty", label: "Koordinaten-Unsicherheit", type: "text", section: "advanced" },
    { key: "verbatim_event_date", label: "Funddatum (Originaltext)", type: "text", section: "advanced" },
    { key: "media_references", label: "Medien-Referenz", type: "text", section: "advanced" },
    { key: "media_creator", label: "Medien-Urheber", type: "text", section: "advanced" },
    { key: "media_publisher", label: "Medien-Herausgeber", type: "text", section: "advanced" },
    { key: "media_rights_holder", label: "Medien-Rechteinhaber", type: "text", section: "advanced" },
    { key: "media_license", label: "Medien-Lizenz", type: "text", section: "advanced" },
  ];

  var NUMBER_FIELDS = { latitude: 1, longitude: 1, gbif_id: 1 };

  function $(id) {
    return document.getElementById(id);
  }
  function show(el) {
    if (el) el.classList.remove("is-hidden");
  }
  function hide(el) {
    if (el) el.classList.add("is-hidden");
  }

  function fieldId(key) {
    return "bf_" + key;
  }

  // Baut ein <label> mit passendem Eingabefeld fuer eine Feld-Definition.
  function buildField(spec) {
    var label = document.createElement("label");
    label.className = "beetle-field" + (spec.type === "textarea" ? " beetle-field--wide" : "");
    label.setAttribute("for", fieldId(spec.key));
    label.appendChild(
      document.createTextNode(spec.label + (spec.required ? " *" : ""))
    );

    var input;
    if (spec.type === "textarea") {
      input = document.createElement("textarea");
      input.rows = 2;
    } else if (spec.type === "select") {
      input = document.createElement("select");
      var blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "— (keine Angabe) —";
      input.appendChild(blank);
      spec.options.forEach(function (opt) {
        var o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        input.appendChild(o);
      });
    } else {
      input = document.createElement("input");
      input.type = spec.type === "number" ? "number" : spec.type === "url" ? "url" : "text";
      if (spec.min !== undefined) input.min = spec.min;
      if (spec.max !== undefined) input.max = spec.max;
      if (spec.step !== undefined) input.step = spec.step;
    }
    input.id = fieldId(spec.key);
    input.name = spec.key;
    if (spec.required) input.required = true;
    if (spec.placeholder) input.placeholder = spec.placeholder;
    label.appendChild(input);

    if (spec.hint) {
      var hint = document.createElement("span");
      hint.className = "beetle-hint";
      hint.textContent = spec.hint;
      label.appendChild(hint);
    }
    return label;
  }

  function renderForm() {
    var core = $("beetleFieldsCore");
    var advanced = $("beetleFieldsAdvanced");
    FIELD_SPECS.forEach(function (spec) {
      var target = spec.section === "advanced" ? advanced : core;
      target.appendChild(buildField(spec));
    });
  }

  // Liest nur ausgefuellte Felder aus und baut das JSON-Payload.
  function collectPayload() {
    var payload = {};
    FIELD_SPECS.forEach(function (spec) {
      var el = $(fieldId(spec.key));
      if (!el) return;
      var raw = el.value.trim();
      if (raw === "") return;
      if (NUMBER_FIELDS[spec.key]) {
        var num = Number(raw);
        if (!Number.isNaN(num)) payload[spec.key] = num;
      } else {
        payload[spec.key] = raw;
      }
    });
    if (payload.image_url) payload.image_available = true;
    return payload;
  }

  function init() {
    var addButton = $("addBeetleButton");
    var modal = $("beetleModal");
    if (!addButton || !modal || !window.Auth) return;

    renderForm();

    var form = $("beetleForm");
    var errorEl = $("beetleError");
    var successEl = $("beetleSuccess");
    var submitBtn = $("beetleSubmit");

    function clearMessages() {
      hide(errorEl);
      hide(successEl);
      errorEl.textContent = "";
      successEl.textContent = "";
    }
    function showError(msg) {
      hide(successEl);
      errorEl.textContent = msg;
      show(errorEl);
    }

    function openModal() {
      clearMessages();
      show(modal);
      var first = $(fieldId("scientific_name"));
      if (first) first.focus();
    }
    function closeModal() {
      hide(modal);
    }

    // Add-Button nur fuer researcher/admin zeigen.
    function syncVisibility() {
      var role = window.Auth.getRole();
      if (role === "researcher" || role === "admin") show(addButton);
      else hide(addButton);
    }

    addButton.addEventListener("click", openModal);
    modal.querySelectorAll("[data-beetle-close]").forEach(function (el) {
      el.addEventListener("click", closeModal);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.classList.contains("is-hidden")) {
        closeModal();
      }
    });

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      clearMessages();

      // HTML5-Pflichtfeld-Pruefung (wir nutzen novalidate fuer eigene Meldungen).
      if (!form.checkValidity()) {
        showError("Bitte Wissenschaftlichen Namen und Familie ausfüllen.");
        return;
      }
      // Koordinaten nur paarweise (Backend lehnt sonst mit generischem 422 ab).
      var lat = $(fieldId("latitude")).value.trim();
      var lon = $(fieldId("longitude")).value.trim();
      if ((lat === "") !== (lon === "")) {
        showError("Breitengrad und Längengrad bitte nur gemeinsam angeben.");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Speichern …";
      try {
        var res = await window.Auth.apiFetch("/api/beetles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(collectPayload()),
        });
        if (!res.ok) {
          var message = "Speichern fehlgeschlagen (" + res.status + ").";
          try {
            var body = await res.json();
            if (body && body.message) message = body.message;
          } catch (e2) {
            /* keine JSON-Antwort */
          }
          if (res.status === 401) message = "Sitzung abgelaufen — bitte neu anmelden.";
          showError(message);
          return;
        }
        var created = await res.json();
        form.reset();
        successEl.textContent =
          "Käfer angelegt: " + created.scientific_name + " (ID " + created.id + ").";
        show(successEl);
      } catch (err) {
        showError("Netzwerkfehler — bitte erneut versuchen.");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Käfer speichern";
      }
    });

    window.addEventListener("auth:changed", syncVisibility);
    syncVisibility();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
