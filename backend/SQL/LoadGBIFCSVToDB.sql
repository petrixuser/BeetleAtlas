USE beetle_db;

SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE media;
TRUNCATE TABLE observation;
TRUNCATE TABLE location;
TRUNCATE TABLE beetle_species;

LOAD DATA INFILE '/var/lib/mysql-files/beetle_species.csv'
INTO TABLE beetle_species
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(beetle_id, taxon_id, family, genus, specific_epithet, scientific_name, scientific_name_authorship);

LOAD DATA INFILE '/var/lib/mysql-files/location.csv'
INTO TABLE location
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(location_id, latitude, longitude, coordinate_uncertainty, country, region, city, verbatim_locality,
 elevation, slope, landcover_class, soil_ph, soil_organic_carbon, worldclim_bio01, worldclim_bio12,
 distance_to_water_m, ecoregion_id, biome_id, human_modification);

LOAD DATA INFILE '/var/lib/mysql-files/observation.csv'
INTO TABLE observation
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(gbif_id, recorded_by, catalogue_number, identification_id, identified_by,
 beetle_id, taxon_id, location_id, @event_date, verbatim_event_date, basis_of_record,
 dataset_name, institution_code, image_available)
SET
 event_date = @event_date,
 event_date_parsed = CASE
	 WHEN @event_date IS NULL OR TRIM(@event_date) = '' THEN NULL
	 WHEN @event_date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(@event_date, '%Y-%m-%d')
	 ELSE NULL
 END;

LOAD DATA INFILE '/var/lib/mysql-files/media.csv'
INTO TABLE media
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(media_id, gbif_id, image_url, `references`, creator, publisher, rights_holder, license);

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'beetle_species' AS table_name, COUNT(*) AS rows_count FROM beetle_species
UNION ALL SELECT 'location', COUNT(*) FROM location
UNION ALL SELECT 'observation', COUNT(*) FROM observation
UNION ALL SELECT 'media', COUNT(*) FROM media;
