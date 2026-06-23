import ee
import pandas as pd
import time
import math
import argparse

DEFAULT_EE_PROJECT = "beetle-db"

STATIC_CSV = "csv/ee_locations_static.csv"
DYNAMIC_CSV = "csv/ee_location_dates_dynamic.csv"

STATIC_BATCH_SIZE = 10000
DYNAMIC_BATCH_SIZE = 10000
DYNAMIC_TILE_SCALE = 1
DYNAMIC_GROUPING = "year"  # "month" oder "year"
STATIC_EXPORT_PREFIX = "beetle_static"
DYNAMIC_EXPORT_PREFIX = "beetle_dynamic"
EXPORT_DRIVE_FOLDER = "beetle_exports"
MAX_ROWS = None  # für Test z.B. 1000 setzen, für komplett: None


def init_ee(project_id):
    project_id = (project_id or "").strip() or DEFAULT_EE_PROJECT
    ee.Initialize(project=project_id)
    print(f"Earth Engine Projekt: {project_id}")


def df_to_fc(df, properties):
    features = []

    for _, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]

        if pd.isna(lat) or pd.isna(lon):
            continue

        geom = ee.Geometry.Point([float(lon), float(lat)])

        props = {}
        for p in properties:
            props[p] = str(row[p])

        features.append(ee.Feature(geom, props))

    return ee.FeatureCollection(features)


def chunks(df, batch_size):
    for i in range(0, len(df), batch_size):
        yield i // batch_size, df.iloc[i:i + batch_size]


def parse_batch_filter(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None

    selected = set()
    parts = [p.strip() for p in value.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            start_str, end_str = [x.strip() for x in part.split("-", 1)]
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"Ungueltiger Bereich in --batch-filter: {part}")
            start = int(start_str)
            end = int(end_str)
            if start > end:
                raise ValueError(f"Ungueltiger Bereich in --batch-filter: {part}")
            selected.update(range(start, end + 1))
        else:
            if not part.isdigit():
                raise ValueError(f"Ungueltiger Wert in --batch-filter: {part}")
            selected.add(int(part))

    return selected


def remap_batch_filter(batch_filter, source_batch_size, target_batch_size):
    if batch_filter is None:
        return None

    if source_batch_size <= 0 or target_batch_size <= 0:
        raise ValueError("Batchgroessen fuer Remapping muessen > 0 sein")

    # Same size: nothing to map.
    if source_batch_size == target_batch_size:
        return set(batch_filter)

    if source_batch_size % target_batch_size != 0:
        raise ValueError(
            "--batch-filter-source-size muss ein Vielfaches von --dynamic-batch-size sein"
        )

    factor = source_batch_size // target_batch_size
    remapped = set()
    for old_id in batch_filter:
        start = old_id * factor
        remapped.update(range(start, start + factor))

    return remapped


def iter_dynamic_groups(df, grouping):
    if grouping == "month":
        months = sorted(df["date"].dropna().unique())

        for ym in months:
            year, month = ym.split("-")
            year = int(year)
            month = int(month)

            start = f"{year}-{month:02d}-01"

            if month == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{month + 1:02d}-01"

            yield ym, start, end, df[df["date"] == ym]

        return

    if grouping == "year":
        years = sorted(df["year"].dropna().unique())

        for year in years:
            year = int(year)
            start = f"{year}-01-01"
            end = f"{year + 1}-01-01"

            yield str(year), start, end, df[df["year"] == year]

        return

    raise ValueError("DYNAMIC_GROUPING muss 'month' oder 'year' sein.")


def make_static_description(batch_id):
    return f"{STATIC_EXPORT_PREFIX}_batch_{batch_id:04d}"


def make_dynamic_description(grouping, group_key, batch_id, batch_size):
    # YYYY-MM bleibt lesbar, andere Sonderzeichen entfernen wir vorsichtshalber.
    safe_key = str(group_key).replace("/", "_").replace(" ", "_")
    start_row = batch_id * batch_size
    end_row = start_row + batch_size - 1
    return (
        f"{DYNAMIC_EXPORT_PREFIX}_{grouping}_{safe_key}_batch_{batch_id:04d}"
        f"_bs{batch_size}_rows_{start_row:07d}_{end_row:07d}"
    )


def month_window_from_ym(ym):
    year, month = str(ym).split("-")
    year = int(year)
    month = int(month)

    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    return start, end


def build_static_image(disable_human_modification=False):
    srtm = ee.Image("USGS/SRTMGL1_003").select("elevation")
    slope = ee.Terrain.slope(srtm).rename("slope")

    worldcover = (
        ee.Image("ESA/WorldCover/v100/2020")
        .select("Map")
        .rename("landcover_class")
    )

    ph = (
        ee.Image("OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02")
        .select("b0")
        .divide(10)
        .rename("soil_ph")
    )

    soc = (
        ee.Image("OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02")
        .select("b0")
        .divide(5)
        .rename("soil_organic_carbon")
    )

    worldclim = ee.Image("WORLDCLIM/V1/BIO").select(
        ["bio01", "bio12"],
        ["worldclim_bio01", "worldclim_bio12"]
    )
    worldclim = worldclim.addBands(
        worldclim.select("worldclim_bio01").divide(10).rename("worldclim_bio01"),
        overwrite=True
    )

    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    water_mask = gsw.select("occurrence").gte(50).unmask(0)

    # Approximate Euclidean distance to nearest persistent surface water (meters).
    distance_to_water_m = (
        water_mask
        .fastDistanceTransform(1024)
        .sqrt()
        .multiply(30)
        .rename("distance_to_water_m")
    )

    eco_fc = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")
    ecoregion_id = eco_fc.reduceToImage(
        properties=["ECO_ID"],
        reducer=ee.Reducer.first()
    ).rename("ecoregion_id")

    biome_id = eco_fc.reduceToImage(
        properties=["BIOME_NUM"],
        reducer=ee.Reducer.first()
    ).rename("biome_id")

    if disable_human_modification:
        human_modification = ee.Image.constant(-9999).rename("human_modification")
    else:
        human_modification = (
            ee.ImageCollection("CSP/HM/GlobalHumanModification")
            .first()
            .select("gHM")
            .rename("human_modification")
        )

    return (
        srtm
        .addBands(slope)
        .addBands(worldcover)
        .addBands(ph)
        .addBands(soc)
        .addBands(worldclim)
        .addBands(distance_to_water_m)
        .addBands(ecoregion_id)
        .addBands(biome_id)
        .addBands(human_modification)
    )


def start_static_exports(
    drive_folder=EXPORT_DRIVE_FOLDER,
    static_csv=STATIC_CSV,
    disable_human_modification=False,
):
    df = pd.read_csv(static_csv)

    if MAX_ROWS:
        df = df.head(MAX_ROWS)

    # Prevent dropped rows from masked pixels by filling no-data with sentinel values.
    static_image = build_static_image(
        disable_human_modification=disable_human_modification
    ).unmask(-9999)

    total_batches = math.ceil(len(df) / STATIC_BATCH_SIZE)
    print(
        f"Static rows: {len(df)} | Batch size: {STATIC_BATCH_SIZE} | Batches: {total_batches}"
    )

    for batch_id, batch in chunks(df, STATIC_BATCH_SIZE):
        points = df_to_fc(batch, ["location_id"])

        sampled = static_image.sampleRegions(
            collection=points,
            properties=["location_id"],
            scale=1000,
            geometries=False
        )

        task = ee.batch.Export.table.toDrive(
            collection=sampled,
            description=make_static_description(batch_id),
            folder=drive_folder,
            fileFormat="CSV"
        )

        task.start()
        print(f"Static batch gestartet {batch_id + 1}/{total_batches}: {task.id}")
        time.sleep(5)


def build_dynamic_image(start, end):
    def _masked_empty_band(name):
        return ee.Image.constant(0).updateMask(ee.Image.constant(0)).rename(name)

    def _collection_stat(
        collection,
        band,
        reducer,
        out_name,
        multiply=None,
        divide=None,
        subtract=None,
    ):
        base = ee.Image(
            ee.Algorithms.If(
                collection.size().gt(0),
                (
                    collection.select(band).mean()
                    if reducer == "mean"
                    else collection.select(band).sum()
                ),
                _masked_empty_band(out_name),
            )
        ).rename(out_name)

        if subtract is not None:
            base = base.subtract(subtract)
        if divide is not None:
            base = base.divide(divide)
        if multiply is not None:
            base = base.multiply(multiply)

        return base.rename(out_name)

    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    era5_monthly = ee.ImageCollection("ECMWF/ERA5/MONTHLY")
    terraclimate = ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
    smap_new = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")
    smap_old = ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
    modis_q1 = ee.ImageCollection("MODIS/061/MOD13Q1")
    modis_a2 = ee.ImageCollection("MODIS/061/MOD13A2")
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    dmsp = ee.ImageCollection("NOAA/DMSP-OLS/NIGHTTIME_LIGHTS")

    era_month = era5.filterDate(start, end)
    era_monthly_window = era5_monthly.filterDate(start, end)
    terraclimate_window = terraclimate.filterDate(start, end)

    temp_monthly_fallback = _collection_stat(
        era_monthly_window,
        "mean_2m_air_temperature",
        "mean",
        "avg_temperature",
        subtract=273.15,
    )

    # TerraClimate tmmx/tmmn are stored as degC * 10.
    tc_tmax = _collection_stat(
        terraclimate_window,
        "tmmx",
        "mean",
        "avg_temperature",
    )
    tc_tmin = _collection_stat(
        terraclimate_window,
        "tmmn",
        "mean",
        "avg_temperature",
    )
    temp_terraclimate_fallback = (
        tc_tmax
        .add(tc_tmin)
        .divide(2)
        .multiply(0.1)
        .rename("avg_temperature")
    )

    dewpoint_monthly_fallback = _collection_stat(
        era_monthly_window,
        "dewpoint_2m_temperature",
        "mean",
        "dewpoint_c",
        subtract=273.15,
    )

    pressure_monthly_fallback = _collection_stat(
        era_monthly_window,
        "mean_sea_level_pressure",
        "mean",
        "surface_pressure_hpa",
        divide=100,
    )

    precip_monthly_fallback = _collection_stat(
        era_monthly_window,
        "total_precipitation",
        "sum",
        "precipitation",
        multiply=1000,
    )

    temp_primary = _collection_stat(
        era_month,
        "temperature_2m",
        "mean",
        "avg_temperature",
        subtract=273.15,
    )
    temp_c = (
        temp_primary
        .unmask(temp_monthly_fallback)
        .unmask(temp_terraclimate_fallback)
        .rename("avg_temperature")
    )

    precip_primary = _collection_stat(
        era_month,
        "total_precipitation_sum",
        "sum",
        "precipitation",
        multiply=1000,
    )

    # CHIRPS provides a robust precipitation fallback for masked/no-data ERA5 pixels.
    precip_chirps = _collection_stat(
        chirps.filterDate(start, end),
        "precipitation",
        "sum",
        "precipitation",
    )

    precip_mm = (
        precip_primary
        .unmask(precip_chirps)
        .unmask(precip_monthly_fallback)
        .rename("precipitation")
    )

    dewpoint_primary = _collection_stat(
        era_month,
        "dewpoint_temperature_2m",
        "mean",
        "dewpoint_c",
        subtract=273.15,
    )
    dewpoint_c = dewpoint_primary.unmask(dewpoint_monthly_fallback).rename("dewpoint_c")

    # Compute relative humidity (%) from temperature and dewpoint (Celsius).
    relative_humidity = temp_c.expression(
        "100 * exp((17.625 * td) / (243.04 + td) - (17.625 * t) / (243.04 + t))",
        {
            "td": dewpoint_c,
            "t": temp_c,
        }
    ).clamp(0, 100).rename("relative_humidity")

    surface_pressure_primary = _collection_stat(
        era_month,
        "surface_pressure",
        "mean",
        "surface_pressure_hpa",
        divide=100,
    )
    surface_pressure = (
        surface_pressure_primary
        .unmask(pressure_monthly_fallback)
        .rename("surface_pressure_hpa")
    )

    era5_soil_moisture = _collection_stat(
        era_month,
        "volumetric_soil_water_layer_1",
        "mean",
        "soil_moisture",
    )

    smap_new_month = smap_new.filterDate(start, end)
    smap_old_month = smap_old.filterDate(start, end)

    # Fallback order: newest SMAP -> older SMAP -> ERA5 soil water.
    soil_moisture = ee.Image(
        ee.Algorithms.If(
            smap_new_month.size().gt(0),
            smap_new_month.select("sm_surface").mean(),
            ee.Algorithms.If(
                smap_old_month.size().gt(0),
                smap_old_month.select("ssm").mean(),
                era5_soil_moisture
            )
        )
    ).rename("soil_moisture")

    viirs_month = viirs.filterDate(start, end)
    start_date = ee.Date(start)
    year_start = ee.Date.fromYMD(start_date.get("year"), 1, 1)
    year_end = year_start.advance(1, "year")
    viirs_year = viirs.filterDate(year_start, year_end)
    dmsp_month = dmsp.filterDate(start, end)

    empty_night = ee.Image(0).updateMask(ee.Image(0)).rename("nighttime_lights")

    nighttime_lights = ee.Image(
        ee.Algorithms.If(
            viirs_month.size().gt(0),
            viirs_month.select("avg_rad").mean(),
            ee.Algorithms.If(
                viirs_year.size().gt(0),
                viirs_year.select("avg_rad").mean(),
                ee.Algorithms.If(
                    dmsp_month.size().gt(0),
                    dmsp_month.select("stable_lights").mean(),
                    empty_night
                )
            )
        )
    ).rename("nighttime_lights")

    ndvi_q1 = _collection_stat(
        modis_q1.filterDate(start, end),
        "NDVI",
        "mean",
        "ndvi",
        multiply=0.0001,
    )

    ndvi_a2_fallback = _collection_stat(
        modis_a2.filterDate(start, end),
        "NDVI",
        "mean",
        "ndvi",
        multiply=0.0001,
    )

    ndvi = ndvi_q1.unmask(ndvi_a2_fallback).rename("ndvi")

    return (
        temp_c
        .addBands(precip_mm)
        .addBands(soil_moisture)
        .addBands(ndvi)
        .addBands(relative_humidity)
        .addBands(surface_pressure)
        .addBands(nighttime_lights)
    )


def start_dynamic_exports(
    year_filter=None,
    drive_folder=EXPORT_DRIVE_FOLDER,
    dynamic_batch_size=DYNAMIC_BATCH_SIZE,
    dynamic_tile_scale=DYNAMIC_TILE_SCALE,
    batch_filter=None,
    dynamic_csv=DYNAMIC_CSV,
):
    df = pd.read_csv(dynamic_csv)

    if MAX_ROWS:
        df = df.head(MAX_ROWS)

    df["date"] = df["date"].astype(str).str.strip()
    df = df[df["date"].str.match(r"^\d{4}-\d{2}$", na=False)]
    df["year"] = df["date"].str.slice(0, 4).astype(int)

    if year_filter:
        allowed_years = sorted({int(y) for y in year_filter})
        df = df[df["year"].isin(allowed_years)]
        if df.empty:
            print(f"Keine Dynamic-Daten fuer die angeforderten Jahre: {allowed_years}")
            return
        print(f"Year filter aktiv: {allowed_years}")

    if DYNAMIC_GROUPING == "month":
        group_count = df["date"].nunique()
    else:
        group_count = df["year"].nunique()

    print(
        f"Dynamic rows: {len(df)} | Grouping: {DYNAMIC_GROUPING} | Groups: {group_count} | Batch size: {dynamic_batch_size}"
    )

    for group_key, start, end, group_df in iter_dynamic_groups(df, DYNAMIC_GROUPING):
        # Keep yearly grouping for export organization, but compute values per exact month (YYYY-MM).
        if DYNAMIC_GROUPING == "year":
            months = sorted(group_df["date"].dropna().unique())
            print(f"{group_key}: {len(group_df)} rows | {len(months)} month windows")

            for ym in months:
                month_df = group_df[group_df["date"] == ym]
                month_start, month_end = month_window_from_ym(ym)
                total_batches = math.ceil(len(month_df) / dynamic_batch_size)
                print(
                    f"  {ym}: {len(month_df)} rows | {total_batches} batches | window {month_start}..{month_end}"
                )

                # Keep all requested points even where a dataset has local/temporal no-data.
                dynamic_image = build_dynamic_image(month_start, month_end).unmask(-9999)

                for batch_id, batch in chunks(month_df, dynamic_batch_size):
                    if batch_filter is not None and batch_id not in batch_filter:
                        continue

                    points = df_to_fc(batch, ["location_id", "date"])

                    sampled = dynamic_image.sampleRegions(
                        collection=points,
                        properties=["location_id", "date"],
                        scale=10000,
                        tileScale=dynamic_tile_scale,
                        geometries=False
                    )

                    task = ee.batch.Export.table.toDrive(
                        collection=sampled,
                        description=make_dynamic_description(
                            DYNAMIC_GROUPING, ym, batch_id, dynamic_batch_size
                        ),
                        folder=drive_folder,
                        fileFormat="CSV"
                    )

                    task.start()
                    print(
                        f"Dynamic {ym} batch {batch_id + 1}/{total_batches}: {task.id}"
                    )
                    time.sleep(5)
            continue

        total_batches = math.ceil(len(group_df) / dynamic_batch_size)
        print(f"{group_key}: {len(group_df)} rows | {total_batches} batches")

        # Keep all requested points even where a dataset has local/temporal no-data.
        dynamic_image = build_dynamic_image(start, end).unmask(-9999)

        for batch_id, batch in chunks(group_df, dynamic_batch_size):
            if batch_filter is not None and batch_id not in batch_filter:
                continue

            points = df_to_fc(batch, ["location_id", "date"])

            sampled = dynamic_image.sampleRegions(
                collection=points,
                properties=["location_id", "date"],
                scale=10000,
                tileScale=dynamic_tile_scale,
                geometries=False
            )

            task = ee.batch.Export.table.toDrive(
                collection=sampled,
                description=make_dynamic_description(
                    DYNAMIC_GROUPING, group_key, batch_id, dynamic_batch_size
                ),
                folder=drive_folder,
                fileFormat="CSV"
            )

            task.start()
            print(
                f"Dynamic {group_key} batch {batch_id + 1}/{total_batches}: {task.id}"
            )
            time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export Earth Engine static/dynamic CSV batches."
    )
    parser.add_argument(
        "--mode",
        choices=["all", "static", "dynamic"],
        default="all",
        help="Welche Exporte gestartet werden sollen (default: all).",
    )
    parser.add_argument(
        "--static-csv",
        default=STATIC_CSV,
        help=f"Pfad zur Static-Input-CSV (default: {STATIC_CSV}).",
    )
    parser.add_argument(
        "--dynamic-csv",
        default=DYNAMIC_CSV,
        help=f"Pfad zur Dynamic-Input-CSV (default: {DYNAMIC_CSV}).",
    )
    parser.add_argument(
        "--year-filter",
        default="",
        help="Kommagetrennte Jahresliste fuer Dynamic-Export, z. B. 2016,2017,2021",
    )
    parser.add_argument(
        "--dynamic-batch-size",
        type=int,
        default=DYNAMIC_BATCH_SIZE,
        help="Batch size fuer Dynamic-Export (default: 10000).",
    )
    parser.add_argument(
        "--dynamic-tile-scale",
        type=int,
        default=DYNAMIC_TILE_SCALE,
        help="tileScale fuer Dynamic sampleRegions (default: 1). Hoeher reduziert Memory pro Task.",
    )
    parser.add_argument(
        "--batch-filter",
        default="",
        help="Optional: nur bestimmte Dynamic-Batch-IDs exportieren (z. B. 0,1,9 oder 10-21).",
    )
    parser.add_argument(
        "--batch-filter-source-size",
        type=int,
        default=0,
        help=(
            "Optional: Batchgroesse, auf der --batch-filter basiert. "
            "Beispiel: alte IDs aus 1000er-Batches bei neuem --dynamic-batch-size 500."
        ),
    )
    parser.add_argument(
        "--drive-folder",
        default=EXPORT_DRIVE_FOLDER,
        help="Google Drive Zielordner fuer Exporte (default: beetle_exports).",
    )
    parser.add_argument(
        "--ee-project",
        default=DEFAULT_EE_PROJECT,
        help="Earth Engine/GCP Projekt-ID (default: beetle-db).",
    )
    parser.add_argument(
        "--disable-human-modification",
        action="store_true",
        help="Nutzt einen Sentinel-Wert statt CSP/HM/GlobalHumanModification (fuer Paid-EE-Projekte).",
    )
    args = parser.parse_args()

    init_ee(args.ee_project)

    years = []
    if args.year_filter.strip():
        years = [y.strip() for y in args.year_filter.split(",") if y.strip()]
        invalid = [y for y in years if not y.isdigit() or len(y) != 4]
        if invalid:
            raise ValueError(f"Ungueltige Jahreswerte in --year-filter: {invalid}")

    if args.mode in {"all", "static"}:
        start_static_exports(
            drive_folder=args.drive_folder,
            static_csv=args.static_csv,
            disable_human_modification=args.disable_human_modification,
        )
    if args.mode in {"all", "dynamic"}:
        if args.dynamic_batch_size <= 0:
            raise ValueError("--dynamic-batch-size muss > 0 sein")
        if args.dynamic_tile_scale <= 0:
            raise ValueError("--dynamic-tile-scale muss > 0 sein")
        if args.batch_filter_source_size < 0:
            raise ValueError("--batch-filter-source-size muss >= 0 sein")

        selected_batches = parse_batch_filter(args.batch_filter)
        if selected_batches is not None and args.batch_filter_source_size > 0:
            selected_batches = remap_batch_filter(
                selected_batches,
                args.batch_filter_source_size,
                args.dynamic_batch_size,
            )
            print(f"Batch-Filter remapped: {sorted(selected_batches)}")

        start_dynamic_exports(
            year_filter=years,
            drive_folder=args.drive_folder,
            dynamic_batch_size=args.dynamic_batch_size,
            dynamic_tile_scale=args.dynamic_tile_scale,
            batch_filter=selected_batches,
            dynamic_csv=args.dynamic_csv,
        )