import os

def process_txt_files(input_folder, output_folder):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Loop through all .txt files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".txt"):  # Process only .txt files
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"F{filename}")
            
            # Read the file and trim first and last rows
            with open(input_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                
                # Ensure there are enough lines to remove first and last
                if len(lines) > 2:
                    trimmed_lines = lines[1:-1]
                else:
                    trimmed_lines = []  # If only 1-2 lines, remove all
            
            # Write the processed content to a new file
            with open(output_path, "w", encoding="utf-8") as file:
                file.writelines(trimmed_lines)
            
            print(f"Processed: {filename} -> {output_path}")

# Define paths
input_folder = r"C:\Users\19mlf3\Desktop\landsat-txtfiles"
output_folder = r"C:\Users\19mlf3\Desktop\ProcessingDataFinal"

# Run the processing function
process_txt_files(input_folder, output_folder)
