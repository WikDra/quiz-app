from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

from app import db

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Creator
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Quiz settings
    is_public = db.Column(db.Boolean, default=True)
    time_limit = db.Column(db.Integer)  # in seconds
    randomize_questions = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)
    
    def to_dict(self, include_questions=False):
        """Convert quiz to dictionary for JSON response"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'creator_username': self.creator.username if self.creator else None,
            'is_public': self.is_public,
            'time_limit': self.time_limit,
            'randomize_questions': self.randomize_questions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'question_count': len(self.questions)
        }
        
        if include_questions:
            result['questions'] = [q.to_dict() for q in self.questions]
        
        return result
    
    def __repr__(self):
        return f'<Quiz {self.title}>'


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_answers=True):
        """Convert question to dictionary for JSON response"""
        result = {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': self.points,
            'order_index': self.order_index
        }
        
        if include_answers:
            result['answers'] = [a.to_dict() for a in self.answers]
        
        return result
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}...>'


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self, include_correct=False):
        """Convert answer to dictionary for JSON response"""
        result = {
            'id': self.id,
            'answer_text': self.answer_text,
            'order_index': self.order_index
        }
        
        if include_correct:
            result['is_correct'] = self.is_correct
        
        return result
    
    def __repr__(self):
        return f'<Answer {self.id}: {self.answer_text[:30]}...>'


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    # Attempt data
    answers_json = db.Column(db.Text)  # JSON string of user answers
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    percentage = db.Column(db.Float)
    
    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    time_taken = db.Column(db.Integer)  # in seconds
    
    def set_answers(self, answers_dict):
        """Set answers as JSON string"""
        self.answers_json = json.dumps(answers_dict)
    
    def get_answers(self):
        """Get answers as dictionary"""
        if self.answers_json:
            return json.loads(self.answers_json)
        return {}
    
    def calculate_score(self):
        """Calculate and set score based on answers"""
        if not self.answers_json:
            return
        
        answers = self.get_answers()
        total_points = 0
        earned_points = 0
        
        for question in self.quiz.questions:
            total_points += question.points
            user_answer_id = answers.get(str(question.id))
            
            if user_answer_id:
                correct_answer = next((a for a in question.answers if a.is_correct), None)
                if correct_answer and str(correct_answer.id) == str(user_answer_id):
                    earned_points += question.points
        
        self.score = earned_points
        self.max_score = total_points
        self.percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    
    def to_dict(self):
        """Convert attempt to dictionary for JSON response"""
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'quiz_title': self.quiz.title if self.quiz else None,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_taken': self.time_taken
        }
    
    def __repr__(self):
        return f'<QuizAttempt {self.id}: User {self.user_id} Quiz {self.quiz_id}>'
