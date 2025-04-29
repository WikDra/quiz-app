from app import db
from app.models.quiz import Quiz
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
import json

class QuizController:
    @staticmethod
    def get_all_quizzes(category=None, difficulty=None, search=None):
        """
        Retrieve all quizzes with optional filtering
        """
        query = Quiz.query
        
        if category:
            query = query.filter(Quiz.category == category)
            
        if difficulty:
            query = query.filter(Quiz.difficulty == difficulty)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Quiz.title.ilike(search_term)) | 
                (Quiz.description.ilike(search_term))
            )
            
        try:
            quizzes = query.all()
            return [quiz.to_dict() for quiz in quizzes], None
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving quizzes"

    @staticmethod
    def get_quiz_by_id(quiz_id):
        """
        Retrieve a specific quiz by ID
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            return quiz.to_dict(), None
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while retrieving the quiz"

    @staticmethod
    def create_quiz(quiz_data, user_id=None):
        """
        Create a new quiz
        """
        if not quiz_data.get('title') or not quiz_data.get('questions'):
            return None, "Title and questions are required"
        
        try:
            new_quiz = Quiz(
                title=quiz_data.get('title'),
                description=quiz_data.get('description'),
                category=quiz_data.get('category'),
                difficulty=quiz_data.get('difficulty'),
                user_id=user_id
            )
            
            # Set questions using the property setter
            new_quiz.questions = quiz_data.get('questions')
            
            db.session.add(new_quiz)
            db.session.commit()
            
            return new_quiz.to_dict(), None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while creating the quiz"

    @staticmethod
    def update_quiz(quiz_id, quiz_data):
        """
        Update an existing quiz
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found"
            
            if 'title' in quiz_data:
                quiz.title = quiz_data['title']
            if 'description' in quiz_data:
                quiz.description = quiz_data['description']
            if 'category' in quiz_data:
                quiz.category = quiz_data['category']
            if 'difficulty' in quiz_data:
                quiz.difficulty = quiz_data['difficulty']
            if 'questions' in quiz_data:
                quiz.questions = quiz_data['questions']
            
            db.session.commit()
            return quiz.to_dict(), None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return None, "Database error occurred while updating the quiz"

    @staticmethod
    def delete_quiz(quiz_id):
        """
        Delete a quiz
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found"
            
            db.session.delete(quiz)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return False, "Database error occurred while deleting the quiz"

    @staticmethod
    def import_quizzes_from_json(file_path):
        """
        Import quizzes from a JSON file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if 'quizzes' not in data:
                return False, "Invalid JSON format: 'quizzes' key not found"
                
            quizzes_data = data['quizzes']
            for quiz_data in quizzes_data:
                new_quiz = Quiz(
                    title=quiz_data.get('title'),
                    description=quiz_data.get('description'),
                    category=quiz_data.get('category'),
                    difficulty=quiz_data.get('difficulty')
                )
                new_quiz.questions = quiz_data.get('questions', [])
                db.session.add(new_quiz)
                
            db.session.commit()
            return True, None
        except FileNotFoundError:
            return False, f"File not found: {file_path}"
        except json.JSONDecodeError:
            return False, "Invalid JSON format in the file"
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return False, "Database error occurred while importing quizzes"
