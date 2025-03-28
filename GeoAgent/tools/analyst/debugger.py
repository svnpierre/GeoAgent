from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

def create_debugger_chain(llm: BaseLanguageModel): 
    """Erstellt eine RunnableSequence zum Korrigieren eines Python-Skripts basierend auf einer Aufgabenstellung, einem Plan Infos über (Geo-)DataFrames, dem Code und der Fehlermeldung."""
    
    debugger_prompt = ChatPromptTemplate.from_template("""You are an experienced debugger for Python scripts in spatial data analysis. Debug the provided script based on the task, plan, available (Geo-)DataFrames, and error message.  
    **Task**: {task}  
    **Plan**: {plan}  
    **(Geo-)DataFrames**: {gdf_infos}  
    **Script**: {code}  
    **Error message**: {error}
    
    - Geometries of GeoDataFrames are in EPSG:25832.
    - Use print statements only for variables and (Geo-)DataFrames that contain final analysis results. Each of these print statements must include a description of the values and specify the variable in which they are stored.
    - Return only the debugged, executable Python code without any additional explanations or markdown formatting. 
    Now, start debugging!""")
    
    debugger_chain = debugger_prompt | llm | StrOutputParser() # RunnableSequence

    return debugger_chain      
