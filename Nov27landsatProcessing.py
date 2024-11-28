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

    # Access Landsat 8 data
    landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")  # Select Landsat 8 v2

    # Filter the image collection by the ROI
    filtered_landsat = landsat.filterBounds(RECTgeometry)

    # Clip the entire image collection to the ROI
    clipped_landsat = filtered_landsat.map(lambda image: image.clip(RECTgeometry))

    # Get the median image from the collection
    median_image = clipped_landsat.median()

    # Select bands
    band4 = median_image.select("SR_B4")  # Red band
    band5 = median_image.select("SR_B5")  # NIR band
    band6 = median_image.select("SR_B6")  # SWIR 1
    band7 = median_image.select("SR_B7")  # SWIR 2

    # Define the region for thumbnails
    region = RECTgeometry.getInfo()['coordinates']

    # Get download URLs for the bands
    urls = {
        "B4": band4.getThumbURL({'min': 1, 'max': 65535, 'region': region, 'dimensions': 512}),
        "B5": band5.getThumbURL({'min': 1, 'max': 65535, 'region': region, 'dimensions': 512}),
        "B6": band6.getThumbURL({'min': 1, 'max': 65535, 'region': region, 'dimensions': 512}),
        "B7": band7.getThumbURL({'min': 1, 'max': 65535, 'region': region, 'dimensions': 512}),
    }

    # Download and read the band images into numpy arrays
    bands = {}
    for key, url in urls.items():
        response = requests.get(url)
        with rasterio.MemoryFile() as memfile:
            memfile.write(response.content)
            with memfile.open() as dataset:
                bands[key] = dataset.read(1)
        response.close()

    # Apply masks for valid ranges
    masks = {key: np.logical_and(band > 0, band < 255) for key, band in bands.items()}
    masked_bands = {key: np.ma.masked_where(~masks[key], band) for key, band in bands.items()}

    # Compute band ratios
    ratio_4_5 = np.ma.divide(masked_bands["B4"], masked_bands["B5"])
    ratio_5_7 = np.ma.divide(masked_bands["B5"], masked_bands["B7"])

    # Plot the images in a 3x2 grid
    if plot:
        fig, ax = plt.subplots(3, 2, figsize=(15, 10))

        # Plot the individual bands
        ax[0, 0].imshow(masked_bands["B4"], extent=[lon_min, lon_max, lat_min, lat_max])
        ax[0, 0].set_title(f'Band 4 (Red)')

        ax[0, 1].imshow(masked_bands["B5"], extent=[lon_min, lon_max, lat_min, lat_max])
        ax[0, 1].set_title(f'Band 5 (NIR)')

        ax[1, 0].imshow(masked_bands["B6"], extent=[lon_min, lon_max, lat_min, lat_max])
        ax[1, 0].set_title(f'Band 6 (SWIR 1)')

        ax[1, 1].imshow(masked_bands["B7"], extent=[lon_min, lon_max, lat_min, lat_max])
        ax[1, 1].set_title(f'Band 7 (SWIR 2)')

        ax[2, 0].imshow(ratio_4_5, extent=[lon_min, lon_max, lat_min, lat_max])
        ax[2, 0].set_title(f'Band 4/5 Ratio')

        ax[2, 1].imshow(ratio_5_7, extent=[lon_min, lon_max, lat_min, lat_max])
        ax[2, 1].set_title(f'Band 5/7 Ratio')

        # Customize tick labels and axis titles
        for i in range(3):  # Rows
            for j in range(2):  # Columns
                if j == 0:  # Leftmost plots
                    ax[i, j].set_ylabel('Latitude')
                else:  # Remove y-axis ticks for right column
                    ax[i, j].set_yticklabels([])

                if i == 2:  # Bottom plots
                    ax[i, j].set_xlabel('Longitude')
                else:  # Remove x-axis ticks for top rows
                    ax[i, j].set_xticklabels([])

        # Add a master title for the entire figure
        fig.suptitle(f"Survey: {survey_name}", fontsize=16, fontweight='bold')

        # Adjust layout to prevent overlap (this will ensure the title doesn't get clipped)
        plt.subplots_adjust(top=0.92)  # Make room for suptitle
        plt.show()

except Exception as e:
    print(f'Error: Unable to access Landsat Data. Exception: {e}')
