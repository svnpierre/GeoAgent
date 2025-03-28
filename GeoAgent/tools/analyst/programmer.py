from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

def create_programmer_chain(llm:BaseLanguageModel): 
    """Erstellt eine RunnableSequence zum Generieren eines Python-Skripts basierend auf einer Aufgabenstellung, einem Plan und Infos über GeoDataFrames."""
    
    programmer_prompt = ChatPromptTemplate.from_template("""You are an experienced Python programmer for spatial data analysis using GeoPandas. Write a Python script to solve the given task based on the provided plan and the available (Geo-)DataFrames.  
    **Task**: {task}  
    **Plan**: {plan}  
    **Available (Geo-)DataFrames**: {gdf_infos}  
    - GeoDataFrames are in EPSG:25832.
    - Consider every step of the plan in your code.
    - Use print statements only for variables and GeoDataFrames that contain final analysis results. Each of these print statements must include a description of the values and specify the variable in which they are stored.
    - Return only the Python script that can be executed directly without any additional explanations or markdown formatting.
    
    Now, start programming!""")
    
    debugger_chain = programmer_prompt | llm | StrOutputParser() # RunnableSequence

    return debugger_chain 


