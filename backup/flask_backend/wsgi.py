#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
print("Uruchamianie skryptu wsgi.py")

# Dodanie ścieżki projektu do PYTHONPATH
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))
print(f"Dodano ścieżkę do PYTHONPATH: {str(project_dir)}")

# Sprawdzamy dostępne moduły
print(f"Dostępne moduły w katalogu:")
for item in os.listdir(project_dir):
    print(f"  - {item}")

def main():
    """Funkcja startowa dla aplikacji Flask"""
    try:
        print("Próba importu create_app z pliku __init__.py...")
        # Bezpośredni import z modułu app
        from app import create_app
        
        # Tworzymy instancję aplikacji
        flask_app = create_app('development')
        
        # Uruchamiamy aplikację
        print("Uruchamianie serwera Flask na http://127.0.0.1:5000")
        flask_app.run(host='127.0.0.1', port=5000, debug=True)
        
    except ImportError as e:
        print(f"Błąd importowania modułów: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
