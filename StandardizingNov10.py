import os
import pandas as pd
from git import Repo

# Paths for local data
raw_data_path = "/Users/maxfollett/Desktop/AirBorneInsight/CapDatabases/Raw/CEDAR_CITY/cedar_city_mag.xyz"
repo_dir = "/Users/maxfollett/AirBorneInsight2/AirBorneInsight2"
cleaned_data_dir = os.path.join(repo_dir, "CapDatabases/cleaned")
cleaned_data_path = os.path.join(cleaned_data_dir, "CedarCityCleaned.csv")

# Clone the repository if not already cloned
if not os.path.exists(repo_dir):
    Repo.clone_from("https://github.com/maxfollett/AirBorneInsight2.git", repo_dir)
    print(f"Repository cloned to {repo_dir}")
else:
    print(f"Repository already cloned at {repo_dir}")

# Ensure the cleaned data directory exists
os.makedirs(cleaned_data_dir, exist_ok=True)

# Load and process the data
print(f"Loading raw data from {raw_data_path}...")
df = pd.read_csv(raw_data_path, header=None, delim_whitespace=True)

# Check number of columns
print(f"Number of columns in data file: {len(df.columns)}")

# Define column names based on user specifications
column_names = [
    "col1", "col2", "col3", "col4", "col5", "Latitude(DD)", "Longitude(DD)", 
    "col8", "TotMagField", "col10", "col11", "col12", "CorrectedMag"
]
df.columns = column_names

# Select and save only relevant columns
cleaned_df = df[["Latitude(DD)", "Longitude(DD)", "TotMagField", "CorrectedMag"]]
cleaned_df.to_csv(cleaned_data_path, index=False)
print(f"Cleaned data saved to {cleaned_data_path}")

# Git operations to commit and push changes
repo = Repo(repo_dir)

# Pull latest changes from GitHub to avoid conflicts
try:
    origin = repo.remote(name="origin")
    origin.pull()
    print("Repository updated with latest changes from GitHub.")
except Exception as e:
    print(f"Error pulling from GitHub: {e}")

# Add, commit, and push the cleaned file
repo.git.add(cleaned_data_path)
repo.index.commit("Add CedarCityCleaned.csv to cleaned folder")

try:
    origin.push()
    print("Changes successfully pushed to GitHub.")
except Exception as e:
    print(f"Error pushing to GitHub: {e}")


