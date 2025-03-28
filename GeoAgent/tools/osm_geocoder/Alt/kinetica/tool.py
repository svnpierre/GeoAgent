from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain_core.prompts import ChatPromptTemplate
from typing import Any,Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.kinetica import ChatKinetica
from langchain_community.chat_models.kinetica import ChatKinetica, KineticaUtil
from langchain_community.chat_models.kinetica import ChatKinetica,KineticaUtil
from langchain_core.messages import (
    SystemMessage,
)
import json
from langchain_core.prompts import ChatPromptTemplate
import os 
from tools.osm_geocoder.outputParser import KineticaCustomSqlOutputParser

from shapely.geometry import box
from shapely import to_wkt
import geopandas as gpd
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

# Tool für Text-to-SQL mit SQL-GPT von Kinetica. Ermöglicht das Abfragen von OSM-Daten sowie das Geokodieren von Adressen/Orten zu Punkten/(Multi-)Polygonen. Das Ergebnis wird als GeoDataFrame zum Python Env hinzugefügt. Ein GDF enthält Daten einer thematischen Kategorie und eines Geometrietyps.

def create_kinetica_chain(): # Erstellt eine RunnableSequence die auf Basis eines Eingabestrings SQL und einen GeoDataFrame erstellt. 
    kinetica_llm = ChatKinetica()
        # Prompt erstellen
    kinetica_ctx = kinetica_llm.load_messages_from_context("osm_geocoding")
    
    # SQL-GPT-Nutzer
    kinetica_url = os.getenv("KINETICA_URL")
    sql_gpt_passwd = os.getenv("KINETICA_SQL_GPT_PASSWD")
    sql_gpt = os.getenv("KINETICA_SQL_GPT")
    kdbc = KineticaUtil.create_kdbc(passwd=sql_gpt_passwd, user=sql_gpt, url=kinetica_url)
    prompt_sql = f"GENERATE PROMPT WITH OPTIONS (CONTEXT_NAMES = 'osm_geocoding')" 
    response = kdbc.execute_sql_and_decode(prompt_sql,limit=1, get_column_major=False)
    record = response["records"][0]
    response_dict = {}
    for col, val in record.items():
        response_dict[col] = val
    prompt = response_dict["Prompt"]
    prompt_json = json.loads(prompt)
    rules = prompt_json["payload"]["context"][5]["rules"] # Globale Regeln an SystemMessage anhängen
    rules = ["-- * " + r for r in rules]
    system_msg = str(kinetica_ctx[0].content) + "\n\nRULES TO APPLY GLOBALLY:\n" + "\n".join(rules)
    kinetica_ctx[0] = SystemMessage(content=system_msg)
    kinetica_ctx.append(("human", "Generate the SQL for the following query: {input}"))
    kinetica_prompt = ChatPromptTemplate.from_messages(kinetica_ctx) 

    return kinetica_prompt | kinetica_llm | KineticaCustomSqlOutputParser(kdbc=kinetica_llm.kdbc)
    
class KineticaInput(BaseModel):
    query: str = Field(description="Start the request with 'Show me …'. Describe the elements to be retrieved and how the output should look in short sentences. Name the elements and specify their characteristics in brackets: - To filter by one or more geometry types, specify the types with Types: type1, type2, type3. Allowed types are Point, Line, Polygon. - To filter by one or more OSM tags, specify the tags with Tags: tag1, tag2,... - To filter by one or more OSM keys, specify the keys with Keys: Key1, Key2,... If geocoding of named places or addresses is needed, specify the geometry type in brackets with Geocoding: type. Allowed types are Point, Polygon. To retrieve polygons of general administrative units without given names, specify the characteristics in brackets with Tags: boundary=administrative, osm-tag: admin_level=<level>. Specify the corresponding level: 4 -> Bundesland (Federal State), 5 -> Regierungsbezirk (Governmental District), 6 -> Stadt-/Landkreis (Urban/Rural District), 7 -> Gemeindeverband (Collective Municipalities), 8 -> Stadtbezirk (City District), 10 -> Stadtteil (Suburb), 11 -> Stadtviertel (Neighborhood) Name the output columns and if the column corresponds to an OSM key, specify the key in brackets with Key: key. ")
    gdfs_bbox: Union[list[str], None] = Field(description="A list of names of GeoDataFrames used to create bounding boxes. You can use this if you need data only in the total bounds of specific GeoDataFrames used for an analysis. This is usefull to avoid unecessary data and to reduce the amount of data. If not provided, the query will be executed on the entire OSM data.")
    gdfs: Union[list[str], None] = Field(description="A list of names of GeoDataFrames. You can use this if the geometries and attributes of specific GeoDataFrames are needed to query osm data, e.g. when only OSM features inside the polygons or in buffers around points of a GeoDataFrame etc. are needed.")

class KineticaTool(BaseTool):
    name: str = "kinetica"
    description: str = "Use this tool to: 1) Analyze OpenStreetMap (OSM) data, such as extracting information or performing spatial analysis. 2) Retrieve OSM data that supports the analysis of GeoDataFrames. 3) Geocode addresses or places to points or polygons. The result of your query should be a single layer, containing data of one geometry type (lines, points, or polygons) and belonging to one specific thematic category."
    args_schema: Type[BaseModel] = KineticaInput 
    kinetica_chain: Any = Field(default_factory=create_kinetica_chain)
    
    def __init__(self, metadata):
        super().__init__(
            kinetica_chain=create_kinetica_chain(),
            metadata=metadata
        )
    
    def _run(self, query, gdfs_bbox, gdfs):
        # Total bounds des GeoDataFrames bestimmen und als WKT in den Propmt integrieren
        if gdfs:
            # Liste von json strings aus GDF-Daten erstellen: jedes dict hat name:str, attriubutes:json und geom:str (wkt)
            json_str_list = []
            examples = ""
            for gdf_name in gdfs:
                gdf = self.metadata["env"][gdf_name]
                for i, row in gdf.iterrows():
                    # Extrahiere den Namen (ersetze 'name' durch den tatsächlichen Spaltennamen)
                    name = gdf
                    attributes = row.drop('geometry').to_dict()  # Entfernt die Geometriespalte
                    geom = str(row['geometry'])  #__geo_interface__
                    json_obj = {
                        'name': name,
                        'attributes': attributes,
                        'geom': geom
                    }
                    
                    if i == 0:
                        examples += f"{gdf_name}: {json_obj['attributes']}\n"
                    json_str_list.append(str(json_obj))
                    
            kinetica_url = os.getenv("KINETICA_URL")
            kinetica_gdf = os.getenv("KINETICA_GDF")
            kinetica_gdf_passwd = os.getenv("KINETICA_GDF_PASSWD")
            kdbc = KineticaUtil.create_kdbc(passwd=kinetica_gdf_passwd, user=kinetica_gdf, url=kinetica_url)
            prompt_sql = f"TRUNCATE TABLE ki_home.gdf;" 
            response = kdbc.execute_sql_and_decode(prompt_sql,limit=1, get_column_major=False)
            kdbc.insert_records(table_name="ki_home.gdf",list_str=json_str_list,list_encoding="json") 
            query += f"Here is an example for an attributes JSON for each GeoDataFrame: {examples}."    
        if gdfs_bbox: # Wert None
            # Bounding-Boxen bestimmen
            bounds_messages = ""
            for _, gdf_name in enumerate(gdfs_bbox):
                gdf = self.metadata["env"][gdf_name]
                minx, miny, maxx, maxy = self.metadata["env"][gdf_name].total_bounds    
                bounds_poly = box(minx, miny, maxx, maxy)
                # WKT mit vier Nachekommastellen 
                bounds_wkt = to_wkt(geometry=bounds_poly, rounding_precision=4)
                bounds_message = f"Bounding box {_}: {bounds_wkt}"
                bounds_messages = bounds_messages + "\n" + bounds_message            
            query += f"Make sure that the queried data intersects the following bounding boxes: '{bounds_messages}'.)"     
        try:  
            response = self.kinetica_chain.invoke({"input": query})# KineticaSqlResponse bestehend aus String und GeoDataFrame
            print("Antwort:", response)
        except Exception as e:
            return f"Kinetica tool not available: {e}"
                       
        # Direkt die Fehlermledung des KineticaCustomSqlOutputParser ausgeben falls keine KineticaSqlResponse zurückgeliefert wird
        if isinstance(response, str):
            return f"Error in executing SQL for the query: {query}. Error: {response}. Adjust the query and recall the kinetica tool."
        
        # GeoDataFrame aus DataFrame erstellen falls nicht None
        if response.dataframe is not None:
            df = response.dataframe
            df["geometry"] = gpd.GeoSeries(df["geometry"])  # Falls nötig, explizit in GeoSeries umwandeln

            gdf = gpd.GeoDataFrame(df, geometry="geometry")  # DataFrame in GeoDataFrame umwandeln
            gdf.set_crs(epsg=4326, allow_override=True)  # CRS setzen (EPSG 4326 = WGS 84)
            gdf = gdf.to_crs(epsg=3857)  # Transformation ins gewünschte CRS (EPSG 3857 = Web Mercator)
            # GeoDataFrame zu env hinzufügen               
            gdfs_num = 0             
            for name, obj in self.metadata["env"].items():
                if isinstance(obj, gpd.GeoDataFrame):
                    gdfs_num += 1
            gdf_name = f"gdf_{gdfs_num}"
            self.metadata["env"][gdf_name] = gdf 
            return f"Query sucessuflly executed. The results are in the GeoDataFrame '{gdf_name}'."   
        else:
            return "Query sucessuflly executed but no results."   
            
            
        
                                        

        
    
    
    
    
    
    
    
    
    
    
    
    
