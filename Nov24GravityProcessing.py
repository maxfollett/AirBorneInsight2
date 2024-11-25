import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from io import StringIO

# Load XYZ file from GitHub repository
def load_xyz_from_github():
    # Correct URL to the raw data from the GitHub repository
    url = 'https://raw.githubusercontent.com/maxfollett/AirBorneInsight2/main/USbougerGravData.xyz'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        xyz_data = response.text
        cleaned_data = []
        
        # Split data into lines and process each line
        for line in xyz_data.splitlines():
            # Split by whitespace and remove empty parts
            columns = line.split()
            if len(columns) == 3:  # Only keep lines with exactly 3 columns
                cleaned_data.append(" ".join(columns))
            else:
                # Optional: Print the problematic line for debugging
                print(f"Skipping malformed line: {line}")
        
        # Join the cleaned data back into a single string
        cleaned_xyz_data = "\n".join(cleaned_data)
        
        # Now load the cleaned data into pandas
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

# Get user-defined latitude and longitude ranges
latitude_min, latitude_max = get_range_input("Enter the latitude range (min,max) (e.g., 40,42) : ")
longitude_min, longitude_max = get_range_input("Enter the longitude range (min,max) (e.g., -114,-112) : ")

# Get the name of the survey for the plot title
survey_name = input("Enter the name of the survey: ")

# Load the data from GitHub
data = load_xyz_from_github()

if data is None:
    print("Error loading data")
else:
    # Downsample by taking every 2nd row from the dataset (adjust as needed)
    data_sampled = data.iloc[::1]

    # Filter the data based on the user-defined ranges
    filtered_data = data_sampled[(data_sampled['x'] >= longitude_min) & (data_sampled['x'] <= longitude_max) & 
                                  (data_sampled['y'] >= latitude_min) & (data_sampled['y'] <= latitude_max)]

    # Check if filtered data is empty
    if filtered_data.empty:
        print("No data to display, check your filtering conditions.")
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
        plt.title(f'Gravity Anomaly Map for {survey_name}')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.colorbar(label='Gravity Value (milligal)')

        # Show the plot
        plt.show()
