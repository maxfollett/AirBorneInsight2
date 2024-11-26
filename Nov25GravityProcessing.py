import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from io import StringIO

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

# Function to plot data
def plot_data(filtered_data, survey_name, title):
    if filtered_data.empty:
        print(f"No data to display for {title}, check your filtering conditions.")
    else:
        # Normalize the value column for circle size (adjust size range)
        min_value = filtered_data['value'].min()
        max_value = filtered_data['value'].max()
        size_scaled = 100 * (filtered_data['value'] - min_value) / (max_value - min_value)  # Scale values for circle size

        # Plotting the circles on the grid
        plt.figure(figsize=(12, 10))  # Increase figure size for better visibility

        # Scatter plot where each point is a circle
        plt.scatter(filtered_data['x'], filtered_data['y'], s=size_scaled, c=filtered_data['value'], cmap='viridis', alpha=0.6, edgecolors='w', linewidth=0.5)

        # Set axis labels
        plt.title(title)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.colorbar(label='Gravity Value (milligal)')

        # Show the plot
        plt.show()

# GitHub raw URLs
url1 = "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/USbougerGravData.xyz"
url2 = "https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/isograv.xyz"

# Get user-defined latitude and longitude ranges
latitude_min, latitude_max = get_range_input("Enter the latitude range (min,max) (e.g., 40,42) for both plots: ")
longitude_min, longitude_max = get_range_input("Enter the longitude range (min,max) (e.g., -114,-112) for both plots: ")

# Get survey name
survey_name1 = input("Enter the name of the survey: ")

# Load and plot the first dataset
data1 = load_xyz_from_github(url1)
if data1 is not None:
    data_sampled1 = data1.iloc[::1]  # Downsample if necessary
    filtered_data1 = data_sampled1[(data_sampled1['x'] >= longitude_min) & (data_sampled1['x'] <= longitude_max) &
                                   (data_sampled1['y'] >= latitude_min) & (data_sampled1['y'] <= latitude_max)]
    plot_data(filtered_data1, survey_name1, f"Gravity: Bouguer Anomaly Map for {survey_name1}")

# Load and plot the second dataset
data2 = load_xyz_from_github(url2)
if data2 is not None:
    data_sampled2 = data2.iloc[::1]  # Downsample if necessary
    filtered_data2 = data_sampled2[(data_sampled2['x'] >= longitude_min) & (data_sampled2['x'] <= longitude_max) &
                                   (data_sampled2['y'] >= latitude_min) & (data_sampled2['y'] <= latitude_max)]
    plot_data(filtered_data2, survey_name1, f"Gravity: Isostatic Anomaly Map for {survey_name1}")
