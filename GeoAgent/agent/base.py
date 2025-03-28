# Hauptscript: Enthält die Funktion create_geo_agent(), mit der ein AgentExecutor zur Ausführung des GeoAgent erstellt wird. 

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from tabulate import tabulate

from langchain_core.agents import AgentAction
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.tools import BaseTool

from langchain.agents.agent import AgentExecutor, RunnableMultiActionAgent
from langchain.agents.format_scratchpad.tools import format_to_tool_messages
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain.memory import ConversationSummaryBufferMemory

from agent.prompts import getPrompt
from tools.mapper.tool import MapperTool, create_map
from tools.analyst.tool import AnalystTool
from tools.osm_geocoder.postgis.tool import DBTool

# Typalias für Nachrichtenformatierung
MessageFormatter = Callable[[Sequence[Tuple[AgentAction, str]]], List[BaseMessage]]

# Quelle: https://github.com/ShoggothAI/motleycrew/tree/main/motleycrew/agents/langchain
def check_variables(prompt: ChatPromptTemplate):
    missing_vars = (
        {"gdfs_num", "gdfs_infos"}
        .difference(prompt.input_variables)
        .difference(prompt.optional_variables)
    )
    if missing_vars:
        raise ValueError(f"Main prompt missing required variables: {missing_vars}. Prompt: {prompt}")

