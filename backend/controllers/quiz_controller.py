"""
Kontroler do operacji na quizach
"""
import sys
import os
from flask import current_app
from pathlib import Path

# Konfiguracja ścieżek
module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if module_path not in sys.path:
    sys.path.append(module_path)

from __init__ import db
from models.quiz import Quiz

class QuizController:
    @staticmethod
    def get_all_quizzes(category=None, difficulty=None, search=None):
        """Pobiera wszystkie quizy z opcjonalnym filtrowaniem"""
        query = Quiz.query
        
        # Filtrowanie po kategorii
        if category:
            query = query.filter(Quiz.category == category)
        
        # Filtrowanie po trudności
        if difficulty:
            query = query.filter(Quiz.difficulty == difficulty)
        
        # Filtrowanie po wyszukiwaniu
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Quiz.title.ilike(search_term)) | 
                (Quiz.description.ilike(search_term))
            )
        
        try:
            quizzes = query.all()
            return [quiz.to_dict() for quiz in quizzes], None
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving quizzes"
    
    @staticmethod
    def get_quiz_by_id(quiz_id):
        """Pobiera quiz na podstawie ID"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            return quiz.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving quiz"
    
    @staticmethod
    def create_quiz(data):
        """Tworzy nowy quiz"""
        try:
            new_quiz = Quiz(
                title=data.get('title', ''),
                description=data.get('description', ''),
                category=data.get('category'),
                difficulty=data.get('difficulty'),
                time_limit=data.get('timeLimit'),
                user_id=data.get('userId'),
                created_at=data.get('createdAt'),
                last_modified=data.get('lastModified')
            )
            
            new_quiz.questions = data.get('questions', [])
            
            db.session.add(new_quiz)
            db.session.commit()
            
            return new_quiz.to_dict(), None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while creating quiz"
    
    @staticmethod
    def update_quiz(quiz_id, data):
        """Aktualizuje istniejący quiz"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            
            quiz.title = data.get('title', quiz.title)
            quiz.description = data.get('description', quiz.description)
            quiz.category = data.get('category', quiz.category)
            quiz.difficulty = data.get('difficulty', quiz.difficulty)
            quiz.time_limit = data.get('timeLimit', quiz.time_limit)
            quiz.last_modified = data.get('lastModified', quiz.last_modified)
            
            if 'questions' in data:
                quiz.questions = data.get('questions')
            
            db.session.commit()
            
            return quiz.to_dict(), None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while updating quiz"
    
    @staticmethod
    def delete_quiz(quiz_id):
        """Usuwa quiz o podanym ID"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found"
            
            db.session.delete(quiz)
            db.session.commit()
            
            return True, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return False, "Database error occurred while deleting quiz"
