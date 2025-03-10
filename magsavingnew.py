import pandas as pd  # For handling tabular data
import numpy as np  # For numerical computations
import matplotlib.pyplot as plt  # For data visualization
from shapely.geometry import Point  # For working with geometric data
from scipy import interpolate  # For interpolation and extrapolation
import requests  # For making HTTP requests to fetch data
from io import StringIO  # For handling in-memory text streams
import os  # For file operations

# Define the file name and survey name
file_name = "richfield_mag.xyz"
Survey_name = "Richfield, Utah"
output_folder = os.path.expanduser("~/Desktop/magnetic_txt_files")
os.makedirs(output_folder, exist_ok=True)

# Function to load CSV data from a GitHub repository
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

# Function to remove outliers
def remove_outliers(df):
    Q1_lat, Q3_lat = df['lat'].quantile([0.25, 0.75])
    IQR_lat = Q3_lat - Q1_lat
    Q1_long, Q3_long = df['long'].quantile([0.25, 0.75])
    IQR_long = Q3_long - Q1_long
    
    df_cleaned = df[(df['lat'].between(Q1_lat - 1.5 * IQR_lat, Q3_lat + 1.5 * IQR_lat)) & 
                    (df['long'].between(Q1_long - 1.5 * IQR_long, Q3_long + 1.5 * IQR_long))]
    return df_cleaned

# Function to interpolate and extrapolate missing magnetic data
def perform_interpolation_with_extrapolation(df, grid_size=1114):
    grid_x, grid_y = np.mgrid[df['long'].min():df['long'].max():grid_size*1j,
                               df['lat'].min():df['lat'].max():grid_size*1j]
    points = np.column_stack((df['long'], df['lat']))
    values = df['corrected_magnetic'].values
    
    grid_z = interpolate.griddata(points, values, (grid_x, grid_y), method='linear')
    
    nan_mask = np.isnan(grid_z)
    grid_z[nan_mask] = interpolate.griddata(points, values, (grid_x[nan_mask], grid_y[nan_mask]), method='nearest')
    
    return grid_x, grid_y, grid_z

# Function to save data as .txt file
def save_to_txt(data, filename):
    filepath = os.path.join(output_folder, filename)
    np.savetxt(filepath, data, fmt='%.6f')
    print(f"Saved: {filepath}")

# Main function to execute the processing pipeline
def main():
    df = load_csv_from_github()
    if df is None:
        return
    
    df_cleaned = remove_outliers(df)
    
    # Get user input for latitude and longitude range
    lat_min, lat_max = map(float, input("Enter latitude range (min, max): ").split(','))
    long_min, long_max = map(float, input("Enter longitude range (min, max): ").split(','))
    
    # Filter data within inputted lat/lon range
    df_filtered = df_cleaned[(df_cleaned['lat'].between(lat_min, lat_max)) & 
                             (df_cleaned['long'].between(long_min, long_max))]
    
    grid_x, grid_y, grid_z = perform_interpolation_with_extrapolation(df_filtered)
    
    filename = f"MAG_{lat_min}_{lat_max}_{long_min}_{long_max}.txt"
    save_to_txt(grid_z, filename)

main()
