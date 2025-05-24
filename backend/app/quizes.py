from .models import Quiz
from .quiz_controller import QuizController
from flask_restful import Resource
from flask import request, jsonify, make_response
from utils.helpers import sanitize_input
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

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
                
                quiz = QuizController.get_quiz_by_id(quiz_id)
                
                if not quiz:
                    logging.error(f"Quiz {quiz_id} not found")
                    return {'error': 'Quiz not found'}, 404
                
                return quiz, 200
            
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
                resp = make_response('', 304)
                return resp
            
            # Create response with cache headers
            resp = make_response({'quizzes': quizzes})
            resp.headers['Cache-Control'] = 'private, max-age=5'
            resp.headers['ETag'] = current_etag
            
            return resp
            
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
            data['author_id'] = current_user_id
            
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
            quiz = QuizController.get_quiz_by_id(quiz_id)
            if not quiz:
                logging.error(f"Quiz {quiz_id} not found")
                return {'error': 'Quiz not found'}, 404
            
            if quiz:
                user = User.query.get(current_user_id)
                if not (hasattr(user, 'is_admin') and user.is_admin) and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                    logging.warning(f"User {current_user_id} attempted to update quiz {quiz_id} without permission")
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
            quiz = QuizController.get_quiz_by_id(quiz_id)
            if not quiz:
                logging.error(f"Quiz {quiz_id} not found")
                return {'error': 'Quiz not found'}, 404
            
            if quiz:
                user = User.query.get(current_user_id)
                if not (hasattr(user, 'is_admin') and user.is_admin) and ('author_id' not in quiz or quiz['author_id'] != current_user_id):
                    logging.warning(f"User {current_user_id} attempted to delete quiz {quiz_id} without permission")
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