# Instrukcja konfiguracji OAuth dla Google w aplikacji Quiz

## 1. Stwórz projekt na Google Cloud Platform

1. Przejdź do [Google Cloud Console](https://console.developers.google.com/)
2. Kliknij "Select a project" -> "New Project"
3. Wprowadź nazwę projektu (np. "Quiz App") i kliknij "Create"
4. Odczekaj chwilę, aż projekt zostanie utworzony

## 2. Włącz Google Sign-In API

1. W menu po lewej stronie wybierz "APIs & Services" -> "Library"
2. Wyszukaj "Google Sign-In API" lub "Google+ API" i kliknij w wynik
3. Kliknij przycisk "Enable"

## 3. Skonfiguruj OAuth Consent Screen

1. Z menu po lewej wybierz "APIs & Services" -> "OAuth consent screen"
2. Wybierz "External" jako User Type i kliknij "Create"
3. Wypełnij wymagane pola:
   - App name: "Quiz App"
   - User support email: Twój adres email
   - Developer contact information: Twój adres email
4. Kliknij "Save and Continue"
5. W sekcji "Scopes" kliknij "Add or Remove Scopes" i wybierz następujące zakresy:
   - `userinfo.email`
   - `userinfo.profile`
   - `openid`
6. Kliknij "Save and Continue", a następnie "Back to Dashboard"

## 4. Utwórz dane uwierzytelniające OAuth

1. Z menu po lewej wybierz "APIs & Services" -> "Credentials"
2. Kliknij "Create Credentials" -> "OAuth client ID"
3. Jako typ aplikacji wybierz "Web application"
4. Wprowadź nazwę (np. "Quiz App Web Client")
5. W sekcji "Authorized JavaScript origins" dodaj:
   - `http://localhost:5173` (dla środowiska deweloperskiego)
6. W sekcji "Authorized redirect URIs" dodaj:
   - `http://localhost:5000/api/authorize/google` (dla backendu Flask)
7. Kliknij "Create"

## 5. Zapisz dane uwierzytelniające

Po utworzeniu klienta OAuth, otrzymasz Client ID i Client Secret. Skopiuj te wartości i umieść je w pliku `.env`:

```
GOOGLE_CLIENT_ID=twój_client_id
GOOGLE_CLIENT_SECRET=twój_client_secret
```

## 6. Uruchom aplikację

1. Uruchom backend Flask:
```
cd backend
python run.py
```

2. Uruchom frontend (w osobnym terminalu):
```
npm run dev
```

3. Otwórz aplikację w przeglądarce pod adresem `http://localhost:5173`
4. Przejdź do strony logowania i kliknij przycisk "Zaloguj się przez Google"

## Uwagi:

- W środowisku produkcyjnym należy dodać domenę produkcyjną do listy autoryzowanych pochodzeń i przekierowań.
- W przypadku problemów z konfiguracją, sprawdź logi aplikacji pod kątem błędów OAuth.
- Jeśli używasz wersji produkcyjnej, zweryfikuj swoją aplikację w Google Cloud Console, aby umożliwić logowanie wszystkim użytkownikom.
