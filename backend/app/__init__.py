from flask import Flask
import os
from flask_restful import Api
from .extensions import db, oauth2  # Teraz importujemy db z extensions
from .quizes import QuizResource
from .routes import (
    RegisterResource, 
    LoginResource, 
    RefreshResource, 
    GoogleLoginCallback, 
    GoogleLoginRedirect, 
    GoogleProfile, 
    UserMeResource, 
    LogoutResource,
    CookieTest,
    UserResource
)
from .quizes import GetQuizzes
from .payments import StripeWebhook, CreatePaymentIntent, create_payment
from flask_jwt_extended import JWTManager
import stripe
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Wczytanie konfiguracji
    app.config.from_object('config.Config')
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    stripe.api_key=os.getenv("STRIPE_SECRET_KEY")
    # Inicjalizacja bazy danych
    db.init_app(app)
    oauth2.init_app(app)
    # Inicjalizacja JWT
    jwt = JWTManager(app)
    with app.app_context():
        db.create_all()

    # Enable CORS for all routes
    CORS(app, supports_credentials=True)
    
    # Inicjalizacja API
    api = Api(app)

    # Endpointy

    # Uwierzytelnienie i rejestracja
    api.add_resource(RegisterResource, '/auth/register')
    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(RefreshResource, '/refresh')
    api.add_resource(LogoutResource, '/auth/logout')

    # Quizy
    api.add_resource(QuizResource, '/quiz')

    # Google OAuth2
    api.add_resource(GoogleLoginCallback, '/auth/oauth2/callback')
    api.add_resource(GoogleLoginRedirect, '/auth/oauth2/redirect')
    api.add_resource(GoogleProfile, '/profile')

    # Użytkownik
    api.add_resource(UserResource, '/users')
    api.add_resource(UserMeResource, '/users/me')

    # Płatności
    api.add_resource(CreatePaymentIntent, '/payments/create')
    api.add_resource(StripeWebhook, '/payments/webhook')
    api.add_resource(create_payment, '/payments/create-payment')

    # Testowe
    api.add_resource(CookieTest, '/test-cookies')

    return app