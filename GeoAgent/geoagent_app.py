# Streamlit-App zur Interaktion mit GeoAgent über den Browser 

import os
import time
from datetime import datetime

import geopandas as gpd
import folium as f
import streamlit as st
from streamlit.components.v1 import html
import streamlit.components.v1 as components

import langchain
from langchain.callbacks import StreamlitCallbackHandler
from langchain_core.tracers.context import tracing_v2_enabled
from langchain_openai import ChatOpenAI
from openai import AuthenticationError
from langsmith import Client

from dotenv import load_dotenv
from agent.base import create_geo_agent
from tools.mapper.tool import create_map, clear_map_html

load_dotenv(dotenv_path=".env")
langchain.debug = True

st.set_page_config(page_title="GeoAgent", page_icon="🗺️", layout="wide")

# CSS zum Festlegen der Sidebar-Breite
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        width: 300px !important;  /* Festgelegte Breite in Pixeln */
    }
</style>
""", unsafe_allow_html=True)

# CSS zum Verringern von Abständen
st.markdown("""
<style>
    .block-container {
        padding: 28px !important;
    }
</style>
""", unsafe_allow_html=True)


# Erlaubte Dateiformate
file_formats = {
    "geojson": gpd.read_file,
}

def clear_submit():
    """
    Clear the Submit Button State
    Returns:

    """
    st.session_state["submit"] = False

# Funktion zum Einlesen von GeoDataFrames
def load_data(uploaded_file):
    try:
        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    except:
        ext = uploaded_file.split(".")[-1]
    if ext in file_formats:
        gdf = gpd.read_file(uploaded_file)
        gdf = gdf.to_crs(epsg=25832)
        file_name = f"{uploaded_file.name}"
        # Dateiname zu gdf-Metadaten
        #gdf.attrs["file"] = file_name
        
        # Anzahl der bisheirgen GeoDataFrames im REPL bestimmen
        env = st.session_state["geoagent"].tools[0].python_repl.locals
        gdfs_num = 0
        for name, obj in env.items():
            if isinstance(obj, gpd.GeoDataFrame):
                gdfs_num += 1

        gdf_name = f"df_{gdfs_num}"
        # GeoDataFrame in REPL hinzufügen z.B. {"gdf2": gdf}
        env[gdf_name] = gdf
        print("geodatframe hinzugefügt", gdf_name)
        # Dict um Gdf-Name auf Dateiname zumappen. für integration in Prompt   
        return {gdf_name: file_name}

    else:
        with st.sidebar:
            st.error(f"Unsupported file format: {ext}")
        return None

# Nötige Session States 
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0
introduction = "I'm a geospatial analyst specialized in GeoPandas and SQL. I can analyze your WGS84 (EPSG:4326) GeoJSON files as well as OpenStreetMap data. How can I assist you?"
if "messages" not in st.session_state:
    # Liste zum Speichern der Konversation von User (Human) und Assistant (LLM)
    st.session_state["messages"] = [{"role": "assistant", "content": introduction}]

# Seitenleiste
#llm_api_key = st.sidebar.text_input("LLM-API Key", type="password", help="Currently OpenAI")
with st.sidebar:

    with st.expander("Info", expanded=False):
        st.markdown(
            """
            **GeoAgent** is an LLM powered agent that analyzes and visualizes user-provided WGS84 (EPSG:4326) GeoJSON files as well as OpenStreetMap data for Germany retrieved from a database. 

            ## Features
            - Automates and solves (easy to medium complexity) spatial tasks with GeoPandas and PostGIS. 
            - Visualizes GeoDataFrames interactively.  
            - Geocodes addresses or places into points or polygons.  
            - Exports analysis results as a HTML map and messages as a TXT file.  

            ## Tools
            ### 🐍 Python_REPL
            - A simple Python shell to execute basic Python commands for quick queries and operations.

            ---  

            ### 📊 AnalystTool
            - Plans, writes, executes, and debugs Python scripts for analyzing (Geo-)DataFrames.  
            
            ---

            ### 🗄️ DatabaseTool
            - Writes, executes, and debugs SQL queries for analyzing OpenStreetMap or GeoDataFrame data.  
            - Performs point or polygon geocoding.
            
            ---
            ### 🗺️ MapperTool
            - Visualizes the geometry column or one numeric or categorical column along with geometries:
            
             1️⃣ Geometrical data  
            - Visualizations of (multi-) Points, Lines, or Polygons.  
            - Heatmaps for points.  
            
             2️⃣ Numeric data  
            - Supported classification schemas: BoxPlot, EqualInterval, FisherJenks, FisherJenksSampled, HeadTailBreaks, JenksCaspall, JenksCaspallForced, JenksCaspallSampled, MaxP, MaximumBreaks, NaturalBreaks, Quantiles, Percentiles, StdMean.  
            - Use-case specific number of classes.  
            - Supports matplotlib colormaps (e.g., `'Blues'`) with an optional min/max value.  

             3️⃣ Categorical data  
            - Allows specifying categories (e.g., `'A'`, `'B'`, `'C'`).   
            - Supports matplotlib colormaps.  
            """,
            unsafe_allow_html=True
        )
    files = st.file_uploader(
        "Upload GeoJSON files in WGS84 (EPSG:4326)",
        type=list(file_formats.keys()),
        help="One or more EPSG:4326 (WGS84) GeoJSON files.",
        on_change=clear_submit,
        disabled="geoagent" not in st.session_state,
        accept_multiple_files = True,
        # von Streamlit:
        key=st.session_state["file_uploader_key"]
    )
    
# Jede neue Datei über load_data einlesen und zum gdf_file_mapping hinzufügen
if files:
    gdfs_added = []
    for num, file in enumerate(files): 
        try:
            mapping = load_data(file)
            gdfs_added.append(next(iter(mapping)))
        except Exception as e:
            st.error(f"Error loading file {file}: {e}")
    # Hochgeladene Dateien durch LLM zusammenfassen
    prompt = f"Create a short summary of the most important information about each GeoDataFrame in {gdfs_added}, including: Topic, Row and column count, details of columns (name, content, datatype)."
    
    gdfs_overviews = st.session_state["geoagent"].run(prompt)
    st.session_state.messages.append({"role": "assistant", "content": gdfs_overviews})
    
    # Key ändern um file_uploader zurückzusetzen
    st.session_state["file_uploader_key"] += 1
    st.rerun()
    
if st.sidebar.button("Export", disabled="geoagent" not in st.session_state, help="All chat messages as txt-file and the map as html-file."):
    # Export der folium.Map als HTML und des Nachrichtenverlaufs als TXT
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    output_path = "./Output"
    map_name = f"map_{timestamp}.html"
    # Bereinigtes HTML generieren
    cleaned_map_html = clear_map_html(st.session_state["geoagent"].tools[1].metadata["m"].get_root().render())
    # Bereinigtes HTML in eine Datei schreiben
    output_file = f"{output_path}/Maps/{map_name}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(cleaned_map_html)
    # Nachrichtenverlauf als txt
    chat_name = f"chat_{timestamp}.txt"
    with open(f"{output_path}/Chats/{chat_name}", "w", encoding="utf-8") as file:
        for entry in st.session_state["messages"]:
            file.write(f"{entry['role']}: {entry['content']}\n")
    st.info(f"Chat and map exported as {chat_name} and {map_name} in the output directory.")
    
if st.sidebar.button("Clear",disabled="geoagent" not in st.session_state, help="Clear the chat and map."):
    st.session_state["messages"] = [{"role": "assistant", "content": introduction}] # Nachrichtenfenster leeren
    st.session_state["geoagent"].memory.clear() # Langzeitpeicher leeren
    # Karte zurücksetzen (neues folium.Map-Objekt erzeugen)
    new_map = create_map()
    st.session_state["geoagent"].tools[1].metadata["m"] = new_map
    # Objektmapping leeren
    st.session_state["geoagent"].tools[0].python_repl.locals = {}
    st.info("Chat and map cleared.")

# Column-Layout: Chat (40%), Karte (60%)
col1, col2 = st.columns([0.4,0.6], gap="medium")

with col1:
    if "geoagent" not in st.session_state:
        try:
            llm_api_key = os.getenv("OPENAI_API_KEY")
            llm = ChatOpenAI(model="gpt-4o-2024-08-06", api_key=llm_api_key, streaming=True)
            llm.invoke("Write 'Hello'")
            with st.sidebar:
                st.info("LLM ready.")
            st.session_state["geoagent"] = create_geo_agent(llm, verbose=True)
            with st.sidebar:
                st.info("Geoagent ready.")
            st.rerun()
        except AuthenticationError:
            with st.sidebar:
                st.error("Invalid LLM-API key. Please check your key and try again.")
        except Exception as e:
            with st.sidebar:
                st.error(f"Error: {e}")
    with st.expander(label="Chat",expanded=True):  
        messages = st.container(height=466, border=False)
    for msg in st.session_state.messages: # Bisherigen Nachrichtenverlauf abrufen
        messages.chat_message(msg["role"]).write(msg["content"])
    # Nutzereingabe verarbeiten, Antwort generieren. Erst aktiv, wenn Geoagent bereit     
    if prompt := st.chat_input(placeholder="Ask geospatial questions.", disabled="geoagent" not in st.session_state):
        st.session_state["messages"].append({"role": "user", "content": prompt}) # Nutzereingabe zu Messages-ST hinzufügen und anzeigen
        messages.chat_message("user").write(prompt)
        st_cb = StreamlitCallbackHandler(st.container(height=585, border=False), expand_new_thoughts=True,max_thought_containers=100) 
        response = st.session_state.geoagent.run(prompt, callbacks=[st_cb]) # Nutzereingabe an LLM senden und Antwort abrufen
        messages.chat_message("assistant").write(response)  # Ausgabe der Antwort innerhalb des Chat-Layouts
        st.session_state.messages.append({"role": "assistant", "content": response})  # Antwort zu messages hinzufügen

# Karte und GeoDataFrame-Viewer          
    with col2:
        if "geoagent" in st.session_state:
            with st.expander(label="Map", expanded=True):
                cleaned_map_html = clear_map_html(st.session_state["geoagent"].tools[1].metadata["m"].get_root().render())
                # Containergröße anpassen
                dynamic_html = f"""
                <div id="map-container" style="width: 100%; height: 100%;">
                    {cleaned_map_html}
                </div>
                """
                components.html(dynamic_html, height=515)  
            with st.expander("GeoDataFrames"):
                with st.container(height=522, border=False):
                    gdf = st.selectbox("GeoDataFrame", tuple([name for name, obj in st.session_state["geoagent"].tools[0].python_repl.locals.items() if isinstance(obj, gpd.GeoDataFrame)]))
                    if gdf:
                        st.dataframe(st.session_state["geoagent"].tools[0].python_repl.locals[gdf],use_container_width=True)
        else:
            st.info("GeoAgent not ready.")
        

