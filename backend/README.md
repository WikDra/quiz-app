# Quiz App Backend v2

This is a rewritten version of the Quiz App backend with improved OAuth and CORS handling.

## Project Structure

```
backend/
├── app.py             # Main application file
├── run.py             # Runner script
├── .env               # Environment variables (contains secrets)
├── models/            # Database models
│   ├── __init__.py
│   ├── quiz.py
│   └── user.py
├── controllers/       # Business logic
│   ├── __init__.py
│   ├── oauth_controller.py
│   ├── quiz_controller.py
│   └── user_controller.py
└── utils/             # Utility functions
    ├── __init__.py
    ├── helpers.py
    └── setup_security.py
```

## Getting Started

1. Set up the environment:
   ```
   python utils/setup_security.py
   ```

2. Run the backend server:
   ```
   python run.py
   ```

3. Test the configuration:
   ```
   python test_setup.py
   ```

## Features

- User authentication (login/register)
- Google OAuth integration
- JWT token-based authentication with HttpOnly cookies
- Proper CORS configuration for cross-origin requests
- Quiz creation, listing, and solving

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `GET /api/login/google` - Login with Google
- `GET /api/authorize/google` - Google OAuth callback
- `POST /api/logout` - Logout user
- `POST /api/token/refresh` - Refresh access token

### Users
- `GET /api/users` - Get all users
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user data
- `PUT /api/users/<id>/change-password` - Change user password
- `PUT /api/users/<id>/avatar` - Update user avatar
- `GET /api/users/me/profile` - Get current user profile

### Quizzes
- `GET /api/quiz` - Get all quizzes (with optional filtering)
- `GET /api/quiz/<id>` - Get quiz by ID
- `POST /api/quiz` - Create new quiz
- `PUT /api/quiz/<id>` - Update quiz
- `DELETE /api/quiz/<id>` - Delete quiz

## Security Notes

- The application uses HttpOnly cookies for JWT tokens
- CORS is configured to allow cross-origin requests with credentials
- Cookies are set with SameSite=None to support cross-site requests
- In production, you should set JWT_COOKIE_SECURE=True and use HTTPS
