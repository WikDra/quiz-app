from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import InputRequired, Length, NumberRange
from datetime import datetime

from app import db
from app.models.quiz import Quiz, Question, Answer, QuizAttempt

quiz_bp = Blueprint('quiz', __name__)

# Forms for validation
class AnswerForm(FlaskForm):
    answer_text = StringField('Answer Text', validators=[InputRequired(), Length(max=500)])
    is_correct = BooleanField('Is Correct')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[InputRequired(), Length(max=1000)])
    question_type = StringField('Question Type', default='multiple_choice')
    points = IntegerField('Points', validators=[NumberRange(min=1)], default=1)
    answers = FieldList(FormField(AnswerForm), min_entries=2)

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    is_public = BooleanField('Is Public', default=True)
    time_limit = IntegerField('Time Limit (seconds)', validators=[NumberRange(min=0)])
    randomize_questions = BooleanField('Randomize Questions', default=False)

@quiz_bp.route('/', methods=['GET'])
def get_quizzes():
    """Get list of public quizzes"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = Quiz.query.filter(Quiz.is_public == True)
        
        if search:
            query = query.filter(Quiz.title.contains(search))
        
        quizzes = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'quizzes': [quiz.to_dict() for quiz in quizzes.items],
            'pagination': {
                'page': page,
                'pages': quizzes.pages,
                'per_page': per_page,
                'total': quizzes.total,
                'has_next': quizzes.has_next,
                'has_prev': quizzes.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania quizów: {str(e)}'
        }), 500

@quiz_bp.route('/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get specific quiz"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Check if quiz is public or user is owner
        if not quiz.is_public and (not current_user.is_authenticated or quiz.creator_id != current_user.id):
            return jsonify({
                'success': False,
                'message': 'Brak dostępu do tego quizu'
            }), 403
        
        return jsonify({
            'success': True,
            'quiz': quiz.to_dict(include_questions=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania quizu: {str(e)}'
        }), 500

@quiz_bp.route('/my', methods=['GET'])
@login_required
def get_my_quizzes():
    """Get current user's quizzes"""
    try:
        quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
        
        return jsonify({
            'success': True,
            'quizzes': [quiz.to_dict() for quiz in quizzes]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania quizów: {str(e)}'
        }), 500

@quiz_bp.route('/create', methods=['POST'])
@login_required
def create_quiz():
    """Create new quiz"""
    try:
        data = request.get_json()
        
        # Create quiz
        quiz = Quiz(
            title=data.get('title'),
            description=data.get('description', ''),
            creator_id=current_user.id,
            is_public=data.get('is_public', True),
            time_limit=data.get('time_limit'),
            randomize_questions=data.get('randomize_questions', False)
        )
        
        db.session.add(quiz)
        db.session.flush()  # Get quiz ID
        
        # Add questions
        questions_data = data.get('questions', [])
        for q_data in questions_data:
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data.get('question_text'),
                question_type=q_data.get('question_type', 'multiple_choice'),
                points=q_data.get('points', 1),
                order_index=q_data.get('order_index', 0)
            )
            
            db.session.add(question)
            db.session.flush()  # Get question ID
            
            # Add answers
            answers_data = q_data.get('answers', [])
            for a_data in answers_data:
                answer = Answer(
                    question_id=question.id,
                    answer_text=a_data.get('answer_text'),
                    is_correct=a_data.get('is_correct', False),
                    order_index=a_data.get('order_index', 0)
                )
                
                db.session.add(answer)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz został utworzony',
            'quiz': quiz.to_dict(include_questions=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas tworzenia quizu: {str(e)}'
        }), 500

@quiz_bp.route('/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start quiz attempt"""
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Check access
        if not quiz.is_public and quiz.creator_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Brak dostępu do tego quizu'
            }), 403
        
        # Create new attempt
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            started_at=datetime.utcnow()
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        # Return quiz without correct answers
        quiz_data = quiz.to_dict(include_questions=True)
        # Remove correct answers from response
        for question in quiz_data.get('questions', []):
            for answer in question.get('answers', []):
                answer.pop('is_correct', None)
        
        return jsonify({
            'success': True,
            'message': 'Quiz rozpoczęty',
            'attempt_id': attempt.id,
            'quiz': quiz_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas rozpoczynania quizu: {str(e)}'
        }), 500

@quiz_bp.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    """Submit quiz answers"""
    try:
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        # Check if user owns this attempt
        if attempt.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Brak dostępu do tej próby'
            }), 403
        
        # Check if already completed
        if attempt.completed_at:
            return jsonify({
                'success': False,
                'message': 'Ta próba została już ukończona'
            }), 400
        
        data = request.get_json()
        answers = data.get('answers', {})
        
        # Save answers and calculate score
        attempt.set_answers(answers)
        attempt.completed_at = datetime.utcnow()
        attempt.time_taken = (attempt.completed_at - attempt.started_at).total_seconds()
        attempt.calculate_score()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz ukończony',
            'attempt': attempt.to_dict(),
            'score': attempt.score,
            'max_score': attempt.max_score,
            'percentage': attempt.percentage
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas zapisywania odpowiedzi: {str(e)}'
        }), 500

@quiz_bp.route('/attempts', methods=['GET'])
@login_required
def get_my_attempts():
    """Get current user's quiz attempts"""
    try:
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.started_at.desc()).all()
        
        return jsonify({
            'success': True,
            'attempts': [attempt.to_dict() for attempt in attempts]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania prób: {str(e)}'
        }), 500
