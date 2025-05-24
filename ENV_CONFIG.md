# Environment Variables Configuration

## Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Sekretne klucze
SECRET_KEY=dev_secret_key_fallback
JWT_SECRET_KEY=dev_jwt_secret_key_fallback

# URL aplikacji
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:5000

# Porty i hosty
FRONTEND_PORT=5173
BACKEND_PORT=5000
BACKEND_HOST=127.0.0.1
FRONTEND_HOST=localhost

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Frontend Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:5000

# Stripe Configuration
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
VITE_STRIPE_PREMIUM_PLAN_ID=your_stripe_price_id
```

## Production Configuration

For production, change the URLs to your actual domains:

### Backend (.env):
```bash
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

### Frontend (.env):
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

## Local Development

The default configuration works for local development with:
- Frontend: http://localhost:5173
- Backend: http://localhost:5000
