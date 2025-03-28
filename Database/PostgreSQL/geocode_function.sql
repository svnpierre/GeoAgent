-- FUNCTION: public.geocode(json)

-- DROP FUNCTION IF EXISTS public.geocode(json);

CREATE OR REPLACE FUNCTION data.geocode(
	geocode_json json)
    RETURNS TABLE(id text, query text, type text, geometry geometry) 
    LANGUAGE 'plpython3u'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$

import json
import osmnx as ox
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.ops import transform
from pyproj import Transformer

# Transformer für 4326 -> 25832 erstellen
transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)

def transform_wkt(wkt_geometry):
    """Transformiert eine WKT-Geometrie von EPSG:4326 nach EPSG:25832"""
    geom = shape(wkt_geometry)
    transformed_geom = transform(transformer.transform, geom)
    return transformed_geom.wkt

def geocode(geocode_inputs):
    geocode_outputs = []
    for geocode_input in geocode_inputs:
        results = ox._nominatim._download_nominatim_element(geocode_input["query"], limit=50)
        if len(results) == 0:
            geocode_input["geometry"] = None
            geocode_outputs.append(geocode_input)
            continue

        if geocode_input["type"] == "polygon":
            try:
                polygon = ox.geocoder._get_first_polygon(results)
                wkt = shape(polygon["geojson"]).wkt
                transformed_wkt = transform_wkt(shape(polygon["geojson"]))
                geocode_input["geometry"] = "SRID=25832;" + transformed_wkt
            except TypeError:
                geocode_input["geometry"] = None            
            geocode_outputs.append(geocode_input)
            continue

        if geocode_input["type"] == "point":
            result = results[0]
            if result["geojson"]["type"] in ["Point", "MultiPoint"]:
                wkt = shape(result["geojson"]).wkt
                transformed_wkt = transform_wkt(shape(result["geojson"]))
                geocode_input["geometry"] = "SRID=25832;" + transformed_wkt
            elif result["geojson"]["type"] in ["Polygon", "MultiPolygon"]:
                polygon_shape = shape(result["geojson"])
                wkt = polygon_shape.centroid.wkt  # Mittelpunkt der Fläche als Punkt verwenden
                transformed_wkt = transform_wkt(polygon_shape.centroid)
                geocode_input["geometry"] = "SRID=25832;" + transformed_wkt
            else:
                geocode_input["geometry"] = None
            geocode_outputs.append(geocode_input)

    return geocode_outputs
    
data = json.loads(geocode_json)
results = geocode(data)
return [(r["id"], r["query"], r["type"], r["geometry"]) for r in results]
$BODY$;

ALTER FUNCTION data.geocode(json)
    OWNER TO postgres;

--SELECT * FROM data.geocode('[{"id": "1", "query": "Eisingen, Baden", "type": "polygon"},{"id": "2", "query": "Stuttgart", "type": "point"},{"id": "3", "query": "Pforzheim", "type": "point"}]')