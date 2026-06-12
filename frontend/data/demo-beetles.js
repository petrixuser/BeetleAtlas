// Demo-Daten fuer Beetle Box
// Werden im Mock-Modus verwendet, solange kein Backend verfuegbar ist.
// Spaeter ersetzt durch echte Backend-Daten ueber loadBeetles() in app.js.
//
// Hinweis: climate/vegetation nutzen dieselben englischen Codes wie das Backend
// (siehe CLIMATE_LABELS / VEGETATION_LABELS in app.js). Die UI zeigt deutsche Labels.

window.DEMO_BEETLES = [
  {
    id: 1,
    name: "Dynastes hercules",
    family: "Scarabaeidae",
    location: "Amazonas, Ecuador",
    coordinates: [-78.2, -1.4],
    climate: "hot",
    vegetation: "tree_cover",
    elevation: 450,
    temperature: 27,
    soil: "Lehmiger Waldboden"
  },
  {
    id: 2,
    name: "Chiasognathus grantii",
    family: "Lucanidae",
    location: "Anden, Chile",
    coordinates: [-72.6, -39.8],
    climate: "mild",
    vegetation: "shrubland",
    elevation: 1700,
    temperature: 14,
    soil: "Humusreicher Gebirgsboden"
  },
  {
    id: 3,
    name: "Megasoma actaeon",
    family: "Scarabaeidae",
    location: "Guayana-Schild",
    coordinates: [-61.1, 5.1],
    climate: "warm",
    vegetation: "grassland",
    elevation: 700,
    temperature: 25,
    soil: "Sandiger Boden"
  },
  {
    id: 4,
    name: "Euchroma gigantea",
    family: "Buprestidae",
    location: "Mata Atlantica, Brasilien",
    coordinates: [-43.2, -22.9],
    climate: "warm",
    vegetation: "tree_cover",
    elevation: 250,
    temperature: 26,
    soil: "Roter Lateritboden"
  }
];
