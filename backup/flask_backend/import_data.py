"""
Skrypt do importowania danych z plików JSON do bazy danych SQLite.
"""
import sys
import json
import os
from pathlib import Path

# Dodaj katalog główny projektu do ścieżki Pythona
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import naszej uproszczonej aplikacji z instancją db
from simplified_app import app, db, User, Quiz

# Ścieżki do plików JSON
PROJECT_ROOT = BASE_DIR.parent
QUIZ_JSON_PATH = PROJECT_ROOT / 'public' / 'quiz.json'
USERS_JSON_PATH = PROJECT_ROOT / 'public' / 'users.json'

def load_json_data(file_path):
    """Wczytuje dane z pliku JSON, obsługując komentarze na początku pliku"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Usuń komentarz z początku pliku jeśli istnieje
        if content.strip().startswith('//'):
            content = '\n'.join(content.splitlines()[1:])
            
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Błąd odczytu pliku {file_path}: {e}")
        return None

def import_users():
    """Importuje użytkowników z pliku JSON do bazy danych"""
    print(f"Importowanie użytkowników z {USERS_JSON_PATH}...")
    
    try:
        data = load_json_data(USERS_JSON_PATH)
        if not data or 'users' not in data:
            print("Brak danych użytkowników do importu lub nieprawidłowy format.")
            return 0
        
        users_data = data['users']
        print(f"Znaleziono {len(users_data)} użytkowników w pliku JSON.")
        
        count = 0
        for user_data in users_data:
            if not isinstance(user_data, dict):
                print(f"Nieprawidłowy format danych użytkownika: {user_data}")
                continue
                
            # Sprawdź czy użytkownik już istnieje
            username = user_data.get('fullName') or user_data.get('username')
            email = user_data.get('email')
            
            if not username:
                print(f"Brak nazwy użytkownika w danych: {user_data}")
                continue
                
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Użytkownik {username} już istnieje. Pomijam.")
                continue
    except Exception as e:
        print(f"Błąd podczas importowania użytkowników: {e}")
        import traceback
        traceback.print_exc()
        return 0
          # Tworzenie nowego użytkownika
        new_user = User(
            username=username or f"user_{count}",
            email=email or f"user{count}@example.com",
            password_hash=user_data.get('password'),  # W rzeczywistej aplikacji należałoby zahashować hasło
            is_admin=username == "Administrator"      # Administrator jest domyślnym adminem
        )
        db.session.add(new_user)
        print(f"Dodano użytkownika: {new_user.username}")
        count += 1
    
    if count > 0:
        db.session.commit()
        print(f"Zaimportowano {count} użytkowników.")
    
    return count

def import_quizzes():
    """Importuje quizy z pliku JSON do bazy danych"""
    print(f"Importowanie quizów z {QUIZ_JSON_PATH}...")
    
    quiz_data = load_json_data(QUIZ_JSON_PATH)
    if not quiz_data or 'quizzes' not in quiz_data:
        print("Brak danych quizów do importu.")
        return 0
    
    count = 0
    for quiz in quiz_data['quizzes']:
        # Sprawdź czy quiz już istnieje
        existing_quiz = Quiz.query.filter_by(title=quiz.get('title')).first()
        if existing_quiz:
            print(f"Quiz '{quiz.get('title')}' już istnieje. Pomijam.")
            continue
        
        # Znajdź użytkownika jeśli istnieje
        user_id = None
        if 'author' in quiz:
            user = User.query.filter_by(username=quiz['author']).first()
            if user:
                user_id = user.id
        
        # Utwórz nowy quiz
        new_quiz = Quiz(
            title=quiz.get('title'),
            description=quiz.get('description'),
            category=quiz.get('category'),
            difficulty=quiz.get('difficulty'),
            user_id=user_id
        )
        
        # Ustaw pytania
        new_quiz.questions = quiz.get('questions', [])
        
        db.session.add(new_quiz)
        count += 1
    
    if count > 0:
        db.session.commit()
        print(f"Zaimportowano {count} quizów.")
    
    return count

def main():
    """Główna funkcja migracji danych"""
    print("Rozpoczynanie migracji danych z JSON do SQLite...")
    print(f"Ścieżka do pliku quizów: {QUIZ_JSON_PATH}")
    print(f"Ścieżka do pliku użytkowników: {USERS_JSON_PATH}")
    
    # Sprawdź czy pliki istnieją
    if not QUIZ_JSON_PATH.exists():
        print(f"BŁĄD: Plik {QUIZ_JSON_PATH} nie istnieje!")
    else:
        print(f"Plik quizów znaleziony: {QUIZ_JSON_PATH}")
        
    if not USERS_JSON_PATH.exists():
        print(f"BŁĄD: Plik {USERS_JSON_PATH} nie istnieje!")
    else:
        print(f"Plik użytkowników znaleziony: {USERS_JSON_PATH}")
    
    # Zamiast używać with app.app_context(), tworzymy nowy kontekst i jawnie go aktywujemy
    try:
        print("Tworzenie kontekstu aplikacji...")
        app.app_context().push()
        
        # Najpierw importuj użytkowników
        user_count = import_users()
        
        # Następnie importuj quizy
        quiz_count = import_quizzes()
        
        print(f"Migracja zakończona. Zaimportowano {user_count} użytkowników i {quiz_count} quizów.")
    except Exception as e:
        print(f"Błąd podczas migracji danych: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
