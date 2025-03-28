# Werkzeug zum Planen, Generieren, Ausführen und Korrigieren von Python-Skripten basierend auf GeoDataFrames und einer Aufgabe mit einem LLM

import pandas as pd
import geopandas as gpd
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Optional
from langchain_core.runnables.base import RunnableSequence
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from tabulate import tabulate
from tools.analyst.planner import create_planner_chain
from tools.analyst.debugger import create_debugger_chain
from tools.analyst.programmer import create_programmer_chain
from tools.analyst.python_repl import PythonREPL 

def _get_default_python_repl() -> PythonREPL: 
    """Der standardmäßig zu verwendende PythonREPL"""
    return PythonREPL(_globals=globals(), locals={})

def get_infos(gdf_names, env):
    """Abrufen von relevanten GeoDataFrame-Informationen"""
    infos = []
    for name in gdf_names:
        # GDF-Objekt aus Objektmapping abrufen
        df = env[name] 
        if isinstance(df, pd.DataFrame):                   
            df_name = f"**Name of the Dataframe: {name}**"
            shape = f"- Number of rows: {df.shape[0]}\n- Number of columns: {df.shape[1]}\n"
            geometry_info = "No geometry column."
            spalten = "\n- Column data types:"
            spaltentypen = pd.DataFrame([df.dtypes], index=["dtypes"])
            spaltentypen = tabulate(spaltentypen, headers="keys", tablefmt="github")
            zeilen = "- First 3 rows:"
            head = df.head(3).copy()
            
            if isinstance(df, gpd.GeoDataFrame):
                df_name = f"**Name of the GeoDataFrame: {name}**"
                try:
                    geometry_column = df.geometry.name
                    geometry_info = f"Active geometry column: {df.geometry.name}" 
                    head[geometry_column] = df[geometry_column].apply(lambda x: x.geom_type)
                except AttributeError as e:
                    geometry_column = f"No existing columns with geometry data type. You must add a geometry column as the active geometry column with df.set_geometry."
                except Exception as e:
                    geometry_column = f"Error: {e}"   
                    
            head = tabulate(head, headers="keys", tablefmt="github")
            #head = head.to_html()               
            info = "\n".join([df_name,shape, geometry_info, zeilen, head, spalten, spaltentypen])  
            infos.append(info)   
    return "\n\n".join([info for info in infos])

# Erlaubte Eingabe für das Werkzeug: Aufgabenbeschreibung und Liste von (Geo-)DataFrames-Namen
class AnalystInput(BaseModel):
    task: str = Field(description="A detailed description of the analysis task.")
    gdfs: List[str] = Field(description="A list of names of the available (Geo-)DataFrames required for the analysis task.")

# Erstellung des Werkzeugs
class AnalystTool(BaseTool):
    name: str = "AnalystTool"
    description: str = "Use this tool for a complex task that require detailed planning or multiple steps to complete. Before using this tool, ensure that all additonal required data (e.g. geocoding results or OSM data) is already available as (Geo-)DataFrames. Ensure that GeoDataFrames has a geometry column. Input must be a detailed description of the analysis task and a list of names of all (Geo-)DataFrames which you can directly access required to solve the task."
    args_schema: Type[BaseModel] = AnalystInput
    
    llm: BaseLanguageModel
    env: Optional[Dict] = Field(default_factory=dict)
    python_repl: PythonREPL = Field(default_factory=_get_default_python_repl)
    planner_chain: RunnableSequence = Field(default_factory=lambda: create_planner_chain(None))
    programmer_chain: RunnableSequence = Field(default_factory=lambda: create_programmer_chain(None))
    debugger_chain: RunnableSequence = Field(default_factory=lambda: create_debugger_chain(None))
    
    def __init__(self, llm: BaseLanguageModel, **kwargs):
        super().__init__(
            llm=llm,
            python_repl=_get_default_python_repl(),
            planner_chain=create_planner_chain(llm),
            programmer_chain=create_programmer_chain(llm),
            debugger_chain=create_debugger_chain(llm),
            **kwargs
        )
        
        self.python_repl.locals = self.metadata["env"] # Zugriff auf Objektmapping
    
    def _run(self, task, gdfs): 
        """Startet die Analyst-Chain: Skript planen. ausführen, ggf. bis zu fünfmal korrigieren"""
        gdf_infos = get_infos(gdfs, self.metadata["env"])
        
        plan = self.planner_chain.invoke({"task":task, "gdf_infos":gdf_infos}) #Plan erstellen
        code = self.programmer_chain.invoke({"task":task, "gdf_infos":gdf_infos, "plan":plan, }).replace("```python\n", "").replace("\n```", "") # Code generieren, Python-Markdown-Formatting aus LLM-Antwort entfernen
        response = eval(self.python_repl.run(code)) # Code ausführen und response-Dict(result, code, error) abrufen
        
        for _ in range(5): # Code ggf. bis zu fünfmal debuggen
            if response["error"] is None: # Code wurde ohne Exception ausgeführt
                return f"Analysis finished: {response['result']}"
            code = self.debugger_chain.invoke({"task":task, "plan":plan, "gdf_infos":gdf_infos, "code":response["code"], "error":response["error"]}) # Code debuggen 
            
            response = eval(self.python_repl.run(code)) # Korrigierten Code ausführen
        # Tool beenden, falls nach fünfmal korrigieren der Code nicht funktioniert
        return f"The analysis failed because the code could not be debugged successfully. Make sure that all required data is available, all relevant (Geo-)DataFrames are provided, and the task description is clear and sufficient to solve the task. Then call the tool again. Previously provided (Geo-)DataFrames: {gdfs}. Previously provided task: {task}." 
