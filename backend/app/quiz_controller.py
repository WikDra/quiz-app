import re
from flask import current_app
from .models import db, User, Quiz
import json
from utils.helpers import sanitize_input, validate_email
class QuizController:    
    @staticmethod
    def get_all_quizzes(category=None, difficulty=None, search=None):
        """
        Get all quizzes with optional filtering
        """
        try:
            # Start with base query
            query = Quiz.query
            
            # Apply filters if provided
            if category:
                query = query.filter(Quiz.category == category)
            
            if difficulty:
                query = query.filter(Quiz.difficulty == difficulty)
            
            if search:
                query = query.filter(Quiz.title.ilike(f'%{search}%'))
            
            # Execute query
            quizzes = query.all()
            
            # Convert to dict
            quizzes_list = [quiz.to_dict() for quiz in quizzes]
            
            return quizzes_list, None
        except Exception as e:
            current_app.logger.error(f"Error fetching quizzes: {str(e)}")
            return [], f"Error fetching quizzes: {str(e)}"
    
    @staticmethod
    def get_quiz_by_id(quiz_id):
        """
        Get a quiz by ID
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            
            if not quiz:
                return None, "Quiz not found"
            
            return quiz.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"Error fetching quiz: {str(e)}")
            return None, f"Error fetching quiz: {str(e)}"
    
    @staticmethod
    def create_quiz(quiz_data):
        """
        Create a new quiz
        """
        try:
            # Extract quiz data
            title = quiz_data.get('title')
            description = quiz_data.get('description')
            category = quiz_data.get('category')
            difficulty = quiz_data.get('difficulty')
            author_id = quiz_data.get('author_id')
            questions = quiz_data.get('questions', [])
            
            # Validate required fields
            if not title:
                return None, "Title is required"
            
            # Create quiz
            quiz = Quiz(
                title=title,
                description=description,
                category=category,
                difficulty=difficulty,
                author_id=author_id,
                questions_json=json.dumps(questions)
            )
            
            db.session.add(quiz)
            db.session.commit()
            
            return quiz.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"Error creating quiz: {str(e)}")
            db.session.rollback()
            return None, f"Error creating quiz: {str(e)}"
    
    @staticmethod
    def update_quiz(quiz_id, quiz_data):
        """
        Update an existing quiz
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            
            if not quiz:
                return None, "Quiz not found"
            
            # Update fields if provided
            if 'title' in quiz_data:
                quiz.title = quiz_data['title']
            
            if 'description' in quiz_data:
                quiz.description = quiz_data['description']
            
            if 'category' in quiz_data:
                quiz.category = quiz_data['category']
            
            if 'difficulty' in quiz_data:
                quiz.difficulty = quiz_data['difficulty']
            
            if 'questions' in quiz_data:
                quiz.questions_json = json.dumps(quiz_data['questions'])
            
            db.session.commit()
            
            return quiz.to_dict(), None
        except Exception as e:
            current_app.logger.error(f"Error updating quiz: {str(e)}")
            db.session.rollback()
            return None, f"Error updating quiz: {str(e)}"
    
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
        except Exception as e:
            current_app.logger.error(f"Error deleting quiz: {str(e)}")
            db.session.rollback()
            return False, f"Error deleting quiz: {str(e)}"