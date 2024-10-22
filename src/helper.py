import pandas as pd
import re
import json

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
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)  # Use indent for pretty printing
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")