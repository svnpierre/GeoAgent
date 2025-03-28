## **Requirements**  
- Creation of venv via the requirements.txt
- Adjustmenets of some libaries (see under adjustments)
- An OpenAI API key  
- A PostGIS database with the following tables:
  - `data.osm_points`  
  - `data.osm_lines`  
  - `data.osm_polygons`  
  - `data.dfs`  
- OSM data can be imported into the public schema using a PBF file and the `pg_osm_import.lua` script.  
- Credentials (database and OpenAI API key) must be stored in the .env file.

## **How to Use**  
To start the agent, run the following command:  
- streamlit run geoagent_app.py

## **Adjustments**  
- Recommended code changes:

1. geopandas.explore.py:
--> Adaptation of the def _categorical_legend() to support scrollbars, custom sizes and folding function for legends

def _categorical_legend(m, title, categories, colors):
    """
    Add a collapsible categorical legend to a map as a Leaflet control that remains visible in fullscreen
    and is draggable.

    Parameters
    ----------
    m : folium.Map
        Existing map instance on which to draw the plot
    title : str
        title of the legend (e.g. column name)
    categories : list-like
        list of categories
    colors : list-like
        list of colors (in the same order as categories)
    """

    import branca as bc

    # JavaScript und CSS für die Leaflet-Kontrolle, Draggable- und Collapsible-Funktionalität
    head = """
    {% macro header(this, kwargs) %}
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
    <style type='text/css'>
      .legend {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        padding: 10px;
        font: 12px/14px Arial, Helvetica, sans-serif;
        max-height: 300px;
        max-width: 200px;
        overflow: auto;
        cursor: move;
      }
      .legend h4 {
        margin: 0;
        padding: 0;
        cursor: pointer;
        user-select: none; /* Verhindert Textselektion */
      }
      .legend ul {
        list-style: none;
        padding: 0;
        margin: 5px 0 0 0; /* Abstand zur Überschrift */
      }
      .legend li {
        margin-bottom: 2px;
        white-space: nowrap;
      }
      .legend span {
        display: inline-block;
        width: 14px;
        height: 14px;
        margin-right: 5px;
        vertical-align: middle;
      }
      .legend-collapsed ul {
        display: none; /* Liste ausblenden, wenn eingeklappt */
      }
    </style>
    {% endmacro %}
    """

    # Add CSS und jQuery UI (im Header)
    macro = bc.element.MacroElement()
    macro._template = bc.element.Template(head)
    m.get_root().add_child(macro)

    # JavaScript für die Leaflet-Kontrolle mit korrekter Karten-ID
    map_id = f"map_{m._id}"
    legend_script = f"""
    <script>
    $(document).ready(function() {{
        // Funktion zum Hinzufügen der Legende
        function addLegend() {{
            var legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function (map) {{
                var div = L.DomUtil.create('div', 'info legend');
                div.innerHTML =
                    '<h4>{title}</h4>' +
                    '<ul>' +
                    {''.join([f"'<li><span style=\\\"background:{color}\\\"></span>{label}</li>' + " for label, color in zip(categories, colors)])}
                    '</ul>';
                L.DomEvent.disableClickPropagation(div);
                L.DomEvent.disableScrollPropagation(div);

                // Einklappfunktion hinzufügen
                var titleElement = div.querySelector('h4');
                var listElement = div.querySelector('ul');
                titleElement.addEventListener('click', function() {{
                    div.classList.toggle('legend-collapsed');
                    if (div.classList.contains('legend-collapsed')) {{
                        listElement.style.display = 'none';
                    }} else {{
                        listElement.style.display = 'block';
                    }}
                }});

                return div;
            }};
            legend.addTo({map_id});
            
            // Draggable-Funktionalität hinzufügen
            $('.legend').draggable({{
                containment: '#{map_id}',
                start: function(event, ui) {{
                    $(this).css({{
                        right: 'auto',
                        bottom: 'auto',
                        position: 'absolute'
                    }});
                }}
            }});
        }}

        // Sicherstellen, dass die Karte geladen ist
        if (typeof {map_id} !== 'undefined') {{
            addLegend();
        }} else {{
            setTimeout(addLegend, 500);
        }}
    }});
    </script>
    """

    # Add JavaScript zur Karte
    script_element = bc.element.Element(legend_script)
    m.get_root().html.add_child(script_element)








