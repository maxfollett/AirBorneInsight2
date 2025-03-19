import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from io import StringIO
from scipy.interpolate import griddata

def interpolate_to_grid(data, lon_min, lon_max, lat_min, lat_max, grid_size):
    rows, cols = grid_size
    grid_x = np.linspace(lon_min, lon_max, cols)
    grid_y = np.linspace(lat_min, lat_max, rows)
    grid_x, grid_y = np.meshgrid(grid_x, grid_y)
    grid_z = griddata((data['x'], data['y']), data['value'], (grid_x, grid_y), method='cubic')

    nan_mask = np.isnan(grid_z)
    if np.any(nan_mask):
        grid_z[nan_mask] = griddata((data['x'], data['y']), data['value'], (grid_x[nan_mask], grid_y[nan_mask]), method='nearest')

    return grid_x, grid_y, grid_z

def resample_to_target_size(x, y, z, target_shape, lon_min, lon_max, lat_min, lat_max):
    rows, cols = target_shape
    resample_x = np.linspace(lon_min, lon_max, cols)
    resample_y = np.linspace(lat_min, lat_max, rows)
    resample_x, resample_y = np.meshgrid(resample_x, resample_y)
    resample_z = griddata((x.flatten(), y.flatten()), z.flatten(), (resample_x, resample_y), method='cubic')

    nan_mask = np.isnan(resample_z)
    if np.any(nan_mask):
        resample_z[nan_mask] = griddata((x.flatten(), y.flatten()), z.flatten(), (resample_x[nan_mask], resample_y[nan_mask]), method='nearest')

    return resample_x, resample_y, resample_z

def plot_subplots(grid_x1, grid_y1, grid_z1, title1, grid_x2, grid_y2, grid_z2, title2):
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))

    c1 = axs[0].contourf(grid_x1, grid_y1, grid_z1, cmap='viridis', levels=100)
    fig.colorbar(c1, ax=axs[0], label='Gravity Value (milligal)')
    axs[0].set_xlabel('Longitude')
    axs[0].set_ylabel('Latitude')
    axs[0].set_title(title1)

    c2 = axs[1].contourf(grid_x2, grid_y2, grid_z2, cmap='viridis', levels=100)
    fig.colorbar(c2, ax=axs[1], label='Gravity Value (milligal)')
    axs[1].set_xlabel('Longitude')
    axs[1].set_ylabel('Latitude')
    axs[1].set_title(title2)

    plt.tight_layout()
    plt.show()

def save_to_txt(grid_x, grid_y, grid_z, filename):
    os.makedirs(os.path.expanduser("~/Desktop/grav_txtfiles"), exist_ok=True)
    filepath = os.path.expanduser(f"~/Desktop/grav_txtfiles/{filename}.txt")
    np.savetxt(filepath, grid_z, fmt='%.6f', delimiter=' ', header="Interpolated gravity values grid")
    print(f"Saved: {filepath}")

# Get user-defined latitude and longitude ranges
latitude_min, latitude_max = map(float, input("Enter the latitude range (min,max): ").split(','))
longitude_min, longitude_max = map(float, input("Enter the longitude range (min,max): ").split(','))

# Expand ROI by 0.3 degrees
expanded_lat_min, expanded_lat_max = latitude_min - 0.3, latitude_max + 0.3
expanded_lon_min, expanded_lon_max = longitude_min - 0.3, longitude_max + 0.3

survey_name = input("Enter the name of the survey: ")

# Load Bouguer and Isostatic data
datasets = {
    "Bouguer": "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/USbougerGravData.xyz",
    "Isostatic": "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/isograv.xyz"
}

cropped_results = {}

for key, url in datasets.items():
    data = pd.read_csv(url, sep='\s+', header=None, names=['x', 'y', 'value'])
    filtered_data = data[(data['x'] >= expanded_lon_min) & (data['x'] <= expanded_lon_max) &
                         (data['y'] >= expanded_lat_min) & (data['y'] <= expanded_lat_max)]

    # Interpolate on expanded area
    grid_x, grid_y, grid_z = interpolate_to_grid(filtered_data, expanded_lon_min, expanded_lon_max, expanded_lat_min, expanded_lat_max, grid_size=(int(1486*1.2), int(2116*1.2)))

    # Crop based on actual user ROI
    crop_mask_x = (grid_x[0, :] >= longitude_min) & (grid_x[0, :] <= longitude_max)
    crop_mask_y = (grid_y[:, 0] >= latitude_min) & (grid_y[:, 0] <= latitude_max)
    cropped_grid_x = grid_x[np.ix_(crop_mask_y, crop_mask_x)]
    cropped_grid_y = grid_y[np.ix_(crop_mask_y, crop_mask_x)]
    cropped_grid_z = grid_z[np.ix_(crop_mask_y, crop_mask_x)]

    # Resample cropped area to exactly (1486, 2116)
    resample_x, resample_y, resample_z = resample_to_target_size(cropped_grid_x, cropped_grid_y, cropped_grid_z, (1486, 2116), longitude_min, longitude_max, latitude_min, latitude_max)

    cropped_results[key] = (resample_x, resample_y, resample_z)
    save_to_txt(resample_x, resample_y, resample_z, f"{survey_name}_{key}_cropped_{latitude_min}_{latitude_max}_{longitude_min}_{longitude_max}")

# Plot both datasets as subplots
plot_subplots(
    cropped_results["Bouguer"][0], cropped_results["Bouguer"][1], cropped_results["Bouguer"][2], f"Bouguer Anomaly ({survey_name})",
    cropped_results["Isostatic"][0], cropped_results["Isostatic"][1], cropped_results["Isostatic"][2], f"Isostatic Anomaly ({survey_name})"
)
