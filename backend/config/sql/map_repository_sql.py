"""SQL-Builder fuer Kartenpunkte und Cluster-Abfragen."""
MAX_CLUSTERS = 5000


def map_base_cte_sql(base_where_sql: str) -> str:
    """Liefert das base-/enriched-CTE-SQL, das Kartenpunkte und Cluster-Abfragen nutzen.
    Liest aus der vorberechneten Tabelle map_point_read fuer schnelle bbox-/Filter-Scans.
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
                m.koppen_code,
                m.vegetation_zone,
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
                b.koppen_code,
                b.vegetation_zone,
                b.elevationGroup,
                b.family,
                b.location,
                b.country
            FROM b_filtered b
        )
    """


def map_clusters_sql(base_where_sql: str, where_sql: str) -> str:
    """Liefert das SQL fuer aggregierte Karten-Cluster ueber das enriched-CTE."""
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
    """Liefert das SQL fuer nicht geclusterte Kartenpunkte ueber das enriched-CTE."""
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
    """Liefert das SQL fuer die Gesamtzahl nicht geclusterter Kartenpunkte ueber das enriched-CTE."""
    return f"""
        {map_base_cte_sql(base_where_sql)}
        SELECT COUNT(*) AS total
        FROM enriched e
        {where_sql}
    """



def list_read_map_clusters_sql(where_sql: str) -> str:
    """Aggregiert Cluster ueber beetle_list_read fuer read-model-gestuetzte Filter."""
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
    """Nicht geclusterte Kartenpunkte ueber beetle_list_read fuer read-model-Filter."""
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
    """Gesamtzahl nicht geclusterter Kartenpunkte ueber beetle_list_read fuer read-model-Filter."""
    return f"""
        SELECT COUNT(*) AS total
        FROM beetle_list_read e
        {where_sql}
    """
