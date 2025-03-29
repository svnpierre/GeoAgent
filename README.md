# GeoAgent

GeoAgent is an LLM-powered agent that analyzes and visualizes user-provided WGS84 (EPSG:4326) GeoJSON files as well as OpenStreetMap data for Germany retrieved from a database.

# Features
- Automates and solves spatial tasks using GeoPandas and PostGIS.
- Provides interactive visualizations of GeoDataFrames.
- Geocodes addresses or places into points or polygons.
- Exports analysis results as an HTML map and messages as a TXT file.

# Tools
🐍 Python_REPL
- A simple Python shell to execute basic Python commands for quick queries and operations.

📊 AnalystTool
- Plans, writes, executes, and debugs Python scripts for analyzing (Geo-)DataFrames.

🗄️ DatabaseTool
- Writes, executes, and debugs SQL queries for analyzing OpenStreetMap or (Geo-)DataFrame data.
- Performs point or polygon geocoding.

🗺️ MapperTool
- Visualizes the geometry column or one numeric or categorical column along with geometries:

1️⃣ Geometrical Data
- Visualizations of (multi-) Points, Lines, or Polygons.
- Heatmaps for points.

2️⃣ Numeric Data
- Supported classification schemas: BoxPlot, EqualInterval, FisherJenks, FisherJenksSampled, HeadTailBreaks, JenksCaspall, JenksCaspallForced, JenksCaspallSampled, MaxP, MaximumBreaks, NaturalBreaks, Quantiles, Percentiles, StdMean.
- Choosable number of classes.
- Supports Matplotlib colormaps (e.g., 'Blues') with an optional min/max value.

3️⃣ Categorical Data
- Choosable categories (e.g., 'A', 'B', 'C') or dynamically generated categories based on unique column values.
- Supports matplotlib colormaps.

# Requirements
- Creation of a venv via the requirements.txt
- Adjustment of some libraries (see readme)
- An OpenAI API key
- A PostGIS database with the following criteria:  
1. Tables: `data.osm_points`, `data.osm_lines`, `data.osm_polygons`, `data.dfs`  
2. EDB Language Pack 3, `plpython3u` extension and language  
3. OSM data can be imported into the `public` schema using a PBF file and the `pg_osm_import.lua` script (see *Database-PostgreSQL*) with `osm2pgsql`  
4. Creation of the `geocode_function` (see *Database-PostgreSQL*)
- Credentials (database and OpenAI API key) stored in the .env file.

# How to use 
- Run the agent using the following command:
```
streamlit run geoagent_app.py
```

# LangSmith traces
- See *Tests*

# Architecture 
![alt text](https://github.com/svnpierre/GeoAgent/blob/main/Architektur.png) 
![alt text](https://github.com/svnpierre/GeoAgent/blob/main/Agent_Executor.png) 



