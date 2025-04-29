import os
import sys
import traceback
from pathlib import Path

# Dodanie ścieżki katalogu nadrzędnego do sys.path, aby moduł app był dostępny
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

try:
    from app import create_app
    print("Moduł app został pomyślnie zaimportowany")
except Exception as e:
    print(f"Błąd podczas importowania modułu app: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    # Get environment configuration from environment variable or default to development
    env = os.environ.get('FLASK_ENV', 'development')
    print(f"Używana konfiguracja: {env}")
    app = create_app(env)
    print("Aplikacja Flask została utworzona pomyślnie")
except Exception as e:
    print(f"Błąd podczas tworzenia aplikacji Flask: {e}")
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
