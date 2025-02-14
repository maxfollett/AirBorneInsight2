import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from io import StringIO
from scipy import interpolate

# Input the standardized CSV filename
file_name = "Richfield, Utah_HighDensity_2025-02-14.csv"

# Load CSV data from GitHub
def load_csv_from_github():
    url = f'https://github.com/maxfollett/AirBorneInsight2/raw/main/CapDatabases/Standardized/{file_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        csv_data = response.text
        df = pd.read_csv(StringIO(csv_data))
        return df
    else:
        print(f"Failed to load data, status code: {response.status_code}")
        return None

# Linear Interpolation with Nearest Neighbor Extrapolation
def perform_interpolation_with_extrapolation(df, grid_size=100):
    # Create grid for interpolation
    grid_x, grid_y = np.mgrid[df['long'].min():df['long'].max():grid_size*1j,
                               df['lat'].min():df['lat'].max():grid_size*1j]
    
    # Extract the x, y, and z (magnetic values) from the dataframe
    points = np.column_stack((df['long'], df['lat']))
    values = df['corrected_magnetic'].values
    
    # Perform linear interpolation using scipy's griddata (linear method)
    grid_z = interpolate.griddata(points, values, (grid_x, grid_y), method='linear')
    
    # Identify NaN values in the interpolated grid
    nan_mask = np.isnan(grid_z)
    
    # Apply nearest neighbor extrapolation to NaN values
    grid_z[nan_mask] = interpolate.griddata(points, values, (grid_x[nan_mask], grid_y[nan_mask]), method='nearest')

    return grid_x, grid_y, grid_z

# Plot the Interpolation result with Extrapolation
def plot_interpolation_with_extrapolation(grid_x, grid_y, grid_z):
    plt.figure(figsize=(10, 8))
    plt.contourf(grid_x, grid_y, grid_z, levels=100, cmap='viridis')
    plt.colorbar(label='Interpolated Corrected Magnetic Value')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f"Linear Interpolation with Nearest Neighbor Extrapolation of Corrected Magnetic Values")
    plt.show()

# Main Data Processing Workflow
def process_and_interpolate():
    df = load_csv_from_github()
    
    if df is None:
        print("Error loading data")
        return
    
    # Step 1: Perform Linear Interpolation with Nearest Neighbor Extrapolation
    grid_x, grid_y, grid_z = perform_interpolation_with_extrapolation(df)
    
    # Step 2: Plot the interpolation with extrapolated values for missing data
    plot_interpolation_with_extrapolation(grid_x, grid_y, grid_z)

# Run the interpolation process
process_and_interpolate()
