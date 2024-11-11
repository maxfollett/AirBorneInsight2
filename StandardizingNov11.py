import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import requests
from io import StringIO
import os

# Set the CSV filename
file_name = "CedarCityCleaned.csv"

# Load CSV data from GitHub
def load_csv_from_github():
    url = f'https://github.com/maxfollett/AirBorneInsight2/raw/main/CapDatabases/Cleaned/{file_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        csv_data = response.text
        # Skip the first row (header row with irrelevant titles) and ignore the third column
        df = pd.read_csv(StringIO(csv_data), skiprows=1, usecols=[0, 1, 3], names=["lat", "long", "corrected_magnetic"])
        return df
    else:
        print(f"Failed to load data, status code: {response.status_code}")
        return None

# Step 1: Generate Hexbin Plot of Entire Survey Area
def generate_hexbin_plot(df, gridsize=50):
    x = df['long']
    y = df['lat']
    
    plt.figure(figsize=(8, 6))
    plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.colorbar(label='Data Density')
    plt.xlabel('Longitude (DD)')
    plt.ylabel('Latitude (DD)')
    plt.title(f"Hexbin Plot of {os.path.splitext(file_name)[0]} Survey Area")
    plt.show()

# Step 2: Filter High-Density Areas Using Hexbin
def filter_high_density_areas(df, gridsize=50, percentile_threshold=25):
    x = df['long']
    y = df['lat']
    
    hexbin = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.close()

    density = hexbin.get_array()
    threshold = np.percentile(density, percentile_threshold)
    
    # Get coordinates of hexagons above the threshold
    high_density_indices = np.where(density >= threshold)
    high_density_coords = hexbin.get_offsets()[high_density_indices]

    # Filter original data points to only include those in high-density hexagons
    high_density_polygons = [
        Polygon([
            (coord[0] - gridsize, coord[1] - gridsize),
            (coord[0] + gridsize, coord[1] - gridsize),
            (coord[0] + gridsize, coord[1] + gridsize),
            (coord[0] - gridsize, coord[1] + gridsize)
        ]) for coord in high_density_coords
    ]
    high_density_union = unary_union(high_density_polygons)

    # Filter df to keep only points within high-density hexagons
    df_filtered = df[df.apply(lambda row: high_density_union.contains(Point(row['long'], row['lat'])), axis=1)]
    return df_filtered

# Step 3: Generate Hexbin Plot of Kept (High-Density) Data
def generate_kept_hexbin_plot(df_high_density, gridsize=50):
    plt.figure(figsize=(8, 6))
    
    # Create hexbin plot with adjusted color scheme and borders
    hb = plt.hexbin(df_high_density['long'], df_high_density['lat'], gridsize=gridsize, 
                    cmap='coolwarm', edgecolors='k', linewidths=0.3)
    
    # Add color bar to show data density
    cb = plt.colorbar(hb, label='Data Density')
    cb.set_ticks([0, max(hb.get_array()) / 2, max(hb.get_array())])
    
    # Set labels and title for better clarity
    plt.xlabel('Longitude (DD)')
    plt.ylabel('Latitude (DD)')
    plt.title(f"High-Density Hexbin Plot of {os.path.splitext(file_name)[0]}")
    
    # Show the plot
    plt.show()

# Main Data Processing Workflow
def preprocess_data():
    df = load_csv_from_github()
    
    if df is None:
        print("Error loading data")
        return None
    
    # Generate hexbin plot of the entire survey area
    generate_hexbin_plot(df, gridsize=50)
    
    # Filter high-density areas based on hexbin
    df_high_density = filter_high_density_areas(df, gridsize=50)
    
    # Generate hexbin plot for the kept (high-density) data
    generate_kept_hexbin_plot(df_high_density, gridsize=50)
    
    return df_high_density

# Run the preprocessing
preprocessed_data = preprocess_data()



