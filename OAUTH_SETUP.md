# 🔐 OAuth Google Setup Guide (PEŁNA IMPLEMENTACJA)

Ten przewodnik opisuje konfigurację Google OAuth dla Quiz App, która **została już zaimplementowana** z zaawansowanymi funkcjami bezpieczeństwa.

## ✅ **ZAIMPLEMENTOWANE FUNKCJE OAUTH**

### **🚀 Core OAuth Features:**
- ✅ **Google Sign-In:** Bezpieczna autentykacja społecznościowa
- ✅ **Profile Sync:** Automatyczne tworzenie i aktualizacja profili
- ✅ **Mixed Authentication:** Wsparcie dla email/password + OAuth users
- ✅ **Token Management:** JWT z refresh tokens dla OAuth users
- ✅ **Stable Flow:** Naprawione "losowe działanie" OAuth

### **🔧 Advanced Features:**
- ✅ **Security:** HttpOnly cookies, CORS protection
- ✅ **User Mapping:** Smart handling Google ID vs regular user ID
- ✅ **Error Handling:** Comprehensive error scenarios
- ✅ **Admin Support:** OAuth users w admin panelu

---

## 🚀 **Setup Steps**

### **1. Utwórz projekt na Google Cloud Platform**

1. Przejdź do [Google Cloud Console](https://console.developers.google.com/)
2. **Select a project** → **New Project**
3. **Nazwa:** "Quiz App" → **Create**
4. Odczekaj na utworzenie projektu

### **2. Włącz Google APIs**

1. **APIs & Services** → **Library**
2. Wyszukaj i włącz:
   - **Google Sign-In API**
   - **Google+ API** (legacy, ale czasem potrzebne)
3. Kliknij **Enable** dla każdego

### **3. Skonfiguruj OAuth Consent Screen**

1. **APIs & Services** → **OAuth consent screen**
2. **User Type:** External → **Create**
3. **Wypełnij dane:**
   - **App name:** "Quiz App"
   - **User support email:** twój-email@domain.com
   - **Developer contact:** twój-email@domain.com
4. **Scopes:** Dodaj zakresy:
   - `userinfo.email`
   - `userinfo.profile` 
   - `openid`
5. **Save and Continue**

### **4. Utwórz OAuth Client**

1. **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth client ID**
3. **Application type:** Web application
4. **Name:** "Quiz App Web Client"
5. **Authorized JavaScript origins:**
   ```
   http://localhost:5173
   http://localhost:5174
   ```
6. **Authorized redirect URIs:**
   ```
   http://localhost:5000/auth/oauth2/callback
   ```
7. **Create** → Skopiuj **Client ID** i **Client Secret**

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
