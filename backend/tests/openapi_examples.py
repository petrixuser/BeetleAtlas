HEALTH_OK_EXAMPLE = {"status": "ok"}

BEETLES_LIST_EXAMPLE = {
    "items": [
        {
            "id": "occ-1",
            "name": "Dynastes hercules",
            "family": "Scarabaeidae",
            "location": "Amazonas, Ecuador",
            "coordinates": [-78.2, -1.4],
            "climate": "Tropisch",
            "vegetation": "Regenwald",
            "elevation": 450,
            "temperature": 27.0,
            "soil": "Lehmiger Waldboden",
            "observedAt": "2024-05-12",
            "imageUrl": "https://example.org/media/occ-1-1.jpg",
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 100,
}

BEETLE_DETAIL_EXAMPLE = {
    "id": "occ-1",
    "name": "Dynastes hercules",
    "family": "Scarabaeidae",
    "location": "Amazonas, Ecuador",
    "coordinates": [-78.2, -1.4],
    "climate": "Tropisch",
    "vegetation": "Regenwald",
    "elevation": 450,
    "temperature": 27.0,
    "soil": "Lehmiger Waldboden",
    "observedAt": "2024-05-12",
    "imageUrl": "https://example.org/media/occ-1-1.jpg",
    "meta": {
        "media": {
            "mediaCount": 2,
            "coverage": "mehrere_bilder",
            "licenseSample": "CC BY 4.0",
            "licenseClass": "offen",
            "imageUrlSample": "https://example.org/media/occ-1-1.jpg",
            "items": [
                {
                    "url": "https://example.org/media/occ-1-1.jpg",
                    "license": "CC BY 4.0",
                    "creator": "Max Muster",
                    "publisher": "GBIF",
                    "rightsHolder": "Museum X",
                }
            ],
        }
    },
}

COUNTRY_DETAIL_EXAMPLE = {
    "code": "GT",
    "name": "GUATEMALA",
    "speciesCount": 740,
    "topClimates": ["Tropisch", "Subtropisch"],
    "topVegetations": ["Regenwald", "Savanne"],
    "elevationRange": [0, 3800],
}

MAP_POINTS_EXAMPLE = {
    "items": [
        {
            "id": "occ-1",
            "speciesName": "Dynastes hercules",
            "lat": -1.4,
            "lng": -78.2,
            "elevation": 450,
            "climate": "Tropisch",
            "vegetation": "Regenwald",
            "observedAt": "2024-05-12",
            "isCluster": False,
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 500,
    "clustered": False,
}

MAP_POINTS_GEOJSON_EXAMPLE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-78.2, -1.4]},
            "properties": {
                "id": "occ-1",
                "speciesName": "Dynastes hercules",
                "isCluster": False,
            },
        }
    ],
    "meta": {
        "total": 1,
        "page": 1,
        "page_size": 500,
        "clustered": False,
    },
}

FILTERS_CORE_EXAMPLE = {
    "climates": ["Tropisch", "Subtropisch", "Trocken", "Gebirge", "Gemaessigt"],
    "vegetations": ["Regenwald", "Savanne", "Trockenwald", "Gebirgsvegetation"],
    "elevations": ["low", "mid", "high", "veryHigh"],
}

QUALITY_REPORT_EXAMPLE = {
    "generatedAt": "2026-06-10T10:00:00+00:00",
    "totals": {
        "observations": 417581,
        "locations": 191388,
        "climateSnapshots": 206025,
    },
    "observationNullRates": [
        {"field": "event_date", "missing": 0, "ratePct": 0.0},
        {"field": "basis_of_record", "missing": 0, "ratePct": 0.0},
    ],
    "locationNullRates": [
        {"field": "soil_ph", "missing": 1240, "ratePct": 0.648},
        {"field": "worldclim_bio01", "missing": 0, "ratePct": 0.0},
    ],
    "climateSnapshotNullRates": [
        {"field": "soil_moisture", "missing": 0, "ratePct": 0.0},
        {"field": "ndvi", "missing": 0, "ratePct": 0.0},
    ],
    "eeCoverage": {
        "withSnapshotMatch": 401200,
        "withoutSnapshotMatch": 16381,
        "withSnapshotRatePct": 96.078,
    },
}

QUALITY_HISTORY_SNAPSHOT_EXAMPLE = {
    "snapshotId": 12,
    "source": "manual",
    "report": QUALITY_REPORT_EXAMPLE,
}

QUALITY_HISTORY_LIST_EXAMPLE = {
    "items": [
        {
            "snapshotId": 12,
            "generatedAt": "2026-06-10T14:20:00+00:00",
            "source": "manual",
            "totals": {
                "observations": 417581,
                "locations": 191388,
                "climateSnapshots": 206025,
            },
            "observationNullRates": QUALITY_REPORT_EXAMPLE["observationNullRates"],
            "locationNullRates": QUALITY_REPORT_EXAMPLE["locationNullRates"],
            "climateSnapshotNullRates": QUALITY_REPORT_EXAMPLE["climateSnapshotNullRates"],
            "eeCoverage": QUALITY_REPORT_EXAMPLE["eeCoverage"],
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
}

QUALITY_HISTORY_COMPARE_EXAMPLE = {
    "fromSnapshot": {
        "snapshotId": 10,
        "generatedAt": "2026-06-09T14:20:00+00:00",
        "source": "seed_import",
    },
    "toSnapshot": {
        "snapshotId": 12,
        "generatedAt": "2026-06-10T14:20:00+00:00",
        "source": "manual",
    },
    "observationNullRateDelta": [
        {
            "field": "event_date_parsed",
            "missingDelta": -12034,
            "ratePctDelta": -2.88,
        }
    ],
    "locationNullRateDelta": [],
    "climateSnapshotNullRateDelta": [],
    "eeCoverageDelta": {
        "withSnapshotMatchDelta": 740,
        "withoutSnapshotMatchDelta": -740,
        "withSnapshotRatePctDelta": 0.177,
    },
}

BEETLE_MEDIA_EXAMPLE = {
    "id": "occ-1",
    "items": [
        {
            "mediaId": 101,
            "url": "https://example.org/media/occ-1-1.jpg",
            "license": "CC BY 4.0",
            "creator": "Max Muster",
            "publisher": "GBIF",
            "rightsHolder": "Museum X",
            "references": "https://gbif.org/occurrence/1",
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
}