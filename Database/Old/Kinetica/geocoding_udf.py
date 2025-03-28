from kinetica_proc import ProcData
import gpudb
import pandas as pd
import osmnx as ox
from shapely.geometry import shape
import json

# Caching und Logging deaktivieren
ox.settings.use_cache = False
ox.settings.log_console = False

# ki_home.geocoding leeren, um nur akutelle Ergebnisse zu speichern
response = gpudb.GPUdb(host=['http://' + '127.0.0.1' + ':' + '9191'], username='geocoder', password='8j!2U4Ys').execute_sql('TRUNCATE TABLE ki_home.geocoding;')
print('geocoder')
print(response) # TODO: User geocoder, password 

def geocode(geocode_input):
    """Use the Nominatim API to geocode an adress or place string to a point or polygon WGS84 geometry.
    Args:
        input: A Dict represent an adress or place and the geometry type (either point or polygon) of the geocoding result as a string.    
    """
    results = ox._nominatim._download_nominatim_element(geocode_input["query"], limit=50) # Anfrage an Nominatim-API und bis zu 50 Ergebnisse als Liste von Dicts abrufen
    
    # geometry-Schlüssel auf None setzen, falls keine Ergebnisse
    if len(results) == 0:
        geocode_input["geometry"] = None
        return geocode_input
    
    # Erstes vorhandenes Polygon abrufen und an geometry zuweisen, ggf. geometry auf None setzen
    if geocode_input["type"] == "polygon":
        try: 
            polygon = ox.geocoder._get_first_polygon(results)  # Erstes vorhandenes Polygon
            geocode_input["geometry"] = shape(polygon["geojson"]).wkt # WKT des Polygons nutzen
        except TypeError: # Kein Polygon gefunden
            geocode_input["geometry"] = None            
        return geocode_input
            
    # Erstes Ergebnis nutzen, direkt an geometry zuweisen falls Punkt, ansonsten Polygonzentroid nutzen 
    if geocode_input["type"] == "point":
        point_types = ["Point", "MultiPoint"]
        polygon_types = ["Polygon", "MultiPolygon"]
        result = results[0]       
        if result["geojson"]["type"] in point_types:
            geocode_input["geometry"] = shape(result["geojson"]).wkt # Punkt nutzen 
        elif result["geojson"]["type"] in polygon_types: 
            polygon_shape = shape(result["geojson"])
            geocode_input["geometry"] = polygon_shape.centroid.wkt # Polygonzentroid nutzen
        else:
            geocode_input["geometry"] = None
        return geocode_input

proc_data = ProcData() # ProcData-Objekt erstellen
geocode_inputs = json.loads(proc_data.params["input"]) # Den String des input-Parameters einlesen, entspricht einer Liste mit mindestens einem Dict 
output_table = proc_data.output_data[0] # Erste OutputTable-Objekt (entspricht der Tabelle ki_home.geocoding) abrufen
output_table.size = len(geocode_inputs) # Festlegen um wie viele Einträge die Tabelle erweitert wird, um Speicherplatz zu reservieren

# Jedes geocode_input Dict mit geocode() um einen geometry-Schlüssel (Geocodinggeometryetrie) erweitern und Daten in die Ausgabetabelle schreiben
for geocode_input in geocode_inputs: 
    print(geocode_input)
    geocode_output = geocode(geocode_input) 
    proc_data.output_data[0]["id"].append(geocode_output["id"])
    proc_data.output_data[0]["query"].append(geocode_output["query"])
    proc_data.output_data[0]["type"].append(geocode_output["type"])
    proc_data.output_data[0]["geometry"].append(geocode_output["geometry"])

"""
# Verwendung eines DataFrames zum Speichern der Daten (funktioniert nicht, da Werte von Spalten mit Datentypen variabler Längen z.B. Strings nicht geschrieben werden können)
df = pd.DataFrame(columns=['query', 'type', 'geometry'])
geocode_output = geocode({"query":proc_data.params["query"],"type":proc_data.params["type"]}) 
df.loc[len(df)] = [geocode_output['query'], geocode_output['type'], geocode_output['geometry']]
df = df.astype({ 'query': 'string' })
df = df.astype({ 'type': 'string' })
df = df.astype({ 'geometry': 'string' })

output_table = proc_data.output_data[0]
output_table.size = len(df)

print(df.dtypes)
proc_data.from_df(df, output_table)
"""
proc_data.complete()
