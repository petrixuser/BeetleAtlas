// Gleicht die rec-IDs der statischen Featured-Liste mit dem Backend ab.
//
// Zweck: verhindert dauerhaft das "Driften" der IDs nach einem DB-Neuaufbau.
// Die kuratierten Felder (commonName, note, Bild) bleiben aus featured-beetles.js;
// nur die "id" wird per scientific_name auf die echte Backend-rec-ID gesetzt.
// Faellt der Backend-Aufruf aus, bleiben die statischen IDs als Fallback erhalten.

(function () {
  // Holt die echten Featured-IDs vom Backend und pinnt sie in window.FEATURED_BEETLES.
  async function reconcileFeaturedIds() {
    var base = window.API_BASE_URL;
    var list = window.FEATURED_BEETLES;
    if (!base || !Array.isArray(list) || !list.length) return;

    try {
      var res = await fetch(base + "/api/beetles/featured");
      if (!res.ok) return;
      var data = await res.json();
      var items = (data && data.items) || [];

      var nameToId = {};
      items.forEach(function (it) {
        if (it && it.name && it.id) nameToId[it.name] = it.id;
      });

      var nameToItem = {};
      items.forEach(function (it) {
        if (it && it.name) nameToItem[it.name] = it;
      });

      list.forEach(function (entry) {
        var id = nameToId[entry && entry.name];
        if (id) entry.id = id;
       var apiItem = nameToItem[entry && entry.name];
        if (apiItem && apiItem.precipitation != null) {
          entry.precipitation = apiItem.precipitation;
        }
      });
    } catch (e) {
    }
  }

  window.reconcileFeaturedIds = reconcileFeaturedIds;
})();
