local srid = 25832 -- WGS84 standardmäßig
local tables = {} -- Dict aller anzulegenden Tabellen

-- Primary Keys werden zu separaten Spalten
local primary_keys = {
    "name", "aerialway", "aeroway", "amenity", "barrier", "building", 
    "craft", "emergency", "geological", "healthcare", "highway", 
    "historic", "landuse", "leisure", "man_made", "military", 
    "natural", "office", "place", "power", "public_transport", 
    "railway", "route", "shop", "sport", "telecom", "tourism", 
    "water", "waterway"
} 

-- Zu löschende Keys
local delete_keys = {
    -- Metadaten und importbezogene Keys
    '^attribution$', '^comment$', '^created_by$', '^fixme$', '^note(:.*)?$', 
    '^odbl(:.+)?$', '^source(:.*)?$', '^source_ref$',
    
    -- Importquellen
    '^(CLC|geobase|canvec|osak|kms|ngbe|it:fvg|KSJ2|yh|LINZ2?:?OSM|ref:linz|WroclawGIS|naptan|tiger|gnis|NHD|mvdgis):.*$',
    
    -- Spezifische Projekt- und regionale schlüssel
    '^(project:eurosha_2012|ref:UrbIS|accuracy:meters|sub_sea:type|waterway:type|statscan:rbuid|ref:ruian(:.*)?|building:ruian:type|dibavod:id|uir_adr:ADRESA_KOD|gst:feat_id|maaamet:ETAK|ref:FR:FANTOIR|3dshapes:ggmodelk|AND_nosr_r|OPPDATERIN|addr:city:simc|addr:street:sym_ul|building:usage:pl|building:use:pl|teryt:simc|raba:id|dcgis:gis_id|nycdoitt:bin|chicago:building_id|lojic:bgnum|massgis:way_id|lacounty:.*|at_bev:addr_date|import|import_uuid|OBJTYPE|SK53_bulk:load|mml:class)$'
}


-- Prüfen ob tag mit delete key
local function is_delete_key(key)
    for _, pattern in ipairs(delete_keys) do
        if key:match(pattern) then
            return true
        end
    end
    return false
end

-- Prüfen ob tag mit primary key
local function is_primary_key(key)
    for _, primary_key in ipairs(primary_keys) do
        if key == primary_key then
            return true
        end
    end
    return false
end

-- Delete tags entfernen, primary und other_tags behalten
local function process_tags(tags)
    local primary_tags = {}
    local other_tags = {}

    for k, v in pairs(tags) do
        if not is_delete_key(k) then
            if is_primary_key(k) then
                primary_tags[k] = v
            else
                other_tags[k] = v
            end
        end
    end

    return primary_tags, other_tags
end

-- Alle Tabellen haben gleichen Aufbau
local function create_table(name)
    tables[name] = osm2pgsql.define_table({
        name = name,
        ids = { type = 'any', type_column = 'osm_type', id_column = 'osm_id' },
        columns = {
            { column = 'name', type = 'text' },
            { column = 'aerialway', type = 'text' },
            { column = 'aeroway', type = 'text' },
            { column = 'amenity', type = 'text' },
            { column = 'barrier', type = 'text' },
            { column = 'building', type = 'text' },
            { column = 'craft', type = 'text' },
            { column = 'emergency', type = 'text' },
            { column = 'geological', type = 'text' },
            { column = 'healthcare', type = 'text' },
            { column = 'highway', type = 'text' },
            { column = 'historic', type = 'text' },
            { column = 'landuse', type = 'text' },
            { column = 'leisure', type = 'text' },
            { column = 'man_made', type = 'text' },
            { column = 'military', type = 'text' },
            { column = 'natural', type = 'text' },
            { column = 'office', type = 'text' },
            { column = 'place', type = 'text' },
            { column = 'power', type = 'text' },
            { column = 'public_transport', type = 'text' },
            { column = 'railway', type = 'text' },
            { column = 'route', type = 'text' },
            { column = 'shop', type = 'text' },
            { column = 'sport', type = 'text' },
            { column = 'telecom', type = 'text' },
            { column = 'tourism', type = 'text' },
            { column = 'water', type = 'text' },
            { column = 'waterway', type = 'text' },
            { column = 'other_tags', type = 'jsonb' },
            { column = 'geom', type = 'geometry', projection = srid, not_null = true }
        }
    })
end

-- Prüfen ob der Key "area" den Wert "yes" hat bzw. typische Keys flächenhafter Objekte (z.B. Building) einen Wert haben
local function has_area_tags(tags)
    -- Direct area tag check
    if tags.area == 'yes' then return true end
    if tags.area == 'no' then return false end

    -- Keys typischerweise flächenhafter Objekte
    local area_indicative_keys = {
        "aeroway", "amenity", "building", "harbour", "historic", 
        "landuse", "leisure", "man_made", "military", "natural", 
        "office", "place", "power", "public_transport", "shop", 
        "sport", "tourism", "water", "waterway", "wetland",
        "abandoned:aeroway", "abandoned:amenity", "abandoned:building", 
        "abandoned:landuse", "abandoned:power", 
        "area:highway", "building:part"
    }

    for _, key in ipairs(area_indicative_keys) do
        if tags[key] then return true end
    end

    return false
end

-- Tabellen für verschiedene Geometrietypen erstellen
create_table('points') -- Punkte
create_table('lines') -- (Multi-)Linien 
create_table('polygons') -- (Multi-)Polygone

-- Ein Node wird zu einem Punkt
function osm2pgsql.process_node(object)
    local primary_tags, other_tags = process_tags(object.tags)
    
    if next(primary_tags) or next(other_tags) then
        local insert_tags = next(primary_tags) and primary_tags or {}
        insert_tags["other_tags"] = next(other_tags) and other_tags or nil
        insert_tags["geom"] = object:as_point() 
        tables.points:insert(insert_tags)
    end
end

-- Ein Way wird zu einer Linie oder zu einem Polygon
function osm2pgsql.process_way(object)
    local primary_tags, other_tags = process_tags(object.tags)
    
    if next(primary_tags) or next(other_tags) then
        local insert_tags = next(primary_tags) and primary_tags or {}
        insert_tags["other_tags"] = next(other_tags) and other_tags or nil

        if object.is_closed and has_area_tags(object.tags) then
            insert_tags["geom"] = object:as_polygon() 
            tables.polygons:insert(insert_tags)
        else 
            insert_tags["geom"] = object:as_linestring() 
            tables.lines:insert(insert_tags)
        end
    end
end

-- Eine Relation wird zu einem MultiLineString/-Polygon
function osm2pgsql.process_relation(object)
    local primary_tags, other_tags = process_tags(object.tags)
    
    if next(primary_tags) or next(other_tags) then
        local insert_tags = next(primary_tags) and primary_tags or {}
        insert_tags["other_tags"] = next(other_tags) and other_tags or nil

        local relation_type = object.tags.type

        if relation_type == 'route' then
            insert_tags["geom"] = object:as_multilinestring()
            tables.lines:insert(insert_tags)
            return
        end

        if relation_type == 'boundary' or (relation_type == 'multipolygon' and object.tags.boundary) then
            insert_tags["geom"] = object:as_multipolygon()
            tables.polygons:insert(insert_tags)
            return
        end

        if relation_type == 'multipolygon' then
            insert_tags["geom"] = object:as_multipolygon() 
            tables.polygons:insert(insert_tags)
        end
    end
end