(function () {
  "use strict";

  // Kartenausschnitt fuer Lateinamerika 
  var LATAM_BOUNDS = {
    west: -160,
    south: -58,
    east: -32,
    north: 34,
  };

  var googleMapsScriptPromises = {};

  // Normalisiert den Eingabewert fuer eine konsistente Verarbeitung.
  function normalizeLegendColor(value) {
    var text = String(value || "").trim().toLowerCase();
    if (!text) return "";
    if (text.charAt(0) === "#") {
      if (text.length === 4) {
        return "#" + text.charAt(1) + text.charAt(1) + text.charAt(2) + text.charAt(2) + text.charAt(3) + text.charAt(3);
      }
      return text;
    }
    var rgb = text.match(/rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
    if (rgb) {
      var toHex = function (n) {
        return Number(n).toString(16).padStart(2, "0");
      };
      return "#" + toHex(rgb[1]) + toHex(rgb[2]) + toHex(rgb[3]);
    }
    return text;
  }

  // Prueft, ob die Bedingung erfuellt ist.
  function hasUsableGoogleMapsKey(key) {
    return Boolean(key) && key !== "DEIN_API_KEY_HIER";
  }

  // Laedt die benoetigten Daten oder Ressourcen.
  function loadGoogleMapsScript(options) {
    var opts = options || {};
    if (window.google && window.google.maps) return Promise.resolve(true);

    var key = opts.key;
    if (!hasUsableGoogleMapsKey(key)) return Promise.resolve(false);

    var callbackName = String(opts.callbackName || "initMap");
    var timeoutMs = Number(opts.timeoutMs || 12000);
    if (googleMapsScriptPromises[callbackName]) return googleMapsScriptPromises[callbackName];

    googleMapsScriptPromises[callbackName] = new Promise(function (resolve) {
      var settled = false;
      var timeoutId = null;
      function finish(value) {
        if (settled) return;
        settled = true;
        if (timeoutId) clearTimeout(timeoutId);
        resolve(value);
      }

      var existingCallback = typeof window[callbackName] === "function" ? window[callbackName] : null;
      window[callbackName] = function () {
        if (existingCallback) existingCallback();
        finish(true);
      };

      timeoutId = setTimeout(function () {
        console.warn("Google Maps script load timed out.");
        finish(false);
      }, Math.max(1000, timeoutMs));

      var script = document.createElement("script");
      script.src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(String(key)) +
        "&callback=" +
        encodeURIComponent(callbackName) +
        "&loading=async";
      script.async = true;
      script.defer = true;
      script.onerror = function () {
        finish(false);
      };
      document.head.appendChild(script);
    });

    return googleMapsScriptPromises[callbackName];
  }

  window.MapCommon = {
    LATAM_BOUNDS: LATAM_BOUNDS, normalizeLegendColor: normalizeLegendColor,
    hasUsableGoogleMapsKey: hasUsableGoogleMapsKey, loadGoogleMapsScript: loadGoogleMapsScript,
  };
})();