def create_geo_agent(
    llm: BaseLanguageModel,
    gdfs = [],
    tools: Sequence[BaseTool] = [],
    main_prompt: str = None,
    verbose: bool = False,
    return_intermediate_steps: bool = False,
    max_iterations: Optional[int] = 15,
    max_execution_time: Optional[float] = None,
    early_stopping_method: str = "force",
    agent_executor_kwargs: Optional[Dict[str, Any]] = None,
    handle_parsing_errors=True,
    m = None
) -> Runnable:
    """Erstellt einen AgentExecutor zur Ausführung von GeoAgent. 
    
    Args:
        llm: Haupt-LLM 
        tools: Bereitgestellte Werkzeuge
        main_prompt: Ein eigener Text der als Hauptprompt genutzt werden soll. Muss die Platzhalter gdfs_num, gdfs_infos enthalten.
        memory: Langzeitspeicher für Konversation zwischen Nutzer und Agent
        gdfs: Liste von GeoDataFrames. Leer falls GeoAgent über Streamlit gestartet wird (GeoDataFrames werden über UI hinzugefügt)
        
    Returns:
        Ein AgentExecutor der u.a. den Agenten, die Werkzeuge und den Langzeitspeicher verwaltet. 
    """
    
    try:
        import pandas as pd
        import geopandas as gpd
    except ImportError as e:
        raise ImportError(
            f"Pandas or GeoPandas not found, install it with 'pip install pandas, geopandas'"
        ) 

    # Sicherstellen dass nur gültige GeoDataFrames verwendet werden 
    for _gdf in gdfs if isinstance(gdfs, list) else [gdfs]:
        if not isinstance(_gdf, pd.DataFrame):
            raise ValueError(f"Expected GeoPandas GeoDataFrame, got {type(_gdf)}")
     
    # Dict für ein Name-Objekt-Mapping zur Verwaltung aller Python-Objekte 
    df_locals = {} 
    
    # Bereitgestellte GeoDataFrames zu Objektmapping hinzufügen
    if gdfs is not None:
        if not isinstance(gdfs, list):
            gdfs = [gdfs]
        for n, gdf in enumerate(gdfs):
            df_locals[f"gdf{n + 1}"] = gdf
    
    # Für die direkte Ausführung einfacher Python-Befehle.
    python_repl_tool = PythonREPLTool()
    python_repl_tool.python_repl.locals = df_locals # Werkzeug greift direkt auf Objektmapping zu
    python_repl_tool.return_direct = False
    python_repl_tool.description = "Use this Python shell to interact with (Geo-)DataFrames and to execute simple Python commands. Always use print() to get the output of variables or commands. Avoid using this tool for complex tasks that require multiple steps."
    
    def count_dfs(input=None):
        """Anzahl an (Geo-)DataFrames in Python-Umgebung bestimmen"""
        dfs_num = 0
        for name, obj in python_repl_tool.python_repl.locals.items():   
            if isinstance(obj, pd.DataFrame): # GeoDataFrame ist eine Unterklasse von pd.DataFrame
                dfs_num+=1
        return dfs_num
    
    def get_infos(input=None):
        """Für jeden (Geo-)DataFrame der Python-Umgebung relevante Informationen bestimmen: 
        Referenzvariablenname, Spaltennamen, Datentypen, Aktive Geometriespalte, Zeilen- und Spaltenanzahl, erste drei Zeilen
        """
        infos = []
        for name, obj in python_repl_tool.python_repl.locals.items():
            if isinstance(obj, pd.DataFrame):                  
                df_name = f"**Name of the DataFrame: {name}**"      
                shape = f"- Number of rows: {obj.shape[0]}\n- Number of columns: {obj.shape[1]}\n"
                geometry_info = "No geometry column."
                spalten = "\n- Column data types:"
                spaltentypen = pd.DataFrame([obj.dtypes], index=["dtypes"])
                spaltentypen = tabulate(spaltentypen, headers="keys", tablefmt="github") 
                zeilen = "- First 3 row:"
                head = obj.head(3).copy()
                
                if isinstance(obj, gpd.GeoDataFrame):
                    df_name = f"**Name of the GeoDataFrame: {name}**"
                    try:
                        geometry_column = obj.geometry.name
                        geometry_info = f"Active geometry column: {obj.geometry.name}" 
                        head[geometry_column] = obj[geometry_column].apply(lambda x: x.geom_type) # WKT durch Geometrietyp ersetzen
                    except AttributeError as e:
                        geometry_column = f"No existing columns with geometry data type. You must add a geometry column as the active geometry column with df.set_geometry."
                    except Exception as e:
                        geometry_column = f"Error: {e}"  
                        
                head = tabulate(head, headers="keys", tablefmt="github") # Erste drei Zeilen als Markdown 
                #head = head.to_html()               
                info = "\n".join([df_name,shape, geometry_info, zeilen, head, spalten, spaltentypen])  
                infos.append(info)              
        return "\n\n".join([info for info in infos])
    
    python_env = python_repl_tool.python_repl.locals 
     
    # MapperTool für die Visualisierung von GeoDataFrames
    m = create_map() # folium.Map
    mapper_tool = MapperTool(metadata={"env":python_repl_tool.python_repl.locals, "m":m}) # Greift direkt auf Objektmapping zu

    # Analyst-Tool für das Planen, Generieren, Korrigieren und Ausführen von Python-Skripten.
    analyst_tool = AnalystTool(llm=llm, metadata={"env":python_env}) 

    # DataBaseTool für das Generieren, Korrigieren und Ausführen von SQL-Abfragen.
    db_tool = DBTool(llm=llm,metadata={"env":python_env}) 
    
    # Infos aller Werkzeuge zu LLM hinzufügen --> RunnableBinding
    tools = [python_repl_tool, mapper_tool,analyst_tool, db_tool] + list(tools)
    llm_with_tools = llm.bind_tools(tools, strict=True)
  
    # Haupt-Prompt erstellen --> ChatPromptTemplate
    prompt = getPrompt(main_prompt)  
    check_variables(prompt)
    
    # RunnableSequence für die Planung von Werkzeugausführungen
    agent = (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_tool_messages(x["intermediate_steps"]),
            gdfs_num=count_dfs,
            gdfs_infos=get_infos
        )
        | prompt
        | llm_with_tools
        | ToolsAgentOutputParser()
    )
    
    # Agent der mehrere Werkzeuge ausführen kann
    agent = RunnableMultiActionAgent(
        runnable=agent,
        input_keys_arg=["input"],
        return_keys_arg=["output"],
    )
    
    # Langzeitspeicher: Speichert bis zu 127000 Tokens, restliche Tokens werden durch ein LLM zusammengefasst. GPT-4o-2024-08-06 hat ein Kontextfenster von 128.000 Tokens
    memory = ConversationSummaryBufferMemory(llm=llm, max_token_size=127000, return_messages=True, memory_key="chat_history", input_key ="input")

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        return_intermediate_steps=return_intermediate_steps,
        max_iterations=max_iterations,
        max_execution_time=max_execution_time,
        memory = memory,
        early_stopping_method=early_stopping_method,
        handle_parsing_errors=handle_parsing_errors,
        **(agent_executor_kwargs or {}))
    
    return agent_executor
  