from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

def create_planner_chain(llm: BaseLanguageModel):
    """Erstellt eine RunnableSequence zum Planen eines Python-Skripts basierend auf einer Aufgabenstellung und Infos über (Geo-)DataFrames."""
    
    planner_prompt = ChatPromptTemplate.from_template("""You are an experienced planner for Python scripts specializing in spatial data analysis with GeoPandas. You must:  
    1. **Understand the Task**: Briefly analyze the task and highlight key objectives and requirements in 1-3 sentences.
    2. **Develop a Plan**: Create a detailed, step-by-step plan in natural language for solving the task based on the given GeoDataFrames. Include all necessary information (e.g., required columns, data types, data cleaning steps, spatial operations etc.) to complete the task. Avoid Python Code and unnecessary steps like visualizations.

    **(Geo-)DataFrames:** {gdf_infos}  
    - Begin planning for the following task: {task}
    - Return only your understanding and the finalized plan.""")

    planner_chain = planner_prompt | llm | StrOutputParser() # RunnableSequence

    return planner_chain 


