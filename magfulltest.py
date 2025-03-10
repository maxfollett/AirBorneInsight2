import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import os
import requests
from io import StringIO

# Define constants
file_name = "richfield_mag.xyz"
Survey_name = "Richfield, Utah"

# Get user's desktop path
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_folder = os.path.join(desktop_path, "magnetic_txt_files")
os.makedirs(output_folder, exist_ok=True)

# Function to load CSV data from GitHub
def load_csv_from_github():
    url = f'https://github.com/maxfollett/AirBorneInsight2/raw/main/CapDatabases/Raw/{file_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        csv_data = response.text
        df = pd.read_csv(StringIO(csv_data), header=None, sep='\\s+', usecols=[5, 6, 12],
                         names=["lat", "long", "corrected_magnetic"])
        return df
    else:
        print(f"Failed to load data, status code: {response.status_code}")
        return None

# Function to perform interpolation
def perform_interpolation_with_extrapolation(df, grid_size=1114):
    grid_x, grid_y = np.mgrid[df['long'].min():df['long'].max():grid_size*1j,
                               df['lat'].min():df['lat'].max():grid_size*1j]
    points = np.column_stack((df['long'], df['lat']))
    values = df['corrected_magnetic'].values
    
    grid_z = interpolate.griddata(points, values, (grid_x, grid_y), method='linear')
    nan_mask = np.isnan(grid_z)
    grid_z[nan_mask] = interpolate.griddata(points, values, (grid_x[nan_mask], grid_y[nan_mask]), method='nearest')
    
    return grid_x, grid_y, grid_z

# Function to save data to a .txt file
def save_to_txt(grid_z, lat_input, long_input):
    filename = f"MAG_{lat_input}_{long_input}.txt"
    filepath = os.path.join(output_folder, filename)
    np.savetxt(filepath, grid_z, fmt='%.6f')
    print(f"Saved file: {filepath}")

# Main function
def main():
    df = load_csv_from_github()
    if df is None:
        return
    
    try:
        lat_input = float(input("Enter latitude: "))
        long_input = float(input("Enter longitude: "))
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        return
    
    df_filtered = df[(df['lat'].between(lat_input - 0.1, lat_input + 0.1)) &
                     (df['long'].between(long_input - 0.1, long_input + 0.1))]
    
    if df_filtered.empty:
        print("No data found for the given latitude and longitude range.")
        return
    
    grid_x, grid_y, grid_z = perform_interpolation_with_extrapolation(df_filtered)
    save_to_txt(grid_z, lat_input, long_input)

if __name__ == "__main__":
    main()
