import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import psycopg2
from shapely import wkt, wkb
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional, Sequence, Type, Union, cast

from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables.base import RunnableSequence
from pydantic import BaseModel, Field

from tools.osm_geocoder.postgis.debugger import create_debugger_chain
from tools.osm_geocoder.postgis.writer import create_writer_chain

# .env-Datei laden
load_dotenv(dotenv_path=".env")


# Tool zum Formalisieren von Anfragen sowie Schreiben, Ausführen und Debuggen von SQL 
class DBInput(BaseModel):
    query: str = Field(description="A description in short sentences that specify what should be queried and/or geocoded and how the output should look. Include infos to geometry types. If (Geo-)DataFrames are involved in the query, include their names and relevant attributes as well as their datatypes.")
    dfs: Union[list[str], None] = Field(description="A list of names of (Geo-)DataFrames whose attributes and/or geometries are involved in the query.")

# LLM und Env als Metadaten
class DBTool(BaseTool):
    name: str = "DatabaseTool"
    description: str = "Use this tool to query OpenStreetMap and/or to geocode adresses/places to points or polygons. The result of the query is a new single (Geo-)DataFrame. A geoDataFrame which should contains data of one geometry type (line, point, or polygon) and belonging to one specific thematic."
    args_schema: Type[BaseModel] = DBInput
    llm: BaseLanguageModel
    writer_chain: RunnableSequence = Field(default_factory=lambda: create_writer_chain(None))
    debugger_chain: RunnableSequence = Field(default_factory=lambda: create_debugger_chain(None))
    
    def __init__(self, llm: BaseLanguageModel, **kwargs):
        super().__init__(
            llm=llm,
            writer_chain=create_writer_chain(llm),
            debugger_chain=create_debugger_chain(llm),
            **kwargs
        )
        # Um GeoDataFrames zum Env hinzuzufügen 
        #self.python_repl.locals = self.metadata["env"]
    
    def _run(self, query, dfs):
        formalized_query = query
        #formalized_query = self.formalizer_chain.invoke({"query":query}) # Query mit OSM-Tags, OSM-Keys, Infos zu df-Attributen und Geocoding formalisieren
        db=os.getenv("POSTGIS_DB")
        user=os.getenv("POSTGIS_USER")
        password=os.getenv("POSTGIS_PASSWORD") 
        host = os.getenv("POSTGIS_HOST")
        port=os.getenv("POSTGIS_PORT")

        conn = psycopg2.connect(
                dbname=db,
                user=user,
                password=password,
                host=host,
                port=port
            )
        cur = conn.cursor()
        if dfs:
            dfs_data = []
            examples = []
            
            for df_name in dfs:
                if df_name not in self.metadata["env"]:
                    return f"Error: {df_name} not found in the environment."
                df = self.metadata["env"][df_name]
                if isinstance(df, pd.DataFrame):
                    geometry_info = f"The DataFrame {df_name} has no geometries, so the geometry column in data.gdfs is empty."
                    for i, row in df.iterrows():
                        # JSON dict for all columns
                        attributes = row.replace({np.nan: None}).to_dict()
                        geom = None  # Default value for non-geometry cases
                        
                        if isinstance(df, gpd.GeoDataFrame):
                            try:
                                geom_column = df.geometry.name
                                geom_type = df.geometry.geom_type.iloc[0] if not df.geometry.empty else "unknown"
                                geometry_info = (f"The GeoDataFrame {df_name} contains geometries of type '{geom_type}', "
                                                "so the geometry column in data.gdfs is not empty.")
                                geom_value = attributes.pop(geom_column)
                                geom = str(geom_value) if geom_value is not None and not pd.isna(geom_value) else None
                            except AttributeError:
                                return (f"The GeoDataFrame {df_name} has no active geometry column. "
                                        "Add an active geometry column with df.set_geometry.")
                        
                        # JSON conversion of attributes
                        attributes_json = json.dumps(attributes)
                        
                        if i == 0:
                            # Include example row with geometry type in examples
                            examples.append(f"- {geometry_info} Example attributes JSON of {df_name}: {attributes_json}")
                        
                        # Tuple of df data for database loading
                        dfs_data.append((df_name, attributes_json, geom))
                else:
                    return f"Error: {df_name} is of type {type(df)}."
            
            # Beispiele als String zusammenfassen
            examples_str = "\n".join(examples)
            
            # Tabelle leeren und Daten einfügen
            try: 
                cur.execute("TRUNCATE TABLE data.dfs;")
                conn.commit()
                
                # Batch-Insertion aller GeoDataFrame-Daten
                insert_sql = """
                INSERT INTO data.dfs (name, attributes, geometry)
                VALUES (%s, %s, ST_GeomFromText(%s, 25832))
                """
                cur.executemany(insert_sql, dfs_data)
                conn.commit()
            except Exception as e:
                cur.execute("ROLLBACK")  # Transaktion zurücksetzen
                conn.rollback()  # Verbindung ebenfalls zurücksetzen
                return f"Error transferring the GeoDataFrame(s) {dfs} to the database: {str(e)}"

            formalized_query += f"Here is an example attributes JSON for each GeoDataFrame: {examples_str}." 
            # dfs_data zeilenweise mit psycopg2 in Datenbank schreiben
        try:
            query_sql = self.writer_chain.invoke({"formalized_query":formalized_query}).replace("```sql\n", "").replace("\n```", "") # SQL schreiben, ggf. sql Mardwown formating entfernen 
        except Exception as e:
            return f"Error to generate the SQL query: {str(e)}"       
        response = {"sql": query_sql, "error": None, "result": None}
        
        try: # Generiertes SQL ausführen
            cur.execute(query_sql)
            response["result"] = cur.fetchall()
            response["colnames"] = [desc[0] for desc in cur.description]
        except Exception as e:
            response["error"] = str(e)
            cur.execute("ROLLBACK")  # Transaktion zurücksetzen
        
        for _ in range(5): # SQL ggf. bis zu fünfmal debuggen
            if not response["error"]: # Kein Fehler 
                if response["result"]: # Keine leere Liste
                    df = pd.DataFrame(response["result"], columns=response["colnames"])

                    # Falls eine 'geometry'-Spalte vorhanden ist, diese in geometrische Objekte umwandeln:
                    if 'geometry' in df.columns:
                        # Konvertiere den WKB-Hex-String in ein Shapely-Geometrieobjekt
                        df['geometry'] = df['geometry'].apply(lambda geom: wkb.loads(geom, hex=True))
                        # Erstelle einen GeoDataFrame mit dem gewünschten CRS (EPSG:25932)
                        df = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:25832")
                        #df["geometry"] = df["geometry"].apply(lambda geom: geom.wkt)
                    dfs_num = 0             
                    for name, obj in self.metadata["env"].items():
                        if isinstance(obj, pd.DataFrame): # Trifft auf (Geo-)DataFrames zu
                            dfs_num += 1
                    df_name = f"df_{dfs_num}"
                    self.metadata["env"][df_name] = df        
                    cur.close()
                    conn.close() 
                    return f"Query successfully executed. The results are in the (Geo-)DataFrame '{df_name}'."
                else:
                    cur.close()
                    conn.close() 
                    return "Query sucessuflly executed but no results."  
            response["sql"] = self.debugger_chain.invoke({"sql":response["sql"], "formalized_query":formalized_query, "error":response["error"]}).replace("```sql\n", "").replace("\n```", "") # SQL debuggen, ggf. sql-Markdown-Formatting entfernen
            
            try: # Verbessertes SQL ausführen
                cur.execute("ROLLBACK")  # Transaktion zurücksetzen
                cur.execute(response["sql"])
                response["result"] = cur.fetchall() 
                response["colnames"] = [desc[0] for desc in cur.description]
                response["error"] = None
            except Exception as e:
                response["error"] = str(e)
        
        cur.close()
        conn.close() 
        # Tool beenden falls nach fünfmal debuggen der Code nicht funktioniert
        return f"The analysis failed because the sql could not be debugged successfully. Previously provided query: {query} and GeoDataFrames: {dfs}." 
    
    
        
    