from flask import Blueprint, request, jsonify
from app.controllers.quiz_controller import QuizController

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')

@quiz_bp.route('/quiz', methods=['GET'])
def get_quizzes():
    """Get all quizzes with optional filtering"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    search = request.args.get('search')
    
    quizzes, error = QuizController.get_all_quizzes(
        category=category,
        difficulty=difficulty,
        search=search
    )
    
    if error:
        return jsonify({"error": error}), 500
        
    return jsonify({"quizzes": quizzes})

@quiz_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get a specific quiz by ID"""
    quiz, error = QuizController.get_quiz_by_id(quiz_id)
    
    if error:
        status_code = 404 if error == "Quiz not found" else 500
        return jsonify({"error": error}), status_code
        
    return jsonify(quiz)

@quiz_bp.route('/quiz', methods=['POST'])
def create_quiz():
    """Create a new quiz"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    quiz_data = request.json
    
    # In the future, get user_id from the authentication token
    # For now, we'll pass None
    quiz, error = QuizController.create_quiz(quiz_data, user_id=None)
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify(quiz), 201

@quiz_bp.route('/quiz/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    """Update an existing quiz"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    quiz_data = request.json
    
    quiz, error = QuizController.update_quiz(quiz_id, quiz_data)
    
    if error:
        status_code = 404 if error == "Quiz not found" else 500
        return jsonify({"error": error}), status_code
        
    return jsonify(quiz)

@quiz_bp.route('/quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Delete a quiz"""
    success, error = QuizController.delete_quiz(quiz_id)
    
    if error:
        status_code = 404 if error == "Quiz not found" else 500
        return jsonify({"error": error}), status_code
        
    return jsonify({"success": True, "message": "Quiz deleted successfully"})
