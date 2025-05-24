from flask import Flask, request, make_response, jsonify
import os
from flask_restful import Api
from flask_cors import CORS
from .extensions import db, oauth2  # Teraz importujemy db z extensions
from .quizes import QuizResource, OptionsQuizResource
from .routes import (
    RegisterResource, 
    LoginResource, 
    RefreshResource, 
    GoogleLoginCallback, 
    GoogleLoginRedirect, 
    GoogleProfile, 
    UserMeResource, 
    LogoutResource,
    UserResource
)
from .quizes import GetQuizzes
from .payments import StripeWebhook, CreatePaymentIntent
from flask_jwt_extended import JWTManager
import stripe

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
    
    # Add JWT error handlers for debugging
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        import logging
        logging.error("JWT token has expired")
        return jsonify({"error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        import logging
        logging.error(f"Invalid JWT token: {error}")
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        import logging
        logging.error(f"JWT token is missing: {error}")
        return jsonify({"error": "Token is missing"}), 401
    
    with app.app_context():
        db.create_all()

    # Enable CORS for all routes
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    allowed_origins = [frontend_url, "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"]
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    # Add explicit OPTIONS handler for CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            # Don't use wildcard with credentials - use specific origin
            origin = request.headers.get('Origin')
            
            if origin in allowed_origins:
                response.headers.add("Access-Control-Allow-Origin", origin)
                response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization")
                response.headers.add('Access-Control-Allow-Methods', "GET, POST, PUT, DELETE, OPTIONS")
                response.headers.add('Access-Control-Allow-Credentials', 'true')
            
            return response

    
    # Inicjalizacja API
    api = Api(app)

    # Endpointy

    # Uwierzytelnienie i rejestracja
    api.add_resource(RegisterResource, '/register')
    api.add_resource(LoginResource, '/login')
    api.add_resource(RefreshResource, '/refresh')
    api.add_resource(LogoutResource, '/logout')  # Zmienione z /auth/logout na /logout

    # Quizy
    api.add_resource(QuizResource, '/quiz')
    api.add_resource(GetQuizzes, '/quizzes')  # Dodany endpoint dla listy quizów
    api.add_resource(OptionsQuizResource, '/quiz/<int:quiz_id>')

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
    
    # Stripe subscription endpoints (compatible with frontend)
    from .stripe_controller import register_stripe_routes
    register_stripe_routes(app)



    return app