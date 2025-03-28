# Ermöglicht die Visualisierung von GeoDataFrames (numerisch, kategorisch, geometrisch, Heatmap) 

import re
import geopandas as gpd
import folium as f
from langchain_core.tools import BaseTool
from typing import Any, Dict, Optional, Sequence, cast, Union,Type, List, Union
from folium.plugins import HeatMap
from folium.plugins import Draw, Geocoder, MousePosition, Fullscreen, LocateControl, MeasureControl, SideBySideLayers, Fullscreen
from enum import Enum
from pydantic import BaseModel, Field
from pyproj import Transformer

def add_layer_control(map):
    f.LayerControl().add_to(map)
    
def fit_map(gdf, map):
    """Zoomt die Karte anhand der Bbox des letzten visualisierten GeoDataFrames."""
    # Extrahiere die Bounding Box des GeoDataFrames in EPSG:25832
    minx, miny, maxx, maxy = gdf.total_bounds

    # Erstelle einen Transformer von EPSG:25832 nach EPSG:4326
    transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

    # Konvertiere die Bounding Box-Koordinaten in WGS84
    minx_wgs84, miny_wgs84 = transformer.transform(minx, miny)
    maxx_wgs84, maxy_wgs84 = transformer.transform(maxx, maxy)

    # Fügt die Bounding Box z folium.Map hinzu
    map.fit_bounds([[miny_wgs84, minx_wgs84], [maxy_wgs84, maxx_wgs84]])
    
def clear_map_html(html_content):
    """Entfernt unnötiges LayerControl-HTML"""
    # Pattern to match layer control variable declarations
    layer_control_var_pattern = r'var layer_control_[a-f0-9]+_layers = \{[^}]+\};'
    # Pattern to match layer control creation and addition to map
    layer_control_creation_pattern = r'let layer_control_[a-f0-9]+ = L\.control\.layers\([^)]+\)\.addTo\(map_[a-f0-9]+\);'
    # Find all layer control instances
    var_matches = re.finditer(layer_control_var_pattern, html_content)
    creation_matches = re.finditer(layer_control_creation_pattern, html_content)
    # Convert to lists to get all matches
    var_matches = list(var_matches)
    creation_matches = list(creation_matches)
    # If there are multiple layer controls, remove all but the last one
    if len(var_matches) > 1:
        # Remove all variable declarations except the last one
        for match in var_matches[:-1]:
            html_content = html_content.replace(match.group(0), '')
    if len(creation_matches) > 1:
        # Remove all control creations except the last one
        for match in creation_matches[:-1]:
            html_content = html_content.replace(match.group(0), '')
    return html_content
def create_map():
    """Erstellt die Standard-Folium-Map"""
    m = f.Map(tiles = None, location=[51.44, 9.83],zoom_start=6)
    Geocoder().add_to(m) # Geocder (forward, reverse) hinzufügen
    # Leere FeatureGroup erstellen und zur Karte hinzufügen
    draw_feature_group = f.FeatureGroup(name="Geometries")
    draw_feature_group.add_to(m)
    Draw(feature_group=draw_feature_group).add_to(m) # Draw Plugin mit der FeatureGroup verknüpfen
    MousePosition().add_to(m) # Koordinaten anzeigen

    Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    LocateControl().add_to(m)

   # Map().add_to(m)

    MeasureControl().add_to(m)

    layer_right = f.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
        name='OpenTopoMap',
        control=False
    )
    layer_left = f.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Imagery @2024 TerraMetrics, Map data @2024 GeoBasis-DE/BKG (@2009), Google',
        name='Google Satellite Hybrid',
        control=False
    )

    sbs = f.plugins.SideBySideLayers(
        layer_left, 
        layer_right,
    )

    layer_left.add_to(m)
    layer_right.add_to(m)
    sbs.add_to(m)
    
    f.LayerControl().add_to(m)
    # Custom CSS um max. Popupgröße festzulegen und Scrollbalken hinzuzufügen
    style = """
    <style>
    .leaflet-popup-content-wrapper {
        overflow: auto !important;
        max-width: 200px !important;
        max-height: 175px !important;
    }
    </style>
    """
    m.get_root().html.add_child(f.Element(style))
        
    return m

# Alle erlaubten Klassifikzierungsschemas für numerische Klassifikation: enum 
class Scheme(Enum):
    BoxPlot = "BoxPlot"
    EqualInterval = "EqualInterval"
    FisherJenks = "FisherJenks"
    FisherJenksSampled = "FisherJenksSampled"
    HeadTailBreaks = "HeadTailBreaks"
    JenksCaspall = "JenksCaspall"
    JenksCaspallForced = "JenksCaspallForced"
    JenksCaspallSampled = "JenksCaspallSampled"
    MaxP = "MaxP"
    MaximumBreaks = "MaximumBreaks"
    NaturalBreaks = "NaturalBreaks"
    Quantiles = "Quantiles"
    Percentiles = "Percentiles"
    StdMean = "StdMean"

# Parameter für numerische Klassifikation: dict
class Numeric(BaseModel):
    gdf_column: str = Field(description="The name of the GeoDataFrame column to visualize e.g., 'Pop2012'.")
    k: Union[int, None] = Field(description="The number of classes to classify the numeric data. If None, a default value is used.")
    scheme: Scheme #= Field(description="The schema used for the classification.")
    cmap: str = Field(description="The name of a suitable colormap recognized by matplotlib e.g., 'blues'.")
    vmin: Union[float, None] = Field(description="The minimum value of the colormap. If None, the minimum value in the column is used.")
    vmax: Union[float, None] = Field(description="The maximum value of the colormap. If None, the maximum value in the column is used.") #If None, the maximum data value in the column is used.
    legend_caption: str = Field(description="A short caption for the legend of the visualization e.g, 'Absolute population in Chicago (2012)'.")

# Parameter für kategorische Klassifikation: dict
class Categorical(BaseModel):
    gdf_column: str = Field(description="The name of the GeoDataFrame column to visualize e.g., 'areas2005'")
    categories: Union[List[str], None] = Field(description="An ordered list of categories to be used for categorical plotting. e.g., ['A', 'B', 'C']. If None, the unique values in the column are used as categories.")
    cmap: str = Field(description="The name of a colormap recognized by matplotlib e.g., 'blues'.")
    legend_caption: str = Field(description="A short caption for the legend of the visualization e.g, 'Community areas in Chicago (2006)'.")
    
# Vom LLM generierte Parameter: str, str, dict/None, dict/None, bool/None. Standardwerte innerhalb der Dicts werden durch None simuliert (z.B. vmin: None)
class MapperInput(BaseModel):
    class Config:
        extra = 'allow'  # Um bei Tool-Erstellung eine Folium.map (m) und Dict mit GeoDataFrames (env) übergeben zu können. 

    gdf_name: str = Field(description="The name of the GeoDataFrame to visualize, e.g., 'gdf_3'.")
    layer_name: str = Field(description="The name of the layer to add to the map, e.g., 'Abs_Population_Chicago_2012'.")
    numeric: Union[Numeric, None] = Field(description="Use this to visualize numeric data. If None, no numeric visualization is used.") #if the column contains numeric data
    categorical: Union[Categorical, None] = Field(description="Use this to visualize categorical data. If None, no categorical visualization is used.")
    heatmap: bool = Field(description="Use this to visualize a point GeoDataFrame as heatmap.")
    geometries: bool = Field(description="Use this to visualize only the geometries of a GeoDataFrame, without any numeric or categorical classifications or heatmaps. ")
    #Union[bool, None] = Field(description="If True, a heatmap is used to visualize a point GeoDataFrame. If None, no HeatMap is used and the GeoDataFrame must be visualized numeric or categorical.")

