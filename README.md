# Quiz App

Aplikacja do tworzenia i rozwiązywania quizów zbudowana z wykorzystaniem React.js (frontend) i Flask (backend). System umożliwia użytkownikom tworzenie własnych quizów, rozwiązywanie ich z liczeniem punktów i pomiarem czasu, oraz zarządzanie swoim profilem.

## Funkcjonalności

- Tworzenie i edycja quizów
- Rozwiązywanie quizów z pomiarem czasu
- System autentykacji (JWT) z logowaniem przez email lub Google OAuth
- Zarządzanie profilem użytkownika
- Śledzenie postępów i statystyk

## Struktura projektu

```
quiz-app/
├── src/                  # Kod źródłowy frontendu (React.js)
│   ├── components/       # Komponenty współdzielone
│   ├── context/         # Konteksty Reacta (Auth, Quiz)
│   ├── pages/           # Komponenty stron
│   ├── styles/          # Pliki CSS
│   └── utils/           # Funkcje i stałe pomocnicze
├── public/              # Pliki statyczne
├── backend/          # Kod źródłowy backendu (Flask)
│   ├── models/          # Modele danych (SQLAlchemy)
│   │   ├── quiz.py     # Model quizu
│   │   └── user.py     # Model użytkownika
│   ├── controllers/     # Kontrolery MVC
│   │   ├── oauth_controller.py    # Logika OAuth
│   │   ├── quiz_controller.py     # Logika quizów
│   │   └── user_controller.py     # Logika użytkowników
│   ├── utils/          # Funkcje pomocnicze
│   │   ├── helpers.py          # Funkcje pomocnicze
│   │   ├── init_db.py         # Inicjalizacja bazy danych
│   │   ├── setup_security.py  # Konfiguracja bezpieczeństwa
│   │   └── token_utils.py     # Zarządzanie JWT
│   ├── routes.py      # Routing API
│   └── app.py         # Główna aplikacja Flask
```

## Technologie

- Frontend:
  - React.js
  - Vite
  - Context API do zarządzania stanem
  - React Router do nawigacji

- Backend:
  - Flask (Python)
  - SQLAlchemy ORM
  - JWT do autentykacji
  - OAuth 2.0 (Google Sign-In)

## System Autentykacji

### JWT Token Management

- Automatyczne odświeżanie tokenów przed wygaśnięciem
- System rotacji tokenów refresh dla zwiększenia bezpieczeństwa
- Bezpieczne przechowywanie tokenów w HttpOnly cookies
- Obsługa CORS z odpowiednimi nagłówkami bezpieczeństwa

### OAuth Integration

Szczegółowe instrukcje konfiguracji OAuth znajdują się w pliku [OAUTH_SETUP.md](OAUTH_SETUP.md).

## Uruchomienie projektu

1. Instalacja zależności:
```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

2. Konfiguracja:
- Skopiuj `.env.example` do `.env` i uzupełnij zmienne środowiskowe
- Skonfiguruj OAuth zgodnie z instrukcją w OAUTH_SETUP.md

3. Uruchomienie:
```bash
# Development
npm run dev  # uruchamia zarówno frontend jak i backend

# Produkcja
npm run build
npm run preview
```

## Bezpieczeństwo

- Wszystkie tokeny JWT są przechowywane w bezpiecznych HttpOnly cookies
- Implementacja CSRF protection
- Sanityzacja danych wejściowych
- Bezpieczne hasła z użyciem bcrypt
- Rotacja tokenów refresh dla lepszego bezpieczeństwa
- Rate limiting dla endpointów logowania
- Walidacja CORS z precyzyjną konfiguracją

## Rozwój projektu

Aby rozpocząć pracę nad projektem:
1. Sklonuj repozytorium
2. Zainstaluj zależności
3. Skonfiguruj środowisko według instrukcji powyżej
4. Uruchom testy przed wprowadzeniem zmian
