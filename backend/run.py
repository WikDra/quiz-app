"""
Plik uruchomieniowy aplikacji Flask dla Quiz-App
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Konfiguracja ścieżek
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Załaduj zmienne środowiskowe (np. SECRET_KEY, JWT_SECRET_KEY) PRZED importem aplikacji
# Szukaj pliku .env w głównym katalogu backend
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Załadowano zmienne środowiskowe z {dotenv_path}")
else:
    print("Nie znaleziono pliku .env. Użyj utils/setup_security.py, aby utworzyć bezpieczne klucze.")

# Importuj potrzebne moduły PO załadowaniu zmiennych środowiskowych
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

# Sprawdź bezpieczeństwo kluczy przy uruchomieniu
def check_security_keys():
    """Sprawdza czy używane są bezpieczne klucze kryptograficzne"""
    default_key1 = 'UNSAFE_DEV_KEY_PLEASE_RUN_SETUP_SECURITY'
    default_key2 = 'UNSAFE_DEV_JWT_KEY_PLEASE_RUN_SETUP_SECURITY'
    
    if (app.config.get('SECRET_KEY') == default_key1 or 
        app.config.get('JWT_SECRET_KEY') == default_key2):
        print("\n" + "!" * 80)
        print("!!! OSTRZEŻENIE: UŻYWASZ DOMYŚLNYCH KLUCZY BEZPIECZEŃSTWA !!!".center(80))
        print("!" * 80)
        print("\nTo zagraża bezpieczeństwu twojej aplikacji!")
        print("Uruchom następującą komendę, aby wygenerować bezpieczne klucze:")
        print("\npython backend/utils/setup_security.py\n")

# Uruchom aplikację
if __name__ == '__main__':
    check_security_keys()
    app.run(host='127.0.0.1', port=5000, debug=True)