# Tool welches GeoDataframes mit gpd.explore() visualisieren kann. 
class MapperTool(BaseTool):
    name = "MapperTool"
    description = """Use this tool to visualize a GeoDataFrame. You can create visualizations based on a numeric or categorical column of a point, line, or polygon GeoDataFrame, generate a heatmap for a point GeoDataFrame, or simply visualize the geometries of the GeoDataFrame. Choose the most suitable visualization type for the analysis task and the data. If you need to visualize multiple GeoDataFrames, call the tool separately for each one with an appropriate visualization type, ensuring this order: start with polygon GeoDataFrames, then linestring GeoDataFrames, and finally point GeoDataFrames.
    """
    args_schema: Type[BaseModel] = MapperInput

    def _run(self, gdf_name, layer_name, numeric, categorical, heatmap, geometries):
        # Drei Visualisierungsarten: numeric, categorical, geometric, heatmap 

        # gdf_name und layer_name müssen vorhanden sein, sowie mindestens eine Visualisierungsart
        if (gdf_name and layer_name) and (numeric or categorical or heatmap or geometries):
            # GDF abrufen
            print("env:", self.metadata["env"])
            if gdf_name not in self.metadata["env"]:
                return f"{gdf_name} is not a valid GeoDataFrame name. Please provide the name of a valid GeoDataFrame."
            
            gdf = self.metadata["env"][gdf_name]
            if not isinstance(gdf, gpd.GeoDataFrame):
                return f"{gdf_name} is of type {type(gdf)} which is not supported. Please provide the name of a valid GeoDataFrame."
            # Layercontrol entfernen um neuen layer hinzufügen zu können
            for item in list(self.metadata['m']._children):
                if item.startswith('layer_control'):
                    print(f"removing {item}")
                    del self.metadata['m']._children[item]      
        else:
            return "Failed to visualize the GeoDataFrame. Make sure to input the name of the GeoDataFrame to visualize, a layer name and exactly one visualization option (numeric, categorical, heatmap or geometries)."

        # Scrollbar nutzen, falls Sachdaten die Größe eines Popup-Fenster überschreiten
        popup_kwds=dict(
                minWidth=500,
                maxWidth=700,
                maxHeight=400,
                style= 'background-opacity: 0.8;'
            )  

        if numeric: # Spalte mit numerischen Daten klassifizieren und visualiseren
            try:
                # Parameter für Klassifizieurng bestimmen, ggf. standardwerte nutzen
                column = numeric.gdf_column
                k = numeric.k
                scheme = numeric.scheme.name
                cmap = numeric.cmap
                vmin = numeric.vmin
                vmax = numeric.vmax
                caption = numeric.legend_caption
                
                gdf.explore(popup=True, tooltip=column, column=column, k=k, scheme=scheme, cmap=cmap, vmin=vmin, vmax=vmax, name=layer_name,legend=True, m=self.metadata['m'],legend_kwds={"caption":caption, "colorbar": False},style_kwds = {"fillOpacity":"0.85","weight":"1.5"})   
                add_layer_control(self.metadata['m'])    
                fit_map(gdf, self.metadata['m'])      
                
                self.metadata["m"].save("geoagent_Map.html")
                return f"Sucessfully visualized the numeric column {column} of the GeoDataFrame {gdf_name}."
            except Exception as e:
                add_layer_control(self.metadata['m']) 
                
                return f"Could not visualize the numeric column {column} of the GeoDataFrame {gdf_name}. Visualize parameters: {numeric}. Error:{str(e)}"
        elif categorical: # Spalte mit kategorigschen Daten klassifizieren und visualiseren
            try:
                # Parameter für Klassifizieurng bestimmen, ggf. Standardwerte nutzen
                gdf_column = categorical.gdf_column
                categories = categorical.categories
                cmap = categorical.cmap
                caption = categorical.legend_caption
                gdf.explore(popup=True, tooltip=gdf_column, column=gdf_column, categories=categories, cmap=cmap, name=layer_name, legend_kwds={"caption":caption, "colorbar": False},categorical= True, m=self.metadata['m'],style_kwds = {"fillOpacity":"0.85","weight":"1.5"})
                add_layer_control(self.metadata['m']) 
                fit_map(gdf, self.metadata['m'])  
                self.metadata["m"].save("geoagent_Map.html")
                return f"Sucessfully visualized the categorical column {gdf_column} of the GeoDataFrame {gdf_name}."
            except Exception as e:
                add_layer_control(self.metadata['m']) 
                
                return f"Could not visualize the categorical column {gdf_column} of the GeoDataFrame {gdf_name}. Visualize parameters: {categorical}. Error:{str(e)}"
        elif heatmap: # Point GeoDataFrame visualiseren
            try:
                # Nur Punkte behalten 
                point_gdf = gdf[gdf.geometry.type == 'Point']
                # Zu WGS84 konvertieren und Liste von Koordinaten erzuegen
                heat_data = [[point.xy[1][0], point.xy[0][0]] for point in point_gdf.geometry.to_crs(epsg=4326)]
                
                HeatMap(heat_data).add_to(f.FeatureGroup(name=f"{layer_name}").add_to(self.metadata['m']))
                add_layer_control(self.metadata['m']) 
                fit_map(gdf, self.metadata['m'])  
                self.metadata["m"].save("geoagent_Map.html")
                
                return f"Sucessfully visualized the GeoDataFrame {gdf_name} as a heatmap."
            except Exception as e:
                
                add_layer_control(self.metadata['m']) 
                return f"Tried to filter points, convert the GeoDataFrame to WGS84, extract the coordinates and visualize as heatmap. Error:{str(e)}"
        elif geometries:
            try:
                gdf.explore(popup=True, tooltip=False, name=layer_name, m=self.metadata['m'],style_kwds = {"fillOpacity":"0.85","weight":"1.5"})
                add_layer_control(self.metadata['m']) 
                fit_map(gdf, self.metadata['m'])  
                
                return f"Sucessfully visualized the geometries of the GeoDataFrame {gdf_name}."
            except Exception as e:
                add_layer_control(self.metadata['m']) 
                
                return f"Could not visualize the geometries of the GeoDataFrame {gdf_name}. Error:{str(e)}"
        
