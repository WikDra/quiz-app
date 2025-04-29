"""
Prosty skrypt do inicjalizacji bazy danych SQLite i utworzenia tabel
"""
import os
import sys
from pathlib import Path

# Dodanie ścieżki projektu do zmiennych środowiskowych Pythona
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Bezpośredni import aplikacji Flask
from app.app_module import create_app
from app import db

def init_db():
    print("Inicjalizacja bazy danych SQLite...")
    
    try:
        # Tworzenie i konfiguracja instancji Flask
        app = create_app('development')
        
        # Tworzenie tabel w bazie danych
        with app.app_context():
            print("Tworzenie tabel w bazie danych...")
            db.create_all()
            print("Baza danych została zainicjalizowana pomyślnie!")
            
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    init_db()
