from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os
import sys

print("Uruchamiam aplikację Flask...")
# Tworzę ścieżkę względną do katalogu głównego projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Import funkcji create_app z app_module i eksportuj ją jako część modułu app
from app.app_module import create_app

# Ustaw zmienną __all__, która określa co jest eksportowane z tego modułu
__all__ = ['create_app', 'db', 'migrate']
