import ee
import geopandas as gpd
import numpy as np
import requests
import rasterio
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Initialize Earth Engine
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

try:
    # Convert GeoDataFrame to Earth Engine Geometry
    RECTgeometry = ee.Geometry.Polygon(gdf.geometry[0].exterior.coords[:])

    # Access Landsat 4 data
    landsat = ee.ImageCollection("LANDSAT/LT04/C02/T1_L2")  # Select Landsat 4 v2
    filtered_landsat = landsat.filterBounds(RECTgeometry)  # Filter by ROI

    # Trim the dataset to only include the area within the polygon
    trimmed_landsat = filtered_landsat.map(lambda image: image.clip(RECTgeometry))

    # Get the first image from the trimmed dataset
    first_image = trimmed_landsat.first()  # Select first image

    # Get the data for the shortwave infrared band (SR_B5 and SR_B7)
    swir5 = first_image.select("SR_B5")  # Select Band 5 (SWIR 1)
    swir7 = first_image.select("SR_B7")  # Select Band 7 (SWIR 2)

    # Get the download URLs for the band images
    url_b5 = swir5.getThumbURL({'min': 1, 'max': 65535})  # Get thumbnail URL for Band 5
    url_b7 = swir7.getThumbURL({'min': 1, 'max': 65535})  # Get thumbnail URL for Band 7

    # Download the band images
    response_b5 = requests.get(url_b5)
    response_b7 = requests.get(url_b7)

    # Read the images into numpy arrays
    with rasterio.MemoryFile() as memfile:
        memfile.write(response_b5.content)
        with memfile.open() as dataset:
            band5 = dataset.read(1)

    with rasterio.MemoryFile() as memfile:
        memfile.write(response_b7.content)
        with memfile.open() as dataset:
            band7 = dataset.read(1)

    # Close the response objects
    response_b5.close()
    response_b7.close()

    # Apply masks for the valid range of values in the bands
    mask_b5 = np.logical_and(band5 > 0, band5 < 255)
    mask_b7 = np.logical_and(band7 > 0, band7 < 255)

    # Keep the full image and just mask invalid values during plotting
    masked_band5 = np.ma.masked_where(~mask_b5, band5)
    masked_band7 = np.ma.masked_where(~mask_b7, band7)

    # Compute the ratio of Band 5 / Band 7
    ratio_band5_7 = np.ma.divide(masked_band5, masked_band7)

    # Plot the images if 'plot' is True
    if plot:
        fig, ax = plt.subplots(1, 3, figsize=(15, 5))

        ax[0].imshow(masked_band5, extent=[lon_min, lon_max, lat_min, lat_max])
        ax[0].set_title(f'{survey_name} - Band 5')
        ax[0].set_xlabel('Longitude')
        ax[0].set_ylabel('Latitude')

        ax[1].imshow(masked_band7, extent=[lon_min, lon_max, lat_min, lat_max])
        ax[1].set_title(f'{survey_name} - Band 7')
        ax[1].set_xlabel('Longitude')
        ax[1].set_ylabel('Latitude')

        ax[2].imshow(ratio_band5_7, extent=[lon_min, lon_max, lat_min, lat_max])
        ax[2].set_title(f'{survey_name} - Band 5/7 Ratio')
        ax[2].set_xlabel('Longitude')
        ax[2].set_ylabel('Latitude')

        plt.tight_layout()
        plt.show()

except Exception as e:
    print(f'Error: Unable to access Landsat Data. Exception: {e}')
    ratio_band5_7 = False
40