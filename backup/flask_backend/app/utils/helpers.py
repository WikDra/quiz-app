import json
import os
from datetime import datetime

def read_json_file(file_path):
    """
    Read and parse a JSON file
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Parsed JSON data or empty dict if error occurs
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        print(f"Error reading JSON file {file_path}: {str(e)}")
        return {}

def write_json_file(file_path, data):
    """
    Write data to a JSON file
    
    Args:
        file_path (str): Path to the JSON file
        data (dict): Data to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error writing to JSON file {file_path}: {str(e)}")
        return False

def format_datetime(dt):
    """
    Format a datetime object as a string
    
    Args:
        dt (datetime): Datetime object to format
        
    Returns:
        str: Formatted datetime string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    
    if isinstance(dt, datetime):
        return dt.isoformat()
    
    return None
