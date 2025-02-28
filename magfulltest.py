import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
from scipy import interpolate
import requests
from io import StringIO

# Inputs by user 
file_name = "richfield_mag.xyz"
Survey_name = "Richfield, Utah"

def load_csv_from_github():
    url = f'https://github.com/maxfollett/AirBorneInsight2/raw/main/CapDatabases/Raw/{file_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        csv_data = response.text
        df = pd.read_csv(StringIO(csv_data), header=None, sep='\s+', usecols=[5, 6, 12], names=["lat", "long", "corrected_magnetic"])
        return df
    else:
        print(f"Failed to load data, status code: {response.status_code}")
        return None

def remove_outliers(df):
    Q1_lat, Q3_lat = df['lat'].quantile([0.25, 0.75])
    IQR_lat = Q3_lat - Q1_lat
    Q1_long, Q3_long = df['long'].quantile([0.25, 0.75])
    IQR_long = Q3_long - Q1_long
    
    df_cleaned = df[(df['lat'].between(Q1_lat - 1.5 * IQR_lat, Q3_lat + 1.5 * IQR_lat)) &
                    (df['long'].between(Q1_long - 1.5 * IQR_long, Q3_long + 1.5 * IQR_long))]
    return df_cleaned

def filter_high_density_areas(df, gridsize=30, percentile_threshold=75):
    x, y = df['long'], df['lat']
    hexbin = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.close()
    
    density = hexbin.get_array()
    threshold = np.percentile(density, percentile_threshold)
    high_density_indices = np.where(density >= threshold)
    high_density_coords = hexbin.get_offsets()[high_density_indices]
    
    x_min, x_max = np.min(high_density_coords[:, 0]), np.max(high_density_coords[:, 0])
    y_min, y_max = np.min(high_density_coords[:, 1]), np.max(high_density_coords[:, 1])
    
    return x_min, x_max, y_min, y_max

def generate_combined_plot(df, x_min, x_max, y_min, y_max, gridsize=30):
    x, y = df['long'], df['lat']
    
    plt.figure(figsize=(10, 8))
    hexbin_plot = plt.hexbin(x, y, gridsize=gridsize, cmap='Blues')
    plt.colorbar(hexbin_plot, label='Data Density')
    plt.scatter(x, y, c='black', s=1, label='Survey Points')
    plt.plot([x_min, x_max, x_max, x_min, x_min],
             [y_min, y_min, y_max, y_max, y_min], 'r-', lw=2, label='High-Density Region')
    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f"Survey Area with High-Density Region: {Survey_name}")
    plt.legend()
    plt.show()

def perform_interpolation_with_extrapolation(df, grid_size=100):
    grid_x, grid_y = np.mgrid[df['long'].min():df['long'].max():grid_size*1j,
                               df['lat'].min():df['lat'].max():grid_size*1j]
    points = np.column_stack((df['long'], df['lat']))
    values = df['corrected_magnetic'].values
    
    grid_z = interpolate.griddata(points, values, (grid_x, grid_y), method='linear')
    nan_mask = np.isnan(grid_z)
    grid_z[nan_mask] = interpolate.griddata(points, values, (grid_x[nan_mask], grid_y[nan_mask]), method='nearest')
    
    return grid_x, grid_y, grid_z

def plot_interpolation(grid_x, grid_y, grid_z):
    plt.figure(figsize=(10, 8))
    plt.contourf(grid_x, grid_y, grid_z, levels=100, cmap='viridis')
    plt.colorbar(label='Interpolated Corrected Magnetic Value')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title("Linear Interpolation with Extrapolation of Corrected Magnetic Values")
    plt.show()

def main():
    df = load_csv_from_github()
    if df is None:
        return
    
    df_cleaned = remove_outliers(df)
    x_min, x_max, y_min, y_max = filter_high_density_areas(df_cleaned)
    df_filtered = df_cleaned[(df_cleaned['long'].between(x_min, x_max)) &
                             (df_cleaned['lat'].between(y_min, y_max))]
    
    generate_combined_plot(df_cleaned, x_min, x_max, y_min, y_max)
    grid_x, grid_y, grid_z = perform_interpolation_with_extrapolation(df_filtered)
    plot_interpolation(grid_x, grid_y, grid_z)

main()