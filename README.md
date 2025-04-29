# Quiz App

Aplikacja do tworzenia i rozwiązywania quizów zbudowana na bazie React.js (frontend) i Flask (backend).

## Struktura projektu

```
quiz-app/
├── src/                  # Kod źródłowy frontendu (React.js)
├── public/               # Pliki statyczne i dane JSON
├── backend/              # Kod źródłowy backendu (Flask)
│   ├── models/           # Modele danych (SQLAlchemy)
│   ├── controllers/      # Logika biznesowa
│   ├── utils/            # Funkcje pomocnicze
├── backup/               # Kopia zapasowa starego kodu
```

## Technologie

- Frontend: React.js, Vite, CSS
- Backend: Flask, SQLAlchemy, SQLite
- Narzędzia: ESLint, Flask-Migrate, Flask-CORS

## Uruchamianie aplikacji

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
npm run server

# Uruchomienie tylko frontendu
npm run frontend
```

### Budowanie aplikacji produkcyjnej:

```bash
npm run build
```

## Funkcje aplikacji

- Rejestracja i logowanie użytkowników
- Przeglądanie dostępnych quizów
- Tworzenie własnych quizów
- Rozwiązywanie quizów z pomiarem czasu
- Zapisywanie wyników i statystyk użytkowników
