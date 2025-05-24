# Quiz App

**Akademicka aplikacja quiz-app** zbudowana zgodnie z wzorcem MVC z wykorzystaniem Python Flask (backend) i React.js (frontend). System umożliwia użytkownikom tworzenie quizów, rozwiązywanie ich z systemem punktacji, oraz zarządzanie płatnościami premium.

## ✅ Funkcjonalności (ZREALIZOWANE)

### 🎯 **Wymagania Podstawowe:**
- ✅ **Język inny niż JavaScript:** Python Flask (backend)
- ✅ **Wzorzec MVC:** Modele (SQLAlchemy), Kontrolery, Widoki (Flask-RESTful)
- ✅ **Social Media Login:** Google OAuth 2.0
- ✅ **Płatności elektroniczne:** Stripe (webhooks, subscriptions)
- ✅ **Offline payment approval:** Panel admin z zatwierdzaniem płatności
- ✅ **Scenariusze negatywne:** Failed payments, retry logic, admin notifications

### 🚀 **Funkcjonalności Dodatkowe:**
- ✅ Tworzenie i edycja quizów (regularne i OAuth użytkownikóW)
- ✅ Rozwiązywanie quizów z pomiarem czasu i punktacją
- ✅ System autentykacji JWT z refresh tokens i blacklisting
- ✅ Panel administratora (zarządzanie użytkownikami, płatnościami)
- ✅ Failed payments tracking i automatyczna dezaktywacja premium
- ✅ Responsive UI z nowoczesnym designem
- ✅ CORS i security headers konfiguracja

## 🔧 Integracja z Stripe (PEŁNA IMPLEMENTACJA)

Aplikacja implementuje **kompletną obsługę płatności** z zaawansowanymi scenariuszami:

### ✅ **Zrealizowane funkcje Stripe:**
- ✅ **Checkout Sessions:** Tworzenie sesji płatności
- ✅ **Webhooks:** `customer.subscription.created/updated/deleted`
- ✅ **Failed Payments:** `invoice.payment_failed`, `payment_intent.payment_failed`
- ✅ **Retry Logic:** 3 próby z automatyczną dezaktywacją
- ✅ **Admin Dashboard:** Monitoring failed payments i offline approvals
- ✅ **Database Tracking:** `failed_payment_count` w modelu `StripeSubscription`

### 📖 **Dokumentacja:**
- [Kompletna instrukcja konfiguracji Stripe](STRIPE_SETUP.md)
- [Szczegóły implementacji i aktualizacji](STRIPE_UPDATES.md)

