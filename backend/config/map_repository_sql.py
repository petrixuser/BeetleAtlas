MAX_CLUSTERS = 5000


def map_base_cte_sql(base_where_sql: str) -> str:
    """Build base and enriched CTE SQL used by map points and cluster queries.

    Reads from the precomputed map_point_read table for fast bbox/filter scans.
    """
    return f"""
        WITH b AS (
            SELECT
                m.source_type,
                m.record_id,
                m.entity_id,
                m.gbif_id,
                m.observed_at AS event_date,
                m.lat,
                m.lng,
                m.elevation,
                m.climate,
                m.vegetation,
                m.elevation_group AS elevationGroup,
                m.species_name AS name,
                m.family,
                m.location,
                m.country
            FROM map_point_read m
        ),
        b_filtered AS (
            SELECT *
            FROM b
            {base_where_sql}
        ),
        enriched AS (
            SELECT
                b.source_type,
                b.record_id,
                b.entity_id,
                b.gbif_id,
                b.event_date AS observedAt,
                b.name,
                b.lat,
                b.lng,
                b.elevation,
                b.climate,
                b.vegetation,
                b.elevationGroup,
                b.family,
                b.location,
                b.country
            FROM b_filtered b
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
            e.entity_id,
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
        ORDER BY e.entity_id
        LIMIT :limit
        OFFSET :offset
    """


def map_points_total_sql(base_where_sql: str, where_sql: str) -> str:
    """Build SQL for total non-clustered map points over the enriched CTE."""
    return f"""
        {map_base_cte_sql(base_where_sql)}
        SELECT COUNT(*) AS total
        FROM enriched e
        {where_sql}
    """


# --- Clustering directly over the beetle_list_read read model ----------------
# map_point_read lacks has_image/observed_year columns, so filtered map queries
# that use those (or the compact bands) cluster over beetle_list_read instead,
# which carries every column the compact list filters reference (e-alias). This
# gives full-dataset clustering for image/year filters without a schema change.

def list_read_map_clusters_sql(where_sql: str) -> str:
    """Aggregate clusters over beetle_list_read for read-model-backed filters."""
    return f"""
        SELECT
            AVG(e.lat) AS lat,
            AVG(e.lng) AS lng,
            COUNT(*) AS count
        FROM beetle_list_read e
        {where_sql}
        GROUP BY FLOOR(e.lat / :cell), FLOOR(e.lng / :cell)
        ORDER BY count DESC
        LIMIT :max_clusters
    """


def list_read_map_points_sql(where_sql: str) -> str:
    """Non-clustered map points over beetle_list_read for read-model filters."""
    return f"""
        SELECT
            e.entity_id,
            e.gbif_id,
            e.name AS speciesName,
            e.lat,
            e.lng,
            e.elevation,
            e.climate,
            e.vegetation,
            e.observed_at AS observedAt
        FROM beetle_list_read e
        {where_sql}
        ORDER BY e.entity_id
        LIMIT :limit
        OFFSET :offset
    """


def list_read_map_points_total_sql(where_sql: str) -> str:
    """Total non-clustered map points over beetle_list_read for read-model filters."""
    return f"""
        SELECT COUNT(*) AS total
        FROM beetle_list_read e
        {where_sql}
    """
