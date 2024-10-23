import pandas as pd
import re
import os
import json
import csv

def get_repo_names_from_file(filename):
    df = pd.read_excel(filename, sheet_name='Result 1')
    return df['repo_full_name'].tolist()

def get_hunk_start_line(hunk_header):
    match = re.match(r'@@ -\d+,\d+ \+(\d+),\d+ @@', hunk_header)
    if match:
        return int(match.group(1))  # Returns the starting line in the "new" version of the file
    return None

def extract_hunks(patch):
    hunks = []
    # Regular expression to capture the hunk header and content
    pattern = re.compile(r'(@@ -\d+,\d+ \+\d+,\d+ @@)(.*?)\n(?=(@@|\Z))', re.DOTALL)
    matches = pattern.findall(patch)
    for match in matches:
        header = match[0]
        content = match[1].strip()
        hunks.append((header, content))
    return hunks

def write_json_to_file(data, file_path):
    """
    Writes a list of dictionaries to a file in JSON format.

    Parameters:
    data (list): A list of dictionaries to write to the file.
    file_path (str): The path of the file where the JSON should be saved.
    """
    # Get the directory name from the file path
    directory = os.path.dirname(file_path)
    
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    try:
        # Write JSON data to the specified file
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        raise


def write_dicts_to_csv(data, file_path):
    """
    Writes a list of dictionaries to a CSV file.

    Parameters:
    data (list): A list of dictionaries to write to the file.
    file_path (str): The path of the CSV file where the data should be saved.
    """
    if not data:
        print("No data to write.")
        return

    headers = data[0].keys()

    # Get the directory name from the file path
    directory = os.path.dirname(file_path)
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    try:
        with open(file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)            
            writer.writeheader()
            writer.writerows(data)

        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")