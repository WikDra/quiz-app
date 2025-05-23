# Quiz App Backend v2

Nowy backend z prostą obsługą ciasteczek i uporządkowaną strukturą.

## Główne funkcje

### 🔧 Architektura
- **Flask** z **Flask-Login** dla autentykacji przez ciasteczka
- **Flask-WTF** dla ochrony CSRF
- **SQLAlchemy** ORM dla bazy danych
- **Flask-CORS** z obsługą ciasteczek
- Modułowa struktura kontrolerów

### 🍪 Zarządzanie sesjami
- Bezpieczne ciasteczka HTTP-only
- Ochrona CSRF z tokenami
- Opcja "Zapamiętaj mnie" 
- Konfiguracja dla dev/prod

### 🚀 Funkcjonalności
- Rejestracja i logowanie użytkowników
- Tworzenie i rozwiązywanie quizów
- System Premium z integracją Stripe
- Statystyki użytkowników
- Rate limiting

## Instalacja

1. **Sklonuj repozytorium i przejdź do backend_v2:**
```bash
cd backend_v2
```

2. **Utwórz wirtualne środowisko:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

4. **Skonfiguruj środowisko:**
```bash
copy .env.example .env
# Edytuj .env i uzupełnij konfigurację
```

5. **Zainicjalizuj bazę danych:**
```bash
python app/utils/init_db.py
```

6. **Uruchom aplikację:**
```bash
python run.py
```

## Struktura projektu

```
backend_v2/
├── app/
│   ├── __init__.py          # Główna aplikacja Flask
│   ├── controllers/         # Kontrolery (endpointy API)
│   │   ├── auth_controller.py
│   │   ├── quiz_controller.py
│   │   ├── user_controller.py
│   │   └── stripe_controller.py
│   ├── models/             # Modele bazy danych
│   │   ├── user.py
│   │   └── quiz.py
│   ├── middleware/         # Middleware i dekoratory
│   │   ├── auth.py
│   │   └── rate_limiting.py
│   └── utils/              # Narzędzia pomocnicze
│       ├── helpers.py
│       └── init_db.py
├── config/
│   └── settings.py         # Konfiguracja aplikacji
├── requirements.txt
├── run.py                  # Punkt wejścia
└── .env.example           # Przykład konfiguracji
```

## API Endpointy

### Autentykacja (`/api/auth/`)
- `GET /csrf-token` - Pobierz token CSRF
- `POST /register` - Rejestracja użytkownika
- `POST /login` - Logowanie
- `POST /logout` - Wylogowanie
- `GET /me` - Dane aktualnego użytkownika
- `GET /check` - Sprawdź status autentykacji

### Quizy (`/api/quiz/`)
- `GET /` - Lista publicznych quizów
- `GET /<id>` - Szczegóły quizu
- `GET /my` - Quizy użytkownika
- `POST /create` - Utwórz quiz
- `POST /<id>/start` - Rozpocznij quiz
- `POST /attempt/<id>/submit` - Prześlij odpowiedzi
- `GET /attempts` - Historia prób

### Użytkownik (`/api/user/`)
- `GET /profile` - Profil użytkownika
- `PUT /profile` - Aktualizuj profil
- `POST /change-password` - Zmień hasło
- `GET /stats` - Statystyki użytkownika
- `DELETE /delete-account` - Usuń konto

### Stripe (`/api/stripe/`)
- `POST /create-checkout-session` - Sesja płatności
- `GET /verify-session/<id>` - Weryfikuj płatność
- `POST /webhook` - Webhook Stripe
- `POST /cancel-subscription` - Anuluj subskrypcję
- `GET /subscription-status` - Status subskrypcji

## Konfiguracja ciasteczek

### Development
```python
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
WTF_CSRF_ENABLED = True
```

### Production
```python
SESSION_COOKIE_SECURE = True  # Wymagane HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
WTF_CSRF_SSL_STRICT = True
```

## Bezpieczeństwo

- **CSRF Protection** - Wszystkie formularze chronione tokenami CSRF
- **Secure Cookies** - HttpOnly, Secure (prod), SameSite
- **Rate Limiting** - Ograniczenia na endpointy
- **Password Hashing** - Bcrypt dla haseł
- **Input Validation** - WTForms dla walidacji

## Testowanie

Przykładowe konta (po `init_db.py`):
- **Admin**: `admin@quiz-app.com` / `admin123`
- **User**: `test@example.com` / `test123`

## Migracje

Po zmianach w modelach:
```bash
flask db init        # Tylko pierwszy raz
flask db migrate -m "Opis zmian"
flask db upgrade
```

## Deployment

1. Ustaw `FLASK_ENV=production`
2. Skonfiguruj HTTPS
3. Ustaw `SESSION_COOKIE_SECURE=True`
4. Użyj bazy produkcyjnej (PostgreSQL)
5. Skonfiguruj rate limiting z Redis

## Główne różnice od v1

- ✅ **Prostsze ciasteczka** zamiast JWT
- ✅ **Flask-WTF CSRF** zamiast ręcznej implementacji  
- ✅ **Lepsza struktura** - kontrolery, middleware, utils
- ✅ **Flask-Login** dla zarządzania sesjami
- ✅ **Walidacja WTForms** dla wszystkich endpointów
- ✅ **Rate limiting** wbudowany
