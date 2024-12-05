import ee
import geopandas as gpd
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Initialize Earth Engine
ee.Authenticate()

ee.Initialize(project='cap2025-airborneinsight')

# User input for ROI and survey name
lat_range = input("Enter the latitude range (min,max) (e.g., 40,42): ").split(',')
lon_range = input("Enter the longitude range (min,max) (e.g., -114,-112): ").split(',')
survey_name = input("Enter the name of the survey: ")

# Convert inputs to floats
lat_min, lat_max = map(float, lat_range)
lon_min, lon_max = map(float, lon_range)

# Define ROI as a rectangle with lat/long coordinates
coordinates = [[lon_min, lat_min], [lon_max, lat_min], [lon_max, lat_max], [lon_min, lat_max]]

# Create a Shapely Polygon object for the ROI
roi = Polygon(coordinates)

# Create a GeoDataFrame with the polygon geometry
gdf = gpd.GeoDataFrame(geometry=[roi], crs="EPSG:4326")

# Set the plot flag to True to display the plots
plot = True

# Tile size (adjust as needed)
tile_size = 0.1  # Degree of latitude/longitude (e.g., 0.1 degrees per tile)

# Create a list of tiles to split the ROI into smaller regions
tiles = []
lat_tiles = np.arange(lat_min, lat_max, tile_size)
lon_tiles = np.arange(lon_min, lon_max, tile_size)

for lat_start in lat_tiles:
    for lon_start in lon_tiles:
        lat_end = lat_start + tile_size
        lon_end = lon_start + tile_size
        tiles.append([lon_start, lat_start, lon_end, lat_end])

# Function to fetch and process data for a tile
def fetch_tile_data(lon_min, lat_min, lon_max, lat_max):
    try:
        # Convert to Earth Engine Geometry for the tile
        tile_geometry = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

        # Access Landsat 8 data, filter for cloud cover and date range to reduce size
        landsat = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
                    .filterBounds(tile_geometry) \
                    .filterDate('2013-01-01', '2024-01-01')  # Updated date range for Landsat 8

        # Get the first image from the filtered dataset
        first_image = landsat.first()

        # Get the data for the shortwave infrared bands (SR_B5 and SR_B7)
        swir5 = first_image.select("SR_B5")  # Band 5 (SWIR 1)
        swir7 = first_image.select("SR_B7")  # Band 7 (SWIR 2)

        # Generate Map ID for visualization (without downloading the full image)
        mapid_b5 = swir5.getMapId({'min': 1, 'max': 65535})
        mapid_b7 = swir7.getMapId({'min': 1, 'max': 65535})

        # Return the map IDs for visualization (not downloading data)
        return mapid_b5, mapid_b7

    except Exception as e:
        print(f'Error fetching tile data: {e}')
        return None, None

# Process all tiles
all_mapids_b5 = []
all_mapids_b7 = []

for tile in tiles:
    lon_min, lat_min, lon_max, lat_max = tile
    mapid_b5, mapid_b7 = fetch_tile_data(lon_min, lat_min, lon_max, lat_max)
    if mapid_b5 is not None:
        all_mapids_b5.append(mapid_b5)
        all_mapids_b7.append(mapid_b7)

# If data was successfully fetched, display the Map IDs for visualization
if all_mapids_b5 and all_mapids_b7:
    print("Map IDs for Band 5 (SWIR 1) and Band 7 (SWIR 2) have been fetched successfully.")

    # Visualize the Map ID for Band 5 and Band 7
    for i, (mapid_b5, mapid_b7) in enumerate(zip(all_mapids_b5, all_mapids_b7)):
        print(f"Tile {i+1}:")
        print(f"  Band 5 Map ID: {mapid_b5}")
        print(f"  Band 7 Map ID: {mapid_b7}")
        
    # For a full visualization, you can view the images on the Earth Engine interactive map
    # Using the Map IDs to visualize in a browser
    print("\nTo visualize the images, open the following links in your browser:") 
    for i, (mapid_b5, mapid_b7) in enumerate(zip(all_mapids_b5, all_mapids_b7)):
        print(f"Tile {i+1} - Band 5: https://earthengine.google.com/map/viewer?mapid={mapid_b5['mapid']}")
        print(f"Tile {i+1} - Band 7: https://earthengine.google.com/map/viewer?mapid={mapid_b7['mapid']}")
else:
    print("No data was fetched.")
