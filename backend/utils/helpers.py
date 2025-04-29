"""
Pomocnicze funkcje dla aplikacji
"""
import json
import os
from pathlib import Path

def load_json_data(file_path):
    """Wczytuje dane z pliku JSON, obsługując komentarze na początku pliku"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Usuń komentarz z początku pliku jeśli istnieje
        if content.strip().startswith('//'):
            content = '\n'.join(content.splitlines()[1:])
            
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Błąd odczytu pliku {file_path}: {e}")
        return None
