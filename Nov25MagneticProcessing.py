import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import requests
from io import StringIO
import os

# Input the CSV filename
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

# Remove outliers based on IQR (Interquartile Range)
def remove_outliers(df):
    Q1_lat = df['lat'].quantile(0.25)
    Q3_lat = df['lat'].quantile(0.75)
    IQR_lat = Q3_lat - Q1_lat
    lower_bound_lat = Q1_lat - 1.5 * IQR_lat
    upper_bound_lat = Q3_lat + 1.5 * IQR_lat

    Q1_long = df['long'].quantile(0.25)
    Q3_long = df['long'].quantile(0.75)
    IQR_long = Q3_long - Q1_long
    lower_bound_long = Q1_long - 1.5 * IQR_long
    upper_bound_long = Q3_long + 1.5 * IQR_long

    # Filter out points outside the IQR range for both latitude and longitude
    df_cleaned = df[(df['lat'] >= lower_bound_lat) & (df['lat'] <= upper_bound_lat) & 
                    (df['long'] >= lower_bound_long) & (df['long'] <= upper_bound_long)]
    return df_cleaned

# Filter High-Density Areas Using Hexbin
def filter_high_density_areas(df, gridsize=30, percentile_threshold=75):
    x = df['long']
    y = df['lat']
    
    hexbin = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.close()

    density = hexbin.get_array()
    threshold = np.percentile(density, percentile_threshold)
    
    # Get coordinates of hexagons above the threshold
    high_density_indices = np.where(density >= threshold)
    high_density_coords = hexbin.get_offsets()[high_density_indices]
    
    # Calculate the bounding box for the high-density points
    x_min = np.min(high_density_coords[:, 0])
    x_max = np.max(high_density_coords[:, 0])
    y_min = np.min(high_density_coords[:, 1])
    y_max = np.max(high_density_coords[:, 1])

    return high_density_coords, x_min, x_max, y_min, y_max, hexbin

# Generate Combined Plot with Hexbin and High-Density Rectangles
def generate_combined_plot(df, gridsize=30, high_density_threshold=75):
    x = df['long']
    y = df['lat']
    
    # Get high-density points and their bounding box
    high_density_coords, x_min, x_max, y_min, y_max, hexbin = filter_high_density_areas(df, gridsize=gridsize, percentile_threshold=high_density_threshold)
    
    # Define the entire survey boundary
    survey_x_min = df['long'].min()
    survey_x_max = df['long'].max()
    survey_y_min = df['lat'].min()
    survey_y_max = df['lat'].max()
    
    # Plot hexbin background
    plt.figure(figsize=(10, 8))
    hexbin_plot = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.colorbar(hexbin_plot, label='Data Density')

    # Plot the survey route as points (black, small, solid)
    plt.scatter(x, y, c='black', s=1, label='Survey Points')  # Smaller points for the survey path

    # Plot the red rectangle around the high-density region
    plt.plot([x_min, x_max, x_max, x_min, x_min],
             [y_min, y_min, y_max, y_max, y_min], 'r-', lw=2, label='High-Density Region')  
    
    # Plot the outline of the survey area
    plt.plot([survey_x_min, survey_x_max, survey_x_max, survey_x_min, survey_x_min],
             [survey_y_min, survey_y_min, survey_y_max, survey_y_max, survey_y_min],
             'k--', lw=1.5, label='Survey Boundary')  
    
    # Add Labels and Title
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f"Survey Area with High-Density Region: {os.path.splitext(file_name)[0]}")
    plt.legend()
    plt.show()

# Main Data Processing Workflow
def preprocess_data():
    df = load_csv_from_github()
    
    if df is None:
        print("Error loading data")
        return None
    
    # Step 1: Remove Outliers in Latitude and Longitude
    df_cleaned = remove_outliers(df)
    
    # Generate combined plot with hexbin and survey boundary
    generate_combined_plot(df_cleaned, gridsize=30, high_density_threshold=75)
    
    return df_cleaned

# Run the preprocessing
preprocessed_data = preprocess_data()

