"""
Database initialization script for Quiz App v2
"""
import os
import sys

# Add the backend_v2 directory to the Python path
backend_v2_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, backend_v2_dir)

from app import create_app, db
from app.models import User, Quiz, Question, Answer, QuizAttempt

def init_database():
    """Initialize the database with tables"""
    app = create_app('development')
    
    with app.app_context():
        print("Tworzenie tabel bazy danych...")
        
        # Drop all tables (be careful in production!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Tabele zostały utworzone pomyślnie!")
        
        # Create sample admin user
        create_sample_data()

def create_sample_data():
    """Create sample data for testing"""
    print("Tworzenie przykładowych danych...")
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@quiz-app.com',
        first_name='Admin',
        last_name='User',
        is_premium=True
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    # Create sample quiz
    quiz = Quiz(
        title='Przykładowy Quiz z Historii Polski',
        description='Test podstawowej wiedzy o historii Polski',
        creator_id=admin.id,
        is_public=True,
        time_limit=300  # 5 minutes
    )
    
    db.session.add(quiz)
    db.session.flush()  # Get quiz ID
    
    # Create sample questions
    questions_data = [
        {
            'text': 'W którym roku Polska odzyskała niepodległość?',
            'answers': [
                {'text': '1918', 'correct': True},
                {'text': '1919', 'correct': False},
                {'text': '1917', 'correct': False},
                {'text': '1920', 'correct': False}
            ]
        },
        {
            'text': 'Kto był pierwszym królem Polski?',
            'answers': [
                {'text': 'Bolesław Chrobry', 'correct': True},
                {'text': 'Mieszko I', 'correct': False},
                {'text': 'Kazimierz Wielki', 'correct': False},
                {'text': 'Władysław Jagiełło', 'correct': False}
            ]
        },
        {
            'text': 'W którym roku miała miejsce bitwa pod Grunwaldem?',
            'answers': [
                {'text': '1410', 'correct': True},
                {'text': '1411', 'correct': False},
                {'text': '1409', 'correct': False},
                {'text': '1412', 'correct': False}
            ]
        }
    ]
    
    for i, q_data in enumerate(questions_data):
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data['text'],
            question_type='multiple_choice',
            points=1,
            order_index=i
        )
        
        db.session.add(question)
        db.session.flush()  # Get question ID
        
        for j, a_data in enumerate(q_data['answers']):
            answer = Answer(
                question_id=question.id,
                answer_text=a_data['text'],
                is_correct=a_data['correct'],
                order_index=j
            )
            
            db.session.add(answer)
    
    # Create regular test user
    user = User(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    user.set_password('test123')
    
    db.session.add(user)
    db.session.commit()
    
    print("Przykładowe dane zostały utworzone!")
    print("Użytkownicy:")
    print("  - admin@quiz-app.com (hasło: admin123) - Administrator z Premium")
    print("  - test@example.com (hasło: test123) - Zwykły użytkownik")
    print("Quiz: 'Przykładowy Quiz z Historii Polski' - dostępny publicznie")

if __name__ == '__main__':
    init_database()
