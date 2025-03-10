import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from io import StringIO
from scipy.interpolate import griddata

# Function to load XYZ file from GitHub repository
def load_xyz_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        xyz_data = response.text
        cleaned_data = []

        # Track malformed lines
        malformed_lines = []

        # Process each line
        for i, line in enumerate(xyz_data.splitlines(), start=1):
            columns = line.split()
            if len(columns) == 3:  # Keep valid lines
                cleaned_data.append(" ".join(columns))
            else:
                malformed_lines.append((i, line))

        # Log malformed lines
        if malformed_lines:
            print(f"Found {len(malformed_lines)} malformed lines. Skipping these:")
            for idx, malformed in malformed_lines[:10]:  # Display first 10 errors
                print(f"Line {idx}: {malformed}")
            print("... (skipping remaining malformed lines)")

        # Join cleaned data
        cleaned_xyz_data = "\n".join(cleaned_data)

        # Load into pandas
        try:
            df = pd.read_csv(StringIO(cleaned_xyz_data), sep='\s+', header=None, names=['x', 'y', 'value'])
            return df
        except Exception as e:
            print(f"Error reading the cleaned data: {e}")
            return None
    else:
        print(f"Failed to load data, status code: {response.status_code}")
        return None

# Function to get user input for the range
def get_range_input(prompt):
    while True:
        try:
            user_input = input(prompt)
            range_values = user_input.split(',')
            min_value = float(range_values[0].strip())
            max_value = float(range_values[1].strip())
            if min_value > max_value:
                print("Minimum value cannot be greater than maximum value. Please try again.")
                continue
            return min_value, max_value
        except ValueError:
            print("Invalid input. Please enter two comma-separated numbers (e.g., -117, -110).")

# Function to interpolate data onto a 1114x1114 grid
def interpolate_to_grid(data, longitude_min, longitude_max, latitude_min, latitude_max):
    grid_x, grid_y = np.linspace(longitude_min, longitude_max, 1114), np.linspace(latitude_min, latitude_max, 1114)
    grid_x, grid_y = np.meshgrid(grid_x, grid_y)

    grid_z = griddata((data['x'], data['y']), data['value'], (grid_x, grid_y), method='cubic')

    # Fill NaNs using nearest interpolation
    nan_mask = np.isnan(grid_z)
    if np.any(nan_mask):
        grid_z[nan_mask] = griddata(
            (data['x'], data['y']), data['value'], (grid_x[nan_mask], grid_y[nan_mask]), method='nearest'
        )

    return grid_x, grid_y, grid_z

# Function to plot interpolated data
def plot_data(grid_x, grid_y, grid_z, title):
    plt.figure(figsize=(12, 10))
    plt.contourf(grid_x, grid_y, grid_z, cmap='viridis', levels=100)
    plt.colorbar(label='Gravity Value (milligal)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(title)
    plt.show()

# Function to save data as .txt file
def save_to_txt(grid_x, grid_y, grid_z, filename):
    os.makedirs(os.path.expanduser("~/Desktop/grav_txtfiles"), exist_ok=True)
    filepath = os.path.expanduser(f"~/Desktop/grav_txtfiles/{filename}.txt")

    np.savetxt(filepath, grid_z, fmt='%.6f', delimiter=' ', header="Interpolated gravity values grid")
    print(f"Saved: {filepath}")

# GitHub raw URLs
url1 = "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/USbougerGravData.xyz"
url2 = "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/isograv.xyz"

# Get user-defined latitude and longitude ranges
latitude_min, latitude_max = get_range_input("Enter the latitude range (min,max) (e.g., 40,42) for both plots: ")
longitude_min, longitude_max = get_range_input("Enter the longitude range (min,max) (e.g., -114,-112) for both plots: ")

# Get survey name
survey_name1 = input("Enter the name of the survey: ")

# Load, process, and plot Bouguer gravity data
data1 = load_xyz_from_github(url1)
if data1 is not None:
    filtered_data1 = data1[(data1['x'] >= longitude_min) & (data1['x'] <= longitude_max) &
                            (data1['y'] >= latitude_min) & (data1['y'] <= latitude_max)]
    if not filtered_data1.empty:
        grid_x, grid_y, grid_z = interpolate_to_grid(filtered_data1, longitude_min, longitude_max, latitude_min, latitude_max)
        plot_data(grid_x, grid_y, grid_z, f"Bouguer Anomaly Map for {survey_name1}")
        save_to_txt(grid_x, grid_y, grid_z, f"{survey_name1}_Bouguer_{latitude_min}_{latitude_max}_{longitude_min}_{longitude_max}")

# Load, process, and plot Isostatic gravity data
data2 = load_xyz_from_github(url2)
if data2 is not None:
    filtered_data2 = data2[(data2['x'] >= longitude_min) & (data2['x'] <= longitude_max) &
                            (data2['y'] >= latitude_min) & (data2['y'] <= latitude_max)]
    if not filtered_data2.empty:
        grid_x, grid_y, grid_z = interpolate_to_grid(filtered_data2, longitude_min, longitude_max, latitude_min, latitude_max)
        plot_data(grid_x, grid_y, grid_z, f"Isostatic Anomaly Map for {survey_name1}")
        save_to_txt(grid_x, grid_y, grid_z, f"{survey_name1}_Isograv_{latitude_min}_{latitude_max}_{longitude_min}_{longitude_max}")
