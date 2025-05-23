from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from werkzeug.security import check_password_hash

from app import db
from app.models.user import User

user_bp = Blueprint('user', __name__)

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[InputRequired()])
    new_password = PasswordField('New Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        InputRequired(), 
        EqualTo('new_password', message='Hasła muszą być identyczne')
    ])

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        form = UpdateProfileForm()
        
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'message': 'Błędne dane',
                'errors': form.errors
            }), 400
        
        # Check if username is taken by another user
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Ta nazwa użytkownika jest już zajęta'
                }), 400
        
        # Check if email is taken by another user
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Ten email jest już zarejestrowany'
                }), 400
        
        # Update user data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profil został zaktualizowany',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas aktualizacji profilu: {str(e)}'
        }), 500

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        form = ChangePasswordForm()
        
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'message': 'Błędne dane',
                'errors': form.errors
            }), 400
        
        # Check current password
        if not current_user.check_password(form.current_password.data):
            return jsonify({
                'success': False,
                'message': 'Nieprawidłowe obecne hasło'
            }), 400
        
        # Set new password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Hasło zostało zmienione'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas zmiany hasła: {str(e)}'
        }), 500

@user_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics"""
    try:
        from app.models.quiz import Quiz, QuizAttempt
        
        # Count user's quizzes
        quiz_count = Quiz.query.filter_by(creator_id=current_user.id).count()
        
        # Count user's attempts
        attempt_count = QuizAttempt.query.filter_by(user_id=current_user.id).count()
        
        # Get average score
        attempts = QuizAttempt.query.filter_by(
            user_id=current_user.id
        ).filter(
            QuizAttempt.completed_at.isnot(None)
        ).all()
        
        avg_score = 0
        if attempts:
            total_percentage = sum(attempt.percentage for attempt in attempts if attempt.percentage)
            avg_score = total_percentage / len(attempts)
        
        # Get recent attempts
        recent_attempts = QuizAttempt.query.filter_by(
            user_id=current_user.id
        ).order_by(
            QuizAttempt.started_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'quiz_count': quiz_count,
                'attempt_count': attempt_count,
                'average_score': round(avg_score, 1),
                'is_premium': current_user.is_premium,
                'premium_expires_at': current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None
            },
            'recent_attempts': [attempt.to_dict() for attempt in recent_attempts]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania statystyk: {str(e)}'
        }), 500

@user_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    """Delete user account"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Wymagane jest podanie hasła'
            }), 400
        
        # Verify password
        if not current_user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Nieprawidłowe hasło'
            }), 400
        
        # Delete user (cascade will handle related records)
        user_id = current_user.id
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Konto zostało usunięte'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas usuwania konta: {str(e)}'
        }), 500
