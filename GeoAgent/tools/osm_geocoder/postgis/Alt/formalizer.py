from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel

def create_formalizer_chain(llm: BaseLanguageModel): # Erstellt eine RunnableSequence, die mit .invoke({"query":str) aufgerufen werden kann und einen Plan zum Schreiben eines Scripts auf Basis einer Aufgabenbeschriebung und Infos über GeoDataFrames zurückliefert
    formalizer_prompt = ChatPromptTemplate.from_template("""Your task is to enrich the provided query with informationen to relevant OSM tags/keys, geometry types and geocoding to make the creation of an SQL to retrieve OSM data and/or to geocode places/addresses easier for an LLM. 
    
    For the enrichmenet you need specify important parts of the query in brackets:
    1) For OSM-related parts:
    - Use either the "Tags:"-Annoation to specify one or more relevant OSM tags (e.g. Tags: amenity=school) or the "Keys:"-Annotation to specify one or more relevant OSM keys (e.g. Keys: building). 
    - For general administrative units (e.g. federal states) use the "administrative=boundary"-Tag and specify the level for the "admin_level=level-tag: 4 -> Bundesland (Federal State), 5 -> Regierungsbezirk (Governmental District), 6 -> Stadt-/Landkreis (Urban/Rural District), 7 -> Gemeindeverband (Collective Municipalities), 8 -> Stadtbezirk (City District), 10 -> Stadtteil (Suburb), 11 -> Stadtviertel (Neighborhood) 
    - Use the "Types:"-Annotation to specify one or more geometry types (point, line and/or polygon).

    2) For geocoding-related parts (named places or addresses e.g. 'Berlin'):
    - Use the "Geocoding:"-Annotation to specify the geometry type (point or polygon) to be used for the geocoding (e.g. Geocoding: point)

    3) For the output part:
    - Use the "Keys:"-Annotation to specify the relevant keys to be output (e.g. Keys: name, capacity)
    
    Enrich the following query and only output the enriched query:
    Query: {query}""")

    formalizer_chain = formalizer_prompt | llm | StrOutputParser() # RunnableSequence

    return formalizer_chain 


