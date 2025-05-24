from .models import Quiz
from .quiz_controller import QuizController
from flask_restful import Resource
from flask import request, jsonify, make_response
from utils.helpers import sanitize_input
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from .models import User

class GetQuizzes(Resource):
    def get(self):
        """Get all quizzes with optional filtering"""
        category = sanitize_input(request.args.get('category'))
        difficulty = sanitize_input(request.args.get('difficulty'))
        search = sanitize_input(request.args.get('search'))
        
        quizzes, error = QuizController.get_all_quizzes(
            category=category,
            difficulty=difficulty,
            search=search
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'quizzes': quizzes})
    
class QuizResource(Resource):
    @jwt_required(locations=["cookies"])
    def get(self, quiz_id=None):
        """Handle quiz GET requests"""
        try:
            # If quiz_id is provided, get specific quiz
            if quiz_id:
                logging.info(f"Getting quiz with ID: {quiz_id}")
                
                quiz_data, error = QuizController.get_quiz_by_id(quiz_id)
                
                if error or not quiz_data:
                    logging.error(f"Quiz {quiz_id} not found: {error}")
                    return {'error': 'Quiz not found'}, 404
                
                return quiz_data, 200
            
            # Otherwise, get all quizzes
            category = request.args.get('category')
            difficulty = request.args.get('difficulty')
            search = request.args.get('search')
            
            # Check if client has a valid cached version
            etag = request.headers.get('If-None-Match')
            
            # Get all quizzes with optional filtering
            quizzes, error = QuizController.get_all_quizzes(
                category=category,
                difficulty=difficulty,
                search=search
            )
            
            if error:
                logging.error(f"Error getting quizzes: {error}")
                return {'error': error}, 400
            
            # Apply filters (placeholder logic)
            if category or difficulty or search:
                # Here you would filter quizzes based on these parameters
                # For now, just log that filters were applied
                logging.info(f"Filtering quizzes with category={category}, difficulty={difficulty}, search={search}")
            
            # Generate ETag for the current data
            current_etag = str(hash(str(quizzes)))
            
            # If client's cached version matches current data, return 304 Not Modified
            if etag and etag == current_etag:
                return '', 304
            
            # Return response with quizzes list directly for tests compatibility
            return {'quizzes': quizzes}, 200
            
        except Exception as e:
            logging.error(f"Error in get_quizzes: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required(locations=["cookies"])
    def post(self):
        """Handle quiz POST requests"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Add current user ID as author
            current_user_id = get_jwt_identity()
            
            # Add current user ID as author
            current_user_id = get_jwt_identity()
            
            # Find user - handle both regular users and OAuth users
            user = None
            try:
                # Try as regular user ID first
                numeric_id = int(current_user_id)
                if numeric_id < 1000000000:  # Regular user ID
                    user = User.query.get(numeric_id)
                else:  # Large number, likely Google ID
                    user = User.query.filter_by(google_id=current_user_id).first()
            except (ValueError, TypeError):
                # If conversion fails, try as Google ID string
                user = User.query.filter_by(google_id=current_user_id).first()
            
            if not user:
                return {'error': 'User not found'}, 404
            
            data['author_id'] = user.id
            
            # Create quiz using QuizController
            quiz, error = QuizController.create_quiz(data)
            
            if error:
                logging.error(f"Error creating quiz: {error}")
                return {'error': error}, 400
            
            return quiz, 201
            
        except Exception as e:
            logging.error(f"Error creating quiz: {str(e)}")
            return {'error': 'Internal server error'}, 500

    @jwt_required(locations=["cookies"])
    def put(self, quiz_id):
        """Update existing quiz"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Check if user is quiz author or admin
            current_user_id = get_jwt_identity()
            quiz_data, error = QuizController.get_quiz_by_id(quiz_id)
            if error or not quiz_data:
                logging.error(f"Quiz {quiz_id} not found: {error}")
                return {'error': 'Quiz not found'}, 404
            
            # Try to find user by regular ID first
            user = User.query.get(current_user_id)
            # If user not found by ID, try by google_id (for OAuth users)
            if not user:
                user = User.query.filter_by(google_id=current_user_id).first()
            
            if not user:
                logging.error(f"User {current_user_id} not found")
                return {'error': 'User not found'}, 404
            
            # Check if user is admin or quiz author
            if not user.is_admin_user() and quiz_data['author_id'] != user.id:
                logging.warning(f"User {current_user_id} (ID: {user.id}) attempted to update quiz {quiz_id} (author: {quiz_data['author_id']}) without permission")
                return {'error': 'You do not have permission to update this quiz'}, 403
            
            # Update quiz using QuizController
            updated_quiz, error = QuizController.update_quiz(quiz_id, data)
            
            if error:
                logging.error(f"Error updating quiz: {error}")
                return {'error': error}, 400
            
            return updated_quiz, 200
            
        except Exception as e:
            logging.error(f"Error updating quiz {quiz_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required(locations=["cookies"])
    def delete(self, quiz_id):
        """Delete quiz"""
        try:
            # Check if user is quiz author or admin
            current_user_id = get_jwt_identity()
            quiz_data, error = QuizController.get_quiz_by_id(quiz_id)
            if error or not quiz_data:
                logging.error(f"Quiz {quiz_id} not found: {error}")
                return {'error': 'Quiz not found'}, 404
            
            # Try to find user by regular ID first
            user = User.query.get(current_user_id)
            # If user not found by ID, try by google_id (for OAuth users)
            if not user:
                user = User.query.filter_by(google_id=current_user_id).first()
            
            if not user:
                logging.error(f"User {current_user_id} not found")
                return {'error': 'User not found'}, 404
            
            # Check if user is admin or quiz author
            if not user.is_admin_user() and quiz_data['author_id'] != user.id:
                logging.warning(f"User {current_user_id} (ID: {user.id}) attempted to delete quiz {quiz_id} (author: {quiz_data['author_id']}) without permission")
                return {'error': 'You do not have permission to delete this quiz'}, 403
            
            # Delete quiz using QuizController
            success, error = QuizController.delete_quiz(quiz_id)
            
            if not success:
                logging.error(f"Error deleting quiz: {error}")
                return {'error': error}, 400
            
            return {'message': 'Quiz deleted successfully'}, 200
            
        except Exception as e:
            logging.error(f"Error deleting quiz {quiz_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500

class OptionsQuizResource(Resource):
    def get(self, quiz_id):
        """Get quiz questions without correct answers (for solving)"""
        try:
            quiz_options, error = QuizController.get_quiz_options(quiz_id)
            if error or not quiz_options:
                logging.error(f"Quiz {quiz_id} not found: {error}")
                return {'error': 'Quiz not found'}, 404
            
            return quiz_options, 200
            
        except Exception as e:
            logging.error(f"Error getting quiz options {quiz_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    def options(self, quiz_id=None):
        """Handle OPTIONS requests for CORS preflight"""
        return '', 200, {
            'Allow': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }