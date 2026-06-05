import ee
import pandas as pd
import time
import math

ee.Initialize(project="beetle-db")

STATIC_CSV = "csv/ee_locations_static.csv"
DYNAMIC_CSV = "csv/ee_location_dates_dynamic.csv"

STATIC_BATCH_SIZE = 10000
DYNAMIC_BATCH_SIZE = 10000
DYNAMIC_GROUPING = "year"  # "month" oder "year"
STATIC_EXPORT_PREFIX = "beetle_static"
DYNAMIC_EXPORT_PREFIX = "beetle_dynamic"
EXPORT_DRIVE_FOLDER = "beetle_exports"
MAX_ROWS = None  # für Test z.B. 1000 setzen, für komplett: None


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


def make_dynamic_description(grouping, group_key, batch_id):
    # YYYY-MM bleibt lesbar, andere Sonderzeichen entfernen wir vorsichtshalber.
    safe_key = str(group_key).replace("/", "_").replace(" ", "_")
    return f"{DYNAMIC_EXPORT_PREFIX}_{grouping}_{safe_key}_batch_{batch_id:04d}"


def build_static_image():
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


def start_static_exports():
    df = pd.read_csv(STATIC_CSV)

    if MAX_ROWS:
        df = df.head(MAX_ROWS)

    # Prevent dropped rows from masked pixels by filling no-data with sentinel values.
    static_image = build_static_image().unmask(-9999)

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
            folder=EXPORT_DRIVE_FOLDER,
            fileFormat="CSV"
        )

        task.start()
        print(f"Static batch gestartet {batch_id + 1}/{total_batches}: {task.id}")
        time.sleep(5)


def build_dynamic_image(start, end):
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    smap_new = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")
    smap_old = ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
    modis = ee.ImageCollection("MODIS/061/MOD13Q1")
    viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    dmsp = ee.ImageCollection("NOAA/DMSP-OLS/NIGHTTIME_LIGHTS")

    era_month = era5.filterDate(start, end)

    temp_c = (
        era_month
        .select("temperature_2m")
        .mean()
        .subtract(273.15)
        .rename("avg_temperature")
    )

    precip_mm = (
        era_month
        .select("total_precipitation_sum")
        .sum()
        .multiply(1000)
        .rename("precipitation")
    )

    dewpoint_c = (
        era_month
        .select("dewpoint_temperature_2m")
        .mean()
        .subtract(273.15)
        .rename("dewpoint_c")
    )

    # Compute relative humidity (%) from temperature and dewpoint (Celsius).
    relative_humidity = temp_c.expression(
        "100 * exp((17.625 * td) / (243.04 + td) - (17.625 * t) / (243.04 + t))",
        {
            "td": dewpoint_c,
            "t": temp_c,
        }
    ).clamp(0, 100).rename("relative_humidity")

    surface_pressure = (
        era_month
        .select("surface_pressure")
        .mean()
        .divide(100)
        .rename("surface_pressure_hpa")
    )

    era5_soil_moisture = (
        era_month
        .select("volumetric_soil_water_layer_1")
        .mean()
        .rename("soil_moisture")
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
    dmsp_month = dmsp.filterDate(start, end)

    empty_night = ee.Image(0).updateMask(ee.Image(0)).rename("nighttime_lights")

    nighttime_lights = ee.Image(
        ee.Algorithms.If(
            viirs_month.size().gt(0),
            viirs_month.select("avg_rad").mean(),
            ee.Algorithms.If(
                dmsp_month.size().gt(0),
                dmsp_month.select("stable_lights").mean(),
                empty_night
            )
        )
    ).rename("nighttime_lights")

    ndvi = (
        modis
        .filterDate(start, end)
        .select("NDVI")
        .mean()
        .multiply(0.0001)
        .rename("ndvi")
    )

    return (
        temp_c
        .addBands(precip_mm)
        .addBands(soil_moisture)
        .addBands(ndvi)
        .addBands(relative_humidity)
        .addBands(surface_pressure)
        .addBands(nighttime_lights)
    )


def start_dynamic_exports():
    df = pd.read_csv(DYNAMIC_CSV)

    if MAX_ROWS:
        df = df.head(MAX_ROWS)

    df["date"] = df["date"].astype(str).str.strip()
    df = df[df["date"].str.match(r"^\d{4}-\d{2}$", na=False)]
    df["year"] = df["date"].str.slice(0, 4).astype(int)

    if DYNAMIC_GROUPING == "month":
        group_count = df["date"].nunique()
    else:
        group_count = df["year"].nunique()

    print(
        f"Dynamic rows: {len(df)} | Grouping: {DYNAMIC_GROUPING} | Groups: {group_count} | Batch size: {DYNAMIC_BATCH_SIZE}"
    )

    for group_key, start, end, group_df in iter_dynamic_groups(df, DYNAMIC_GROUPING):
        total_batches = math.ceil(len(group_df) / DYNAMIC_BATCH_SIZE)
        print(f"{group_key}: {len(group_df)} rows | {total_batches} batches")

        # Keep all requested points even where a dataset has local/temporal no-data.
        dynamic_image = build_dynamic_image(start, end).unmask(-9999)

        for batch_id, batch in chunks(group_df, DYNAMIC_BATCH_SIZE):
            points = df_to_fc(batch, ["location_id", "date"])

            sampled = dynamic_image.sampleRegions(
                collection=points,
                properties=["location_id", "date"],
                scale=10000,
                geometries=False
            )

            task = ee.batch.Export.table.toDrive(
                collection=sampled,
                description=make_dynamic_description(
                    DYNAMIC_GROUPING, group_key, batch_id
                ),
                folder=EXPORT_DRIVE_FOLDER,
                fileFormat="CSV"
            )

            task.start()
            print(
                f"Dynamic {group_key} batch {batch_id + 1}/{total_batches}: {task.id}"
            )
            time.sleep(5)


if __name__ == "__main__":
    start_static_exports()
    start_dynamic_exports()
    pass