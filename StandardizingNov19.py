import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
import requests
from io import StringIO

# Input the CSV filename
file_name = "CedarCityCleaned.csv"  # Example survey file

# Load CSV data from GitHub
def load_csv_from_github(file_name):
    url = f'https://github.com/maxfollett/AirBorneInsight2/raw/main/CapDatabases/Cleaned/{file_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        csv_data = response.text
        df = pd.read_csv(StringIO(csv_data), skiprows=1, usecols=[0, 1, 3], names=["lat", "long", "corrected_field"])
        return df
    else:
        print(f"Failed to load data for {file_name}, status code: {response.status_code}")
        return None

# Filter High-Density Areas
def filter_high_density_areas(df, gridsize=50, percentile_threshold=25):
    x = df['long']
    y = df['lat']
    
    hexbin = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.close()

    density = hexbin.get_array()
    threshold = np.percentile(density, percentile_threshold)
    
    high_density_indices = np.where(density >= threshold)
    high_density_coords = hexbin.get_offsets()[high_density_indices]

    high_density_polygons = [
        box(coord[0] - gridsize, coord[1] - gridsize, coord[0] + gridsize, coord[1] + gridsize)
        for coord in high_density_coords
    ]
    high_density_union = unary_union(high_density_polygons)
    df_filtered = df[df.apply(lambda row: high_density_union.contains(Point(row['long'], row['lat'])), axis=1)]
    
    return df_filtered, high_density_union

# Compute Minimum Rotated Rectangle
def compute_minimum_rotated_rectangle(polygon):
    return polygon.minimum_rotated_rectangle

# Plot Survey Rectangle
def plot_survey_footprint(rectangle):
    plt.figure(figsize=(8, 6))
    
    x, y = rectangle.exterior.xy
    plt.plot(x, y, 'r-', label="Survey Footprint (Red)")
    
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Survey Footprint")
    plt.legend()
    plt.grid(True)
    plt.show()

# Main Workflow
def preprocess_data(file_name):
    df = load_csv_from_github(file_name)
    if df is None:
        return None, None

    df_high_density, high_density_union = filter_high_density_areas(df, gridsize=50)
    rotated_rectangle = compute_minimum_rotated_rectangle(high_density_union)
    return df_high_density, rotated_rectangle

# Run Processing
df, rect = preprocess_data(file_name)  # Process the single survey

if rect:
    plot_survey_footprint(rect)
    print("Rotated Rectangle Coordinates:")
    print(list(rect.exterior.coords))

else:
    print("The rectangle could not be generated.")

