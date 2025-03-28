from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

def create_debugger_chain(llm: BaseLanguageModel): 
    """Erstellt eine RunnableSequence zum Korrigieren eines SQL-Skripts basierend auf einer Aufgabenstellung, dem generierten SQL und der Fehlermeldung."""

    debugger_prompt = ChatPromptTemplate.from_template("""You are an experienced debugger for PostGIS SQLs. Debug the provided SQL.
    You have only access to the 'data'-schema.
    The schema contains the following OSM related tables:
    - The 'data.osm_points'-table holds points derived from OSM nodes. 
    - The 'data.osm_lines'-table hols (multi-)LineStrings derived from OpenStreetMap (OSM) ways or relations. 
    - The 'data.osm_polygons'-table holds (multi-)Polygons derived from closed OpenStreetMap (OSM) ways or relations.  
    
    Each of these tables has the following columns:
    - 'aerialway' (text): The value of the aerialway key.  
    - 'aeroway' (text): The value of the aeroway key.  
    - 'amenity' (text): The value of the amenity key.  
    - 'barrier' (text): The value of the barrier key.  
    - 'building' (text): The value of the building key.  
    - 'craft' (text): The value of the craft key.  
    - 'emergency' (text): The value of the emergency key.  
    - 'geological' (text): The value of the geological key.  
    - 'geometry' (geometry): The EPSG:25832 (multi-) point or line or polygon geometry.
    - 'healthcare' (text): The value of the healthcare key.  
    - 'highway' (text): The value of the highway key.  
    - 'historic' (text): The value of the historic key.  
    - 'landuse' (text): The value of the landuse key.  
    - 'leisure' (text): The value of the leisure key.  
    - 'man_made' (text): The value of the man_made key.  
    - 'military' (text): The value of the military key.  
    - 'name' (text): The value of the name key.  
    - 'natural' (text): The value of the natural key.  
    - 'office' (text): The value of the office key.  
    - 'osm_id' (bigint): The OSM-ID.  
    - 'other_tags' (JSON): Additional OSM tags stored as key-value pairs in JSON format.  
    - 'place' (text): The value of the place key.  
    - 'power' (text): The value of the power key.  
    - 'public_transport' (text): The value of the public_transport key.  
    - 'railway' (text): The value of the railway key.  
    - 'route' (text): The value of the route key.  
    - 'shop' (text): The value of the shop key.  
    - 'sport' (text): The value of the sport key.  
    - 'telecom' (text): The value of the telecom key.  
    - 'tourism' (text): The value of the tourism key.  
    - 'water' (text): The value of the water key.  
    - 'waterway' (text): The value of the waterway key.  
    
    Example row: 
    {{"aerialway": null, "aeroway": null, "amenity": null, "barrier": null, "building": null, "craft": null, "emergency": null, "geological": null, "geometry": ""POINT(512625.09676340927 5402441.772387527)"", "healthcare": null, "highway": null, "historic": null, "landuse": null, "leisure": null, "man_made": null, "military": null, "name": null, "natural_key": null, "office": null, "osm_id": 461705586, "other_tags": {{"ref": "II", "note": "ref=II (roman number) means ref=2"}}, "place": null,"power": "tower", "public_transport": null, "railway": null, "route": null, "shop": null, "sport": null, "telecom": null, "tourism": null, "water": null, "waterway": null}}

    OSM Tags associated with commonly used keys are stored in a dedicated column for each key. If an object lacks a tag for a key, the column will contain a NULL value. Tags for less common keys are stored in the other_tags column.
    
    Rules to apply for the 'data.osm_points', 'data.osm_lines' and 'data.osm_polygons' tables:
    - Choose based on the query the most suitable tables and the most suitable osm tags or keys.
    - To filter by a key: Use either WHERE key IS NOT NULL or WHERE other_tags ? 'key' IS NOT NULL.
    - To get the value of a key: Use either SELECT key or SELECT other_tags->>'key'.
    - To filter by a tag: Use either WHERE key = 'value' or WHERE other_tags->>'key' = 'value'. 
    - For general administrative units (e.g. federal states) use the "administrative=boundary"-Tag and specify the level for the "admin_level=level-tag: 4 -> Bundesland (Federal State), 5 -> Regierungsbezirk (Governmental District), 6 -> Stadt-/Landkreis (Urban/Rural District), 7 -> Gemeindeverband (Collective Municipalities), 8 -> Stadtbezirk (City District), 10 -> Stadtteil (Suburb), 11 -> Stadtviertel (Neighborhood) 

    The data schema contains the following (Geo-)DataFrames related table:
    - The 'data.dfs'-table stores rows of (Geo-)DataFrames and has the following columns:
    - 'name' (text): The name of a (Geo-)DataFrame.
    - 'attributes' (jsonb): One row of a (Geo-)DataFrame.
    - 'geometry' (geometry): The EPSG:25832 (multi-) point, line or polygon geometry or null if no geometry is available.
    Example of a GeoDataFrame row: '{{"name": "gdf1", "attributes": {{"air_quality_index": "100", "zone": "3A"}}, "geometry": "POINT(512641.09676340927 5402468.772387527)"}}'
    Example of a DataFrame row: '{{"name": "df3", "attributes": {{"name": "Sven", "age": "23"}}, "geometry": "null"}}'

    Rules to apply for the 'data.gdfs' table: 
    - Filter by the 'name' column in a WHERE clause to retrieve data from specific GeoDataFrames.
    - Use attributes->>'attribute' to extract the value of an attribute or attributes->>'attribute' = 'value' to filter an attribute by a specific value.

    For geocoding of addresses or places:
    - Choose the desired geometry type (point or polygon) and use the 'data.geocode' PostgreSQL function to perform geocoding: data.geocode(input).          
    The input must be a string representation of a list containing one or more dictionaries, where each dictionary includes:  
    a) id: An unique identifier for the query.  
    b) query: The address or place to be geocoded.  
    c) type: The desired geometry type ("point" or "polygon"). 
    
    Example function call: data.geocode('[{{"id":"1","query":"Berlin", "type": "polygon"}}, {{"id":"2","query":"Frankfurt", "type":"polygon"}}]'). 
    The function returns a temporary table with the following columns: 
    - id (text): The unique identifier for the query.
    - query(text): The address or place. 
    - type (text): The geometry type ("point" or "polygon"). 
    - geometry (geometry): The ESPG:25832 (point or polygon) geometry of the geocoded address or place.
    You can filter specific geocoding results by their id. 
    
    General rules for all tables of the 'data' schema: 
    - Use precise and descriptive aliases for expressions.
    - Make sure to include the geometry column and other for the query relevant information in the output whenever possible. The name of the geometry output column must be 'geometry'
    - When using values from JSONB columns, ensure to cast them to the appropriate data types when needed with value::target_data_type or CAST(value AS target_data_type).
    - Geometries must be in EPSG:25832.
    
    Return only the debugged SQL script that can be executed directly without any additional explanations or markdown formatting. Now, start debugging of the SQL script based on the original query, the error message and the information about the database.
    
    **Original user query**: {formalized_query}
    **SQL**: {sql}
    **Error message**: {error}""")

    formalizer_chain = debugger_prompt | llm | StrOutputParser() # RunnableSequence

    return formalizer_chain 

