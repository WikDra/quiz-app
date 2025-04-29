"""
Inicjalizuje bazę danych SQLite i tworzy tabele.
"""
import os
import sys
from pathlib import Path

# Dodanie ścieżki projektu do PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def init_db():
    """Inicjalizuje bazę danych i tworzy wszystkie tabele."""
    try:
        print("Inicjalizacja bazy danych SQLite...")
        
        # Import aplikacji Flask i modeli
        from app import create_app, db
        from app.models.user import User
        from app.models.quiz import Quiz
        
        # Utworzenie aplikacji Flask z kontekstem
        app = create_app('development')
        
        # Utworzenie tabel w bazie danych
        with app.app_context():
            db.create_all()
            print("Tabele zostały utworzone pomyślnie!")
        
        return True
    except Exception as e:
        print(f"Wystąpił błąd podczas inicjalizacji bazy danych: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_db()