### ⚙️ **Konfiguracja:**
1. Utwórz konto na [stripe.com](https://stripe.com)
2. Ustaw klucze API w pliku `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
3. Zweryfikuj konfigurację: `python -m backend.utils.setup_security`
4. Skonfiguruj webhooks na endpoint: `/stripe/webhook`

## 🏗️ Struktura projektu (Wzorzec MVC)

```
quiz-app/
├── frontend/                # React.js Application
│   ├── src/
│   │   ├── components/      # Reusable UI Components
│   │   ├── context/         # React Contexts (Auth, Quiz)
│   │   ├── pages/           # Page Components (Views)
│   │   ├── styles/          # CSS Styling
│   │   └── utils/           # Frontend Utilities
│   └── public/              # Static Assets
│
├── backend/                 # Flask MVC Backend
│   ├── app/
│   │   ├── models.py        # 📊 MODELS - SQLAlchemy ORM
│   │   ├── quiz_controller.py    # 🎮 CONTROLLERS - Business Logic
│   │   ├── user_controller.py    # 👤 CONTROLLERS - User Management
│   │   ├── admin_controller.py   # 👑 CONTROLLERS - Admin Functions
│   │   ├── routes.py        # 🌐 VIEWS - Flask-RESTful Routes
│   │   ├── quizes.py        # 🧩 VIEWS - Quiz Resources
│   │   └── stripe_resources.py  # 💳 VIEWS - Payment Resources
│   │
│   ├── utils/               # Backend Utilities
│   │   ├── helpers.py       # Sanitization, Validation
│   │   ├── setup_security.py    # Security Configuration
│   │   └── scheduled_tasks.py   # Background Tasks
│   │
│   ├── tests/               # Test Suite (NEEDS IMPLEMENTATION)
│   │   ├── conftest.py      # ❌ TODO: Test Configuration
│   │   ├── test_models.py   # ❌ TODO: Model Tests
│   │   ├── test_controllers.py  # ❌ TODO: Controller Tests
│   │   └── test_api.py      # ❌ TODO: API Integration Tests
│   │
│   └── config.py            # Flask Configuration
└── requirements.txt         # Python Dependencies
```
## 🚀 **STAN IMPLEMENTACJI**

### ✅ **KOMPLETNIE ZREALIZOWANE:**
- **MVC Architecture:** Modele, Kontrolery, Widoki oddzielone
- **Google OAuth:** Pełna integracja z smooth UX
- **Stripe Payments:** Checkout, webhooks, failed payments handling
- **Admin Panel:** User management, offline payment approvals, failed payments monitoring
- **Quiz System:** Create, edit, solve quizzes with scoring
- **JWT Security:** Refresh tokens, blacklisting, automatic renewal
- **Database Models:** User, Quiz, Question, Answer, StripeSubscription, OfflinePayment
- **Error Handling:** Comprehensive error scenarios and validation

### ❌ **NADAL WYMAGANE (KRYTYCZNE):**
- **🧪 TESTY:** Unit tests, integration tests, 50%+ coverage
- **📊 Advanced Analytics:** Quiz statistics, user progress tracking
- **🔍 Search & Filtering:** Advanced quiz discovery

---

## 💻 Technologie

### **Backend (Python):**
- **Flask:** Web framework z Flask-RESTful
- **SQLAlchemy:** ORM z relacyjnymi modelami
- **JWT Extended:** Token management z refresh logic
- **Stripe Python:** Payment processing
- **APScheduler:** Background tasks (token cleanup)

### **Frontend (React.js):**
- **Vite:** Fast build tool
- **Context API:** State management (Auth, Quiz)
- **React Router:** SPA navigation
- **Modern CSS:** Responsive design
- **Stripe.js:** Payment UI integration

---

## 🔐 System Autentykacji (ADVANCED)

### **JWT Token Management:**
- ✅ **HttpOnly Cookies:** Secure token storage
- ✅ **Auto-refresh:** Background token renewal
- ✅ **Token Blacklisting:** Logout security
- ✅ **Rotation System:** Enhanced security for refresh tokens
- ✅ **CORS Security:** Proper same-site policies

### **OAuth Integration:**
- ✅ **Google Sign-In:** Seamless social authentication
- ✅ **Profile Sync:** Auto user creation and updates
- ✅ **Mixed Auth:** Support for both email/password and OAuth users

**📖 Szczegółowa dokumentacja:** [OAUTH_SETUP.md](OAUTH_SETUP.md)

---

## 🚀 Uruchomienie projektu

### **Krok 1: Environment Setup**
```bash
# Skopiuj i skonfiguruj zmienne środowiskowe
cp .env.example .env
# Edytuj .env z właściwymi kluczami API
```

### **Krok 2: Instalacja**
```bash
# Root directory - instaluje frontend i backend
npm install

# Backend dependencies
cd backend
pip install -r requirements.txt
```

### **Krok 3: Database Setup**
```bash
# Utwórz bazę danych (SQLite)
cd backend
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### **Krok 4: Uruchomienie**
```bash
# Development mode (concurrently runs frontend + backend)
npm run dev

# Alternatywnie, oddzielnie:
# Backend: cd backend && python run.py
# Frontend: npm run frontend
```

---

## 🧪 **TESTING (TODO - KRYTYCZNE)**

```bash
# Unit tests
pytest backend/tests/test_models.py -v

# Integration tests  
pytest backend/tests/test_api.py -v

# Coverage report
pytest --cov=backend/app --cov-report=html

# Target: 50%+ coverage requirement
```

---

## 🚨 **STATUS PROJEKTU**

### ✅ **KOMPLETNIE ZREALIZOWANE:**
- ✅ OAuth działa stabilnie (naprawione wielokrotne refreshy)
- ✅ Quiz endpoints działają poprawnie (naprawiony routing)
- ✅ Email update w admin panelu (naprawiona serializacja)  
- ✅ Failed payments monitoring i retry logic
- ✅ Stripe webhooks z comprehensive error handling
- ✅ Admin dashboard z pełną funkcjonalnością
- ✅ Wzorzec MVC z separacją Models/Controllers/Views
- ✅ Security best practices (JWT, CORS, HttpOnly cookies)

### ❌ **KRYTYCZNE BRAKI:**
- **🧪 TESTY:** Bez testów projekt nie spełnia wymagań akademickich  
- **📊 Coverage:** Minimum 50% wymagane

---

## 🔧 **Environment Variables**

```env
# Database
DATABASE_URL=sqlite:///instance/baza.db

# JWT Security
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ACCESS_TOKEN_EXPIRES=5400  # 90 minutes
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe (Development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

**📖 Więcej szczegółów:** [ENV_CONFIG.md](ENV_CONFIG.md)

---

**🎯 NASTĘPNY KROK:** Implementacja testów jednostkowych i integracyjnych dla spełnienia wymagania 50%+ coverage.
