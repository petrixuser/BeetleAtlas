from backend.config.classifications_sql import (
    CLIMATE_CASE_SQL,
    ELEVATION_GROUP_CASE_SQL,
    VEGETATION_CASE_SQL,
)

MAX_CLUSTERS = 5000


def _normalized_worldclim_bio01_sql(location_alias: str = "l") -> str:
    """Return SQL expression that normalizes BIO01 values for map queries."""
    return f"""
                CASE
                    WHEN {location_alias}.worldclim_bio01 IS NULL OR {location_alias}.worldclim_bio01 = -9999 THEN NULL
                    WHEN {location_alias}.worldclim_bio01 > 80 THEN {location_alias}.worldclim_bio01 / 10
                    ELSE {location_alias}.worldclim_bio01
                END
    """


def map_base_cte_sql(base_where_sql: str) -> str:
    """Build base and enriched CTE SQL used by map points and cluster queries."""
    return f"""
        WITH b AS (
            SELECT
                o.gbif_id,
                o.event_date,
                l.latitude AS lat,
                l.longitude AS lng,
                l.elevation,
                l.landcover_class,
                {_normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                bs.scientific_name AS name,
                bs.family,
                COALESCE(
                    NULLIF(l.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', l.city, l.region, l.country), ''),
                    NULLIF(CONCAT_WS(', ', l.region, l.country), ''),
                    l.country,
                    'Unbekannt'
                ) AS location
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            {base_where_sql}
        ),
        enriched AS (
            SELECT
                b.gbif_id,
                b.event_date AS observedAt,
                b.name,
                b.lat,
                b.lng,
                b.elevation,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation,
                {ELEVATION_GROUP_CASE_SQL} AS elevationGroup,
                b.family,
                b.location
            FROM b
        )
    """


def map_clusters_sql(base_where_sql: str, where_sql: str) -> str:
    """Build SQL for aggregated map clusters over the enriched CTE."""
    return f"""
        {map_base_cte_sql(base_where_sql)}
        SELECT
            AVG(e.lat) AS lat,
            AVG(e.lng) AS lng,
            COUNT(*) AS count
        FROM enriched e
        {where_sql}
        GROUP BY FLOOR(e.lat / :cell), FLOOR(e.lng / :cell)
        ORDER BY count DESC
        LIMIT :max_clusters
    """


def map_points_sql(base_where_sql: str, where_sql: str) -> str:
    """Build SQL for non-clustered map points over the enriched CTE."""
    return f"""
        {map_base_cte_sql(base_where_sql)}
        SELECT
            e.gbif_id,
            e.name AS speciesName,
            e.lat,
            e.lng,
            e.elevation,
            e.climate,
            e.vegetation,
            e.observedAt
        FROM enriched e
        {where_sql}
        ORDER BY e.gbif_id
        LIMIT :limit
    """
