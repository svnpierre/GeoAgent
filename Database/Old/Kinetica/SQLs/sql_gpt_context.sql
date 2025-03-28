CREATE CONTEXT "ki_home"."osm_geocoding" (
    TABLE = ki_home.points,
    COMMENT = 'This table holds points from OpenStreetMap (OSM) nodes. OSM Tags associated with commonly used keys are stored in a dedicated column for each key. If an object lacks a tag for a key, the column will contain a NULL value. Tags for less common keys are stored in the other_tags column.',
    COMMENTS = (
        aerialway = 'The value of the aerialway key.',
        aeroway = 'The value of the aeroway key.',
        amenity = 'The value of the amenity key.',
        barrier = 'The value of the barrier key.',
        building = 'The value of the building key.',
        craft = 'The value of the craft key.',
        emergency = 'The value of the emergency key.',
        geological = 'The value of the geological key.',
        geometry = 'The WKT of the point geometry.',
        healthcare = 'The value of the healthcare key.',
        highway = 'The value of the highway key.',
        historic = 'The value of the historic key.',
        landuse = 'The value of the landuse key.',
        leisure = 'The value of the leisure key.',
        man_made = 'The value of the man_made key.',
        military = 'The value of the military key.',
        name = 'The value of the name key.',
        natural_key = 'The value of the natural key.',
        office = 'The value of the office key.',
        osm_id = 'The OSM-ID.',
        other_tags = 'Additional OSM tags stored as key-value pairs in JSON format.',
        place = 'The value of the place key.',
        power_key = 'The value of the power key.',
        public_transport = 'The value of the public_transport key.',
        railway = 'The value of the railway key.',
        route = 'The value of the route key.',
        shop = 'The value of the shop key.',
        sport = 'The value of the sport key.',
        telecom = 'The value of the telecom key.',
        tourism = 'The value of the tourism key.',
        water = 'The value of the water key.',
        waterway = 'The value of the waterway key.'
    )
),
(
    TABLE = ki_home.lines,
    COMMENT = 'This table stores (multi-)LineStrings derived from OpenStreetMap (OSM) ways or relations. OSM Tags associated with commonly used keys are stored in a dedicated column for each key. If an object lacks a tag for a key, the column will contain a NULL value. Tags for less common keys are stored in the other_tags column.',
    COMMENTS = (
        aerialway = 'The value of the aerialway key.',
        aeroway = 'The value of the aeroway key.',
        amenity = 'The value of the amenity key.',
        barrier = 'The value of the barrier key.',
        building = 'The value of the building key.',
        craft = 'The value of the craft key.',
        emergency = 'The value of the emergency key.',
        geological = 'The value of the geological key.',
        geometry = 'The WKT of the (multi-)linestring geometry.',
        healthcare = 'The value of the healthcare key.',
        highway = 'The value of the highway key.',
        historic = 'The value of the historic key.',
        landuse = 'The value of the landuse key.',
        leisure = 'The value of the leisure key.',
        man_made = 'The value of the man_made key.',
        military = 'The value of the military key.',
        name = 'The value of the name key.',
        natural_key = 'The value of the natural key.',
        office = 'The value of the office key.',
        osm_id = 'The OSM-ID.',
        other_tags = 'Additional OSM tags stored as key-value pairs in JSON format.',
        place = 'The value of the place key.',
        power_key = 'The value of the power key.',
        public_transport = 'The value of the public_transport key.',
        railway = 'The value of the railway key.',
        route = 'The value of the route key.',
        shop = 'The value of the shop key.',
        sport = 'The value of the sport key.',
        telecom = 'The value of the telecom key.',
        tourism = 'The value of the tourism key.',
        water = 'The value of the  water key.',
        waterway = 'The value of the waterway key.'
    )
),
(
    TABLE = ki_home.polygons,
    COMMENT = 'This table stores (multi-)Polygons derived from closed OpenStreetMap (OSM) ways or relations.  OSM Tags associated with commonly used keys are stored in a dedicated column for each key. If an object lacks a tag for a key, the column will contain a NULL value. Tags for less common keys are stored in the other_tags column.',
    COMMENTS = (
        aerialway = 'The value of the aerialway key.',
        aeroway = 'The value of the aeroway key.',
        amenity = 'The value of the amenity key.',
        barrier = 'The value of the barrier key.',
        building = 'The value of the building key.',
        craft = 'The value of the craft key.',
        emergency = 'The value of the emergency key.',
        geological = 'The value of the geological key.',
        geometry = 'The WKT of the (multi-)polygon geometry.',
        healthcare = 'The value of the healthcare key.',
        highway = 'The value of the highway key.',
        historic = 'The value of the historic key.',
        landuse = 'The value of the landuse key.',
        leisure = 'The value of the leisure key.',
        man_made = 'The value of the man_made key.',
        military = 'The value of the waterway key.',
        name = 'The value of the name key.',
        natural_key = 'The value of the natural key.',
        office = 'The value of the office key.',
        osm_id = 'The OSM-ID.',
        other_tags = 'Additional OSM tags stored as key-value pairs in JSON format.',
        place = 'The value of the place key.',
        power_key = 'The value of the power_key key.',
        public_transport = 'The value of the public_transport key.',
        railway = 'The value of the railway key.',
        route = 'The value of the route key.',
        shop = 'The value of the shop key.',
        sport = 'The value of the sport key.',
        telecom = 'The value of the telecom key.',
        tourism = 'The value of the tourism key.',
        water = 'The value of the water key.',
        waterway = 'The value of the waterway key.'
    )
),
(
    TABLE = ki_home.geocoding,
    COMMENT = 'This table stores geocoding results of the GEOCODING_UDF User-Defined Table Function (UDTF).',
    COMMENTS = (
        geometry = 'The WKT of the point or (multi-)Polygon geometry.',
        id = 'The id that identifies a result.',
        query = 'The address or place.',
        type = 'The geometry type (point or polygon).'
    )
),
(
    TABLE = ki_home.gdf,
    COMMENT = 'This table stores data of GeoDataFrames.',
    RULES = (
        'To retrieve data from specific GeoDataFrames, filter by the name column in a WHERE clause.',
        'Use JSON_VALUE(attributes, ''$."attribute"'') to extract the value of an attribute or JSON_VALUE(attributes, ''$."attribute"'') = ''value'' to filter an attribute by a specific value.'
    ),
    COMMENTS = (
        attributes = 'All Attributes of one row of a GeoDataFrame stored as key-value-pairs in JSON format.',
        geometry = 'The WKT geometry.',
        name = 'The name identifying the GeoDataFrame.'
    )
),
(
    RULES = (
        'If addresses or places need to be geocoded, the desired geometry types (point or polygon) are specified using ''Geocoding:'' expressions. To perform geocoding, first use the GEOCODING_UDF user-defined table function (UDTF), which writes the results to the ki_home.geocoding table. Then, retrieve the results from this table using the query IDs. How to use the UDTF:  EXECUTE FUNCTION GEOCODING_UDF(   OUTPUT_TABLE_NAMES => OUTPUT_TABLES(''ki_home.geocoding''),    PARAMS => KV_PAIRS(input=''[{"id":"id_value", "query":"query_value", "type":"type_value"}]'') );    - The input argument must be a string representation of a list containing one or more dictionaries, where each dictionary includes:  a) id: An unique identifier for the query.  b) query: The address or place to be geocoded.  c) type: The desired geometry type ("point" or "polygon").',
        '- OSM Keys are specified using ''Keys:'' expressions. To filter by keys use either <WHERE key IS NOT NULL> or <JSON_VALUE(other_tags, ''$."key"'') IS NOT NULL> for each key. To include the values of OSM keys use <SELECT key> or <SELECT JSON_VALUE(other_tags, ''$."key"'')> for keys contained in other_tags. - OSM Tags to be queried are specified using ''Tags:'' expressions. To filter by tags use either <WHERE key=''value''> or <JSON_VALUE(other_tags, ''$."key"'') = ''value''> for each tag.  - The geometry types of the output are specified using ''Types:'' expressions. To filter by types use the point, line and/or polygon table accordingly. - Attributes of GeoDataFrames to be queried are specified using ''Attributes:'' expressions. Use the ki_home.gdf table accordingly.',
        'Make sure to include the geometry column and other for the query relevant information in the output whenever possible.',
        'For queries related to GeoDataFrames, use the gdf table.',
        'Use ST_GEOMFROMTEXT(WKT) to create a geometry from a WKT-String. To create a point geometry from WGS84 (lat, lon) coordinates use ''POINT(lon lat)'' as WKT.',
        'Use precise and descriptive aliases for expressions.',
        'Use ST_DISSOLVE(geometry) to merge multiple geometries into a single geometry if only one is needed.',
        'Use the solution type 1 (sphere) for measurements (lenghts or areas) in geospatial functions.',
        'Enclose subqueries in parentheses.'
    )
),
(
    SAMPLES = (
        'Query all buildings (Keys: building; Types: polygon) with an area more than 150 m2 located inside the geometries of the GeoDataframe gdf_4 which have an air quality index (Attributes: air_quality_index) higher than 175. Output the Name (Keys: name), building type (Keys: name), air quality index (Attributes: air_quality_index) and the geometry.' = 'SELECT b.name, b.building, gdf.air_quality_index, b.geometry
FROM ki_home.polygons b
LEFT JOIN (
    SELECT gdf.geometry, JSON_VALUE(gdf.attributes, ''$.air_quality_index'') AS air_quality_index
    FROM ki_home.gdf gdf
    WHERE gdf.name = ''gdf_4'' 
    AND JSON_VALUE(gdf.attributes, ''$.air_quality_index'') >= 175
) gdf 
ON ST_WITHIN(b.geometry, gdf.geometry)
WHERE b.building IS NOT NULL 
AND ST_AREA(b.geometry) >= 150;',
        'Query all schools (Tags: amenity=school; Types: polygon) located in Berlin (Geocoding: polygon) and Frankfurt (Geocoding: polygon) that are more than 10 km away from hospitals (Tags: amenity=hospital; Geometry: point). Output the name (Keys: name), school type (Keys: school), and the geometry.' = 'EXECUTE FUNCTION GEOCODING_UDF(
    OUTPUT_TABLE_NAMES => OUTPUT_TABLES(''ki_home.geocoding''),
    PARAMS => KV_PAIRS(input=''[{"id":"1","query":"Berlin", "type": "polygon"}, {"id":"2","query":"Frankfurt", "type":"polygon"}]'')
);
SELECT p.name, p.school, p.geometry
FROM ki_home.points p
WHERE amenity = ''school''
AND ST_Intersects(p.geometry, (
    SELECT ST_Dissolve(geometry) 
    FROM ki_home.geocoding 
    WHERE id IN (''1'', ''2'') 
))
AND NOT EXISTS (
    SELECT 1
    FROM ki_home.points h
    WHERE h.amenity = ''hospital''
    AND ST_Distance(p.geometry, h.geometry,1) <= 10000
);',
        'Query for each federal state (Tags: admin_level=4, boundary=administrative; Types: polygon) the number of windmills (Tags: generator:source=wind; Types:point). Output the name (Keys: name),  number of windmills and geometry.' = 'SELECT po.name, COUNT(pt.osm_id) AS count_windmills, po.geometry  
FROM ki_home.points pt 
JOIN ki_home.polygons po ON ST_Intersects(pt.geometry, po.geometry)  
WHERE JSON_VALUE(pt.other_tags, ''$."generator:source"'') = ''wind'' 
AND JSON_VALUE(po.other_tags, ''$."admin_level"'') = ''4''
AND JSON_VALUE(po.other_tags, ''$."boundary"'') = ''administrative''
GROUP BY po.name, po.geometry'
    )
)