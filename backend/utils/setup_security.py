#!/usr/bin/env python
"""
Skrypt pomocniczy do konfiguracji zabezpieczeń aplikacji Quiz App.
Ten skrypt:
1. Generuje bezpieczne klucze kryptograficzne dla aplikacji
2. Tworzy lub aktualizuje plik .env z tymi kluczami
3. Zachowuje istniejące zmienne środowiskowe
"""
import os
import sys
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu backend, aby zaimportować generate_keys
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from utils.generate_keys import generate_key

def print_header():
    """Drukuje nagłówek skryptu"""
    print("\n" + "=" * 80)
    print(" QUIZ APP - KONFIGURACJA ZABEZPIECZEŃ ".center(80, "="))
    print("=" * 80)
    print("\nTen skrypt pomoże Ci skonfigurować bezpieczne klucze dla aplikacji Quiz App.")
    print("Wygeneruje on nowe klucze kryptograficzne i zapisze je w pliku .env")
    print("\n")

def read_existing_env():
    """Odczytuje istniejący plik .env jeśli istnieje"""
    env_path = BACKEND_DIR / ".env"
    env_vars = {}
    
    if env_path.exists():
        print(f"Znaleziono istniejący plik .env w {env_path}")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        print(f"Wczytano {len(env_vars)} zmiennych środowiskowych")
    else:
        print(f"Nie znaleziono pliku .env w {env_path}")
        
    return env_vars

def update_env_file(env_vars):
    """Aktualizuje plik .env z nowymi kluczami bezpieczeństwa"""
    env_path = BACKEND_DIR / ".env"
    
    # Generuj nowe klucze
    print("\nGenerowanie nowych kluczy bezpieczeństwa...")
    env_vars["SECRET_KEY"] = generate_key()
    env_vars["JWT_SECRET_KEY"] = generate_key()
    
    # Zapisz plik .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# Plik konfiguracyjny dla Quiz App - wygenerowany automatycznie\n")
        f.write("# UWAGA: Ten plik zawiera poufne dane - nie umieszczaj go w repozytorium kodu!\n\n")
        
        # Zapisz klucze bezpieczeństwa na początku pliku
        f.write("# Klucze bezpieczeństwa\n")
        f.write(f"SECRET_KEY={env_vars['SECRET_KEY']}\n")
        f.write(f"JWT_SECRET_KEY={env_vars['JWT_SECRET_KEY']}\n\n")
        
        # Zapisz pozostałe zmienne
        f.write("# Pozostałe zmienne konfiguracyjne\n")
        for key, value in env_vars.items():
            if key not in ["SECRET_KEY", "JWT_SECRET_KEY"]:
                f.write(f"{key}={value}\n")
    
    print(f"✅ Zapisano zaktualizowany plik .env w {env_path}")

def check_google_oauth_config(env_vars):
    """Sprawdza konfigurację Google OAuth"""
    google_client_id = env_vars.get("GOOGLE_CLIENT_ID", "")
    google_client_secret = env_vars.get("GOOGLE_CLIENT_SECRET", "")
    
    if not google_client_id or google_client_id == "your_google_client_id_here" or \
       not google_client_secret or google_client_secret == "your_google_client_secret_here":
        print("\n⚠️ UWAGA: Konfiguracja Google OAuth jest niepełna lub niepoprawna.")
        print("Logowanie przez Google nie będzie działać bez poprawnych danych.")
        print("Instrukcje konfiguracji OAuth można znaleźć w pliku OAUTH_SETUP.md")
        
        setup_oauth = input("\nCzy chcesz skonfigurować Google OAuth teraz? (t/n): ")
        if setup_oauth.lower() == "t":
            print("\nAby skonfigurować OAuth Google:")
            print("1. Przejdź do https://console.cloud.google.com/")
            print("2. Utwórz nowy projekt lub wybierz istniejący")
            print("3. Przejdź do 'APIs & Services' > 'Credentials'")
            print("4. Kliknij 'Create Credentials' > 'OAuth client ID'")
            print("5. Ustaw typ aplikacji jako 'Web application'")
            print("6. Dodaj URL przekierowania: http://localhost:5000/api/auth/google/callback")
            print("7. Kliknij 'Create'")
            
            client_id = input("\nPodaj GOOGLE_CLIENT_ID: ")
            client_secret = input("Podaj GOOGLE_CLIENT_SECRET: ")
            
            if client_id and client_secret:
                env_vars["GOOGLE_CLIENT_ID"] = client_id
                env_vars["GOOGLE_CLIENT_SECRET"] = client_secret
                print("✅ Zapisano dane Google OAuth")
            else:
                print("❌ Nie podano wymaganych danych")

def main():
    """Główna funkcja skryptu"""
    print_header()
    
    # Odczytaj istniejący plik .env
    env_vars = read_existing_env()
    
    # Zapytaj użytkownika czy chce wygenerować nowe klucze
    generate_new = input("\nCzy chcesz wygenerować nowe klucze bezpieczeństwa? [t/N]: ")
    if generate_new.lower() == "t":
        update_env_file(env_vars)
        # Odczytaj zaktualizowany plik .env
        env_vars = read_existing_env()
    
    # Sprawdź konfigurację Google OAuth
    check_google_oauth_config(env_vars)
    
    print("\n✅ Konfiguracja zakończona!")
    print("\nAby uruchomić aplikację z nowymi ustawieniami, zrestartuj serwer.")

if __name__ == "__main__":
    main()
