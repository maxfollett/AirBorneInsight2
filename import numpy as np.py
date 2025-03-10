import numpy as np

# Function to read a txt file into a NumPy array and print dimensions
def read_txt_to_numpy(file_path):
    try:
        data = np.loadtxt(file_path)  # Load text file into a NumPy array
        print(f"Array Shape: {data.shape}")  # Print dimensions of the array
        return data
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

# Example usage
file_path = "test3_Bouguer_38.5_38.8_-113.5_-113.2.txt"  # Replace with your actual file path
array = read_txt_to_numpy(file_path)
