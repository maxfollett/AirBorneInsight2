import ee
import geopandas as gpd
import numpy as np
import requests
import rasterio
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from datetime import datetime
import os

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project='cap2025-airborneinsight')

# User input for ROI and survey name
lat_range = input("Enter the latitude range (min,max) (e.g., 40,42): ").split(',')
lon_range = input("Enter the longitude range (min,max) (e.g., -114,-112): ").split(',')
survey_name = f"Lat_({lat_range[0]}_{lat_range[1]})_Lon_({lon_range[0]}_{lon_range[1]})"

# Convert inputs to floats
lat_min, lat_max = map(float, lat_range)
lon_min, lon_max = map(float, lon_range)

# Define ROI as a rectangle with lat/long coordinates
coordinates = [[lon_min, lat_min], [lon_max, lat_min], [lon_max, lat_max], [lon_min, lat_max]]

# Create a Shapely Polygon object for the ROI
roi = Polygon(coordinates)

# Create a GeoDataFrame with the polygon geometry
gdf = gpd.GeoDataFrame(geometry=[roi], crs="EPSG:4326")

# Get current date
current_date = datetime.now().strftime("%m%d")

# Create the folder for saving files
output_folder = os.path.join(os.path.expanduser("~/Desktop"), "SpectralBandData")
os.makedirs(output_folder, exist_ok=True)

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

    # Download and read the band images into numpy arrays
    bands = {}
    for band_name, band in [("B4", band4), ("B5", band5), ("B6", band6), ("B7", band7)]:
        try:
            # Define region and visualization parameters
            region = RECTgeometry.bounds().getInfo()
            params = {
                'region': region,  # Specify the ROI for the band
                'scale': 30,       # Resolution (in meters for Landsat)
                'format': 'GEO_TIFF',
                'crs': 'EPSG:4326'
            }

            # Get URL and fetch the data
            url = band.getThumbURL(params)
            response = requests.get(url)
            response.raise_for_status()  # Raise error for HTTP issues

            # Load data into Rasterio for processing
            with rasterio.MemoryFile(response.content) as memfile:
                with memfile.open() as dataset:
                    bands[band_name] = dataset.read(1)  # Read as numpy array
            response.close()
        except Exception as e:
            print(f"Error fetching band {band_name}: {e}")
            raise

    # Ensure all bands were downloaded correctly before proceeding
    if len(bands) != 4:
        raise Exception("One or more bands failed to download. Check error messages above.")

    # Compute band ratios
    ratio_4_5 = np.ma.divide(bands["B4"], bands["B5"])
    ratio_5_7 = np.ma.divide(bands["B5"], bands["B7"])

    # Save the georeferenced bands and ratios to .txt files
    def save_to_txt(data, name):
        output_filename = os.path.join(output_folder, f"{current_date}_{survey_name}_{name}.txt")
        np.savetxt(output_filename, data, fmt='%.6f')

    # Save bands
    for band_name, band_data in bands.items():
        save_to_txt(band_data, band_name)

    # Save ratios
    save_to_txt(ratio_4_5.astype('float32'), "Ratio_4_5")
    save_to_txt(ratio_5_7.astype('float32'), "Ratio_5_7")

    # Plot the images
    fig, ax = plt.subplots(3, 2, figsize=(15, 10))
    ax[0, 0].imshow(bands["B4"], extent=[lon_min, lon_max, lat_min, lat_max])
    ax[0, 0].set_title(f'Band 4 (Red)')
    ax[0, 1].imshow(bands["B5"], extent=[lon_min, lon_max, lat_min, lat_max])
    ax[0, 1].set_title(f'Band 5 (NIR)')
    ax[1, 0].imshow(bands["B6"], extent=[lon_min, lon_max, lat_min, lat_max])
    ax[1, 0].set_title(f'Band 6 (SWIR 1)')
    ax[1, 1].imshow(bands["B7"], extent=[lon_min, lon_max, lat_min, lat_max])
    ax[1, 1].set_title(f'Band 7 (SWIR 2)')
    ax[2, 0].imshow(ratio_4_5, extent=[lon_min, lon_max, lat_min, lat_max])
    ax[2, 0].set_title(f'Band 4/5 Ratio')
    ax[2, 1].imshow(ratio_5_7, extent=[lon_min, lon_max, lat_min, lat_max])
    ax[2, 1].set_title(f'Band 5/7 Ratio')

    for i in range(3):
        for j in range(2):
            if j == 0:
                ax[i, j].set_ylabel('Latitude')
            else:
                ax[i, j].set_yticklabels([])
            if i == 2:
                ax[i, j].set_xlabel('Longitude')
            else:
                ax[i, j].set_xticklabels([])

    fig.suptitle(f"Landsat Spectral Band Imagery of {survey_name}", fontsize=16)
    plt.subplots_adjust(top=0.92)
    plt.show()

    print("All 6 files saved successfully to the SpectralBandData folder.")

except Exception as e:
    print(f'Error: Unable to process Landsat Data. Exception: {e}')
