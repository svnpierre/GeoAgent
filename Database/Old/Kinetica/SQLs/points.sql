CREATE TABLE "ki_home"."points"
(
    "osm_id" BIGINT NOT NULL,
    "osm_type" VARCHAR NOT NULL,
    "aerialway" VARCHAR (256, dict),
    "aeroway" VARCHAR (256, dict),
    "amenity" VARCHAR (256, dict),
    "barrier" VARCHAR (256, dict),
    "building" VARCHAR (256, dict),
    "craft" VARCHAR (256, dict),
    "emergency" VARCHAR (256, dict),
    "geological" VARCHAR (256, dict),
    "healthcare" VARCHAR (256, dict),
    "highway" VARCHAR (256, dict),
    "historic" VARCHAR (256, dict),
    "landuse" VARCHAR (256, dict),
    "leisure" VARCHAR (256, dict),
    "man_made" VARCHAR (256, dict),
    "military" VARCHAR (256, dict),
    "name" VARCHAR (256, dict),
    "natural_key" VARCHAR (256, dict),
    "office" VARCHAR (256, dict),
    "place" VARCHAR (256, dict),
    "power_key" VARCHAR (256, dict),
    "public_transport" VARCHAR (256, dict),
    "railway" VARCHAR (256, dict),
    "route" VARCHAR (256, dict),
    "shop" VARCHAR (256, dict),
    "sport" VARCHAR (256, dict),
    "telecom" VARCHAR (256, dict),
    "tourism" VARCHAR (256, dict),
    "water" VARCHAR (256, dict),
    "waterway" VARCHAR (256, dict),
    "other_tags" JSON,
    "geometry" GEOMETRY NOT NULL
)
TIER STRATEGY (
    ( ( VRAM 1, RAM 5, DISK0 5, PERSIST 5 ) )
)
LOW CARDINALITY INDEX ("name")
LOW CARDINALITY INDEX ("aerialway")
LOW CARDINALITY INDEX ("aeroway")
LOW CARDINALITY INDEX ("amenity")
LOW CARDINALITY INDEX ("barrier")
LOW CARDINALITY INDEX ("building")
LOW CARDINALITY INDEX ("craft")
LOW CARDINALITY INDEX ("emergency")
LOW CARDINALITY INDEX ("geological")
LOW CARDINALITY INDEX ("healthcare")
LOW CARDINALITY INDEX ("highway")
LOW CARDINALITY INDEX ("historic")
LOW CARDINALITY INDEX ("landuse")
LOW CARDINALITY INDEX ("leisure")
LOW CARDINALITY INDEX ("man_made")
LOW CARDINALITY INDEX ("military")
LOW CARDINALITY INDEX ("natural_key")
LOW CARDINALITY INDEX ("office")
LOW CARDINALITY INDEX ("place")
LOW CARDINALITY INDEX ("power_key")
LOW CARDINALITY INDEX ("public_transport")
LOW CARDINALITY INDEX ("railway")
LOW CARDINALITY INDEX ("route")
LOW CARDINALITY INDEX ("shop")
LOW CARDINALITY INDEX ("sport")
LOW CARDINALITY INDEX ("telecom")
LOW CARDINALITY INDEX ("tourism")
LOW CARDINALITY INDEX ("water")
LOW CARDINALITY INDEX ("waterway")
GEOSPATIAL INDEX ("geometry");