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
        # Validation
        required_fields = ['title', 'category', 'difficulty', 'questions']
        for field in required_fields:
            if field not in data or not data[field]:
                return None, f"Missing required field: {field}", 400

        title = data.get('title')
        if not (1 <= len(title) <= 100):
            return None, "Title must be between 1 and 100 characters.", 400

        description = data.get('description')
        if description and len(description) > 500:
            return None, "Description must be at most 500 characters.", 400

        category = data.get('category')
        if not category: # Already checked by required_fields, but good for clarity
            return None, "Category cannot be empty.", 400
        # Optional: Add validation against a predefined list of categories
        # predefined_categories = ["Science", "History", "General Knowledge"]
        # if category not in predefined_categories:
        #     return None, f"Invalid category. Allowed categories are: {', '.join(predefined_categories)}", 400

        difficulty = data.get('difficulty')
        if not difficulty: # Already checked by required_fields
            return None, "Difficulty cannot be empty.", 400
        # Optional: Add validation against a predefined list of difficulties
        # predefined_difficulties = ["Easy", "Medium", "Hard"]
        # if difficulty not in predefined_difficulties:
        #     return None, f"Invalid difficulty. Allowed difficulties are: {', '.join(predefined_difficulties)}", 400

        time_limit = data.get('timeLimit')
        if time_limit is not None:
            if not isinstance(time_limit, int) or time_limit < 0:
                return None, "Time limit must be a non-negative integer.", 400

        questions = data.get('questions')
        if not isinstance(questions, list) or not questions:
            return None, "Questions list cannot be empty.", 400

        for i, q_data in enumerate(questions):
            if not isinstance(q_data, dict):
                return None, f"Question at index {i} must be an object.", 400
            
            q_text = q_data.get('questionText')
            if not q_text or not isinstance(q_text, str):
                return None, f"Question text for question {i+1} cannot be empty.", 400

            answers = q_data.get('answers')
            if not isinstance(answers, list) or len(answers) < 2:
                return None, f"Question {i+1} must have at least 2 answers.", 400

            correct_answers_count = 0
            for j, ans_data in enumerate(answers):
                if not isinstance(ans_data, dict):
                    return None, f"Answer at index {j} for question {i+1} must be an object.", 400
                
                ans_text = ans_data.get('answerText')
                if not ans_text or not isinstance(ans_text, str):
                    return None, f"Answer text for answer {j+1} in question {i+1} cannot be empty.", 400
                
                is_correct = ans_data.get('isCorrect')
                if not isinstance(is_correct, bool):
                    return None, f"isCorrect flag for answer {j+1} in question {i+1} must be a boolean.", 400
                if is_correct:
                    correct_answers_count += 1
            
            if correct_answers_count == 0:
                return None, f"Question {i+1} must have at least one correct answer.", 400

        try:
            new_quiz = Quiz(
                title=title,
                description=description,
                category=category,
                difficulty=difficulty,
                time_limit=time_limit,
                user_id=data.get('userId'), # Assuming userId is validated elsewhere or comes from authenticated user
                # created_at and last_modified are usually handled by the database or ORM by default
            )
            
            # The questions structure in the Quiz model might need adjustment
            # if it expects ORM objects rather than dicts.
            # For now, assuming it can handle dicts or that the model's setter handles it.
            new_quiz.questions = questions 
            
            db.session.add(new_quiz)
            db.session.commit()
            
            return new_quiz.to_dict(), None, 201 # Return 201 Created status
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error or other exception: {str(e)}")
            # Consider more specific error handling if possible
            return None, "An error occurred while creating the quiz.", 500
    
    @staticmethod
    def update_quiz(quiz_id, data):
        """Aktualizuje istniejący quiz"""
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return None, "Quiz not found", 404

            # Validation for fields present in data
            if 'title' in data:
                title = data.get('title')
                if not title or not (1 <= len(title) <= 100):
                    return None, "Title must be between 1 and 100 characters.", 400
                quiz.title = title

            if 'description' in data:
                description = data.get('description')
                if description is not None and len(description) > 500: # Allow empty string to clear description
                    return None, "Description must be at most 500 characters.", 400
                quiz.description = description

            if 'category' in data:
                category = data.get('category')
                if not category:
                    return None, "Category cannot be empty.", 400
                # Optional: Add validation against a predefined list of categories
                quiz.category = category

            if 'difficulty' in data:
                difficulty = data.get('difficulty')
                if not difficulty:
                    return None, "Difficulty cannot be empty.", 400
                # Optional: Add validation against a predefined list of difficulties
                quiz.difficulty = difficulty

            if 'timeLimit' in data:
                time_limit = data.get('timeLimit')
                if time_limit is not None:
                    if not isinstance(time_limit, int) or time_limit < 0:
                        return None, "Time limit must be a non-negative integer.", 400
                quiz.time_limit = time_limit # Allows setting to None
            
            if 'lastModified' in data: # Usually handled by the application or DB trigger
                quiz.last_modified = data.get('lastModified')

            if 'questions' in data:
                questions = data.get('questions')
                if not isinstance(questions, list) or not questions:
                    return None, "Questions list cannot be empty if provided.", 400

                for i, q_data in enumerate(questions):
                    if not isinstance(q_data, dict):
                        return None, f"Question at index {i} must be an object.", 400
                    
                    q_text = q_data.get('questionText')
                    if not q_text or not isinstance(q_text, str):
                        return None, f"Question text for question {i+1} cannot be empty.", 400

                    answers = q_data.get('answers')
                    if not isinstance(answers, list) or len(answers) < 2:
                        return None, f"Question {i+1} must have at least 2 answers.", 400

                    correct_answers_count = 0
                    for j, ans_data in enumerate(answers):
                        if not isinstance(ans_data, dict):
                            return None, f"Answer at index {j} for question {i+1} must be an object.", 400
                        
                        ans_text = ans_data.get('answerText')
                        if not ans_text or not isinstance(ans_text, str):
                            return None, f"Answer text for answer {j+1} in question {i+1} cannot be empty.", 400
                        
                        is_correct = ans_data.get('isCorrect')
                        if not isinstance(is_correct, bool):
                            return None, f"isCorrect flag for answer {j+1} in question {i+1} must be a boolean.", 400
                        if is_correct:
                            correct_answers_count += 1
                    
                    if correct_answers_count == 0:
                        return None, f"Question {i+1} must have at least one correct answer.", 400
                quiz.questions = questions
            
            db.session.commit()
            
            return quiz.to_dict(), None, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error or other exception during update: {str(e)}")
            return None, "An error occurred while updating the quiz.", 500
    
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
