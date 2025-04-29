"""
Plik uruchomieniowy aplikacji Flask dla Quiz-App
"""
import os
import sys
from pathlib import Path

# Konfiguracja ścieżek
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Importuj potrzebne moduły
from __init__ import create_app, db

# Inicjalizuj aplikację
app = create_app()

# Zarejestruj modele w kontekście aplikacji
with app.app_context():
    # Sprawdź czy baza danych istnieje, jeśli nie - utwórz tabele
    db_path = os.path.join(os.path.dirname(__file__), 'quiz_app.db')
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print("Inicjalizacja bazy danych...")
        db.create_all()
        
    # Importowanie modeli
    from models import user, quiz

# Uruchom aplikację
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
