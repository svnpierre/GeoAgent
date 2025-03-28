CREATE TABLE "ki_home"."gdf"
(
    "name" VARCHAR NOT NULL,
    "attributes" JSON NOT NULL,
    "geometry" GEOMETRY NOT NULL
)
TIER STRATEGY (
    ( ( VRAM 1, RAM 5, DISK0 5, PERSIST 5 ) )
)
GEOSPATIAL INDEX ("geometry");