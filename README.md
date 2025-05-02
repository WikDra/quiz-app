# Quiz App

Aplikacja do tworzenia i rozwiązywania quizów zbudowana z wykorzystaniem React.js (frontend) i Flask (backend). System umożliwia użytkownikom tworzenie własnych quizów, rozwiązywanie ich z liczeniem punktów i pomiarem czasu, oraz zarządzanie swoim profilem.

## Struktura projektu

```
quiz-app/
├── src/                  # Kod źródłowy frontendu (React.js)
│   ├── components/       # Komponenty współdzielone
│   ├── context/          # Konteksty Reacta (Auth, Quiz)
│   ├── pages/            # Komponenty stron
│   ├── styles/           # Pliki CSS
│   └── utils/            # Funkcje i stałe pomocnicze
├── public/               # Pliki statyczne
├── backend/              # Kod źródłowy backendu (Flask)
│   ├── models/           # Modele danych (SQLAlchemy)
│   ├── controllers/      # Kontrolery MVC
│   └── utils/            # Funkcje pomocnicze
```

## Technologie

### Frontend:
- React.js 18
- Vite (narzędzie buildowania)
- React Router dla nawigacji
- Context API do zarządzania stanem
- CSS z własnymi stylami

### Backend:
- Flask 2.3.2
- SQLAlchemy (ORM)
- SQLite (baza danych)
- Flask-Bcrypt (bezpieczne przechowywanie haseł)
- Flask-CORS (obsługa Cross-Origin Requests)

## Instalacja i uruchomienie

### Wymagania wstępne:
- Node.js (wersja 16+)
- Python (wersja 3.9+)

### Instalacja zależności:

```bash
# Zależności frontendu
npm install

# Zależności backendu
cd backend
pip install -r requirements.txt
```

### Uruchamianie aplikacji w trybie deweloperskim:

```bash
# Uruchamia zarówno frontend jak i backend
npm run dev

# Uruchomienie tylko backendu
cd backend
python run.py

# Uruchomienie tylko frontendu
npm run dev -- --host
```

### Budowanie aplikacji produkcyjnej:

```bash
npm run build
```

## Funkcje aplikacji

### Użytkownicy:
- Rejestracja i logowanie użytkowników
- Bezpieczne przechowywanie haseł (bcrypt)
- Profil użytkownika z awatarem (integracja z Gravatar)
- Zarządzanie ustawieniami konta

### Quizy:
- Przeglądanie dostępnych quizów
- Tworzenie własnych quizów z wieloma kategoriami
- Edycja i usuwanie własnych quizów
- Rozwiązywanie quizów z pomiarem czasu
- Dynamiczne liczenie punktów w zależności od czasu odpowiedzi

### System:
- Implementacja wzorca MVC
- RESTowe API
- Responsywny interfejs użytkownika
- Zarządzanie stanem aplikacji przez konteksty React

## Rozwój projektu

### Planowane funkcjonalności:
- Integracja z systemami social media do logowania
- Implementacja systemu płatności
- Rozbudowa statystyk użytkowników
- Wdrożenie testów jednostkowych i integracyjnych

## Autorzy

Projekt powstał w ramach projektu Backend development.
