import ee
import geopandas as gpd
from shapely.geometry import Polygon
from datetime import datetime
import os

# Set up authentication using your service account JSON file
SERVICE_ACCOUNT_EMAIL = "service-account-capstone-2025@cap2025-airborneinsight.iam.gserviceaccount.com"
KEY_FILE = r"C:\Users\19mlf3\Desktop\cap2025-airborneinsight-0312a0d58824.json"  # Update the path if needed

credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT_EMAIL, KEY_FILE)
ee.Initialize(credentials)

# User input for ROI and survey name
lat_range = input("Enter the latitude range (min,max) (e.g., 40,42): ").split(',')
lon_range = input("Enter the longitude range (min,max) (e.g., -114,-112): ").split(',')
# Build a safe survey name with underscores only (no parentheses or spaces)
survey_name = f"Lat_{lat_range[0].strip()}_{lat_range[1].strip()}_Lon_{lon_range[0].strip()}_{lon_range[1].strip()}"

lat_min, lat_max = map(float, lat_range)
lon_min, lon_max = map(float, lon_range)

# Define ROI as a rectangle using shapely
coordinates = [[lon_min, lat_min], [lon_max, lat_min], [lon_max, lat_max], [lon_min, lat_max]]
roi = Polygon(coordinates)
gdf = gpd.GeoDataFrame(geometry=[roi], crs="EPSG:4326")

# Get current date (for filename prefixes)
current_date = datetime.now().strftime("%m%d")

# Create Earth Engine geometry from the GeoDataFrame polygon
RECTgeometry = ee.Geometry.Polygon(gdf.geometry[0].exterior.coords[:])
export_region = RECTgeometry.getInfo()['coordinates']

# Access Landsat 8 data (Collection: LANDSAT/LC08/C02/T1_L2)
landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
filtered_landsat = landsat.filterBounds(RECTgeometry)
clipped_landsat = filtered_landsat.map(lambda image: image.clip(RECTgeometry))
median_image = clipped_landsat.median()

# Select spectral bands
band4 = median_image.select("SR_B4")  # Red band
band5 = median_image.select("SR_B5")  # NIR band
band6 = median_image.select("SR_B6")  # SWIR 1
band7 = median_image.select("SR_B7")  # SWIR 2

# Compute band ratios using Earth Engine operations
ratio_4_5 = band4.divide(band5)
ratio_5_7 = band5.divide(band7)

# Define common export parameters
export_params = {
    'region': export_region,
    'scale': 30,
    'crs': 'EPSG:4326',
    'maxPixels': 1e13
}

# Function to create and start an export task to Google Drive
def create_export_task(image, name):
    # Construct a safe description. Allowed characters: a..z, A..Z, 0..9, ".", ",", ":", ";", "_" or "-"
    description = f"Export_{name}_{current_date}_{survey_name}"
    # Truncate description to 100 characters if needed
    description = description[:100]
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder='LandsatExports',  # Folder in your Google Drive
        fileNamePrefix=f"{current_date}_{survey_name}_{name}",
        **export_params
    )
    task.start()
    print(f"Export task started for {name} with description: {description}")

# Create export tasks for each band and ratio image
create_export_task(band4, "B4")
create_export_task(band5, "B5")
create_export_task(band6, "B6")
create_export_task(band7, "B7")
create_export_task(ratio_4_5, "Ratio_4_5")
create_export_task(ratio_5_7, "Ratio_5_7")

print("All export tasks have been started. Monitor the tasks in the Earth Engine Task Manager or check your Google Drive folder 'LandsatExports'.")
