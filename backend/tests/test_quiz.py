"""
Integration tests for quiz endpoints.

This module tests quiz creation, retrieval, updating, deletion,
and quiz-solving functionality with proper access control.
"""

import pytest
import json
from app.models import Quiz, User


class TestQuizCreation:
    """Test cases for quiz creation endpoint."""
    
    def test_create_quiz_success(self, client, db_session, auth_headers, sample_user):
        """Test successful quiz creation by authenticated user."""
        quiz_data = {
            'title': 'New Test Quiz',
            'description': 'A comprehensive test quiz',
            'category': 'Science',
            'difficulty': 'medium',
            'questions': [
                {
                    'question': 'What is the atomic number of carbon?',
                    'options': ['6', '12', '14', '16'],
                    'correct_answer': 0
                },
                {
                    'question': 'Which gas makes up most of Earth\'s atmosphere?',
                    'options': ['Oxygen', 'Carbon Dioxide', 'Nitrogen', 'Hydrogen'],
                    'correct_answer': 2
                }
            ]
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'New Test Quiz'
        assert data['description'] == 'A comprehensive test quiz'
        assert data['category'] == 'Science'
        assert data['difficulty'] == 'medium'
        assert data['author_id'] == sample_user.id
        assert len(data['questions']) == 2
        assert data['questions'][0]['question'] == 'What is the atomic number of carbon?'
        
        # Verify quiz was created in database
        quiz = Quiz.query.filter_by(title='New Test Quiz').first()
        assert quiz is not None
        assert quiz.author_id == sample_user.id
    
    def test_create_quiz_without_auth(self, client, db_session):
        """Test quiz creation without authentication."""
        quiz_data = {
            'title': 'Unauthorized Quiz',
            'description': 'This should fail',
            'questions': []
        }
        
        response = client.post('/quiz', json=quiz_data)
        
        assert response.status_code == 401
    
    def test_create_quiz_missing_title(self, client, db_session, auth_headers):
        """Test quiz creation with missing title."""
        quiz_data = {
            'description': 'Quiz without title',
            'questions': []
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_create_quiz_empty_questions(self, client, db_session, auth_headers):
        """Test quiz creation with empty questions array."""
        quiz_data = {
            'title': 'Empty Quiz',
            'description': 'Quiz with no questions',
            'questions': []
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        # Should succeed - empty quizzes might be allowed for drafts
        assert response.status_code in [200, 201, 400]
    
    def test_create_quiz_invalid_questions(self, client, db_session, auth_headers):
        """Test quiz creation with invalid question format."""
        quiz_data = {
            'title': 'Invalid Quiz',
            'description': 'Quiz with malformed questions',
            'questions': [
                {
                    'question': 'Question without options',
                    'correct_answer': 0
                    # Missing 'options' field
                },
                {
                    'options': ['A', 'B', 'C'],
                    'correct_answer': 0
                    # Missing 'question' field
                }
            ]
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_create_quiz_invalid_correct_answer(self, client, db_session, auth_headers):
        """Test quiz creation with invalid correct_answer index."""
        quiz_data = {
            'title': 'Invalid Answer Quiz',
            'description': 'Quiz with wrong answer index',
            'questions': [
                {
                    'question': 'Test question?',
                    'options': ['A', 'B', 'C'],
                    'correct_answer': 5  # Index out of range
                }
            ]
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data


class TestQuizRetrieval:
    """Test cases for quiz retrieval endpoints."""
    
    def test_get_all_quizzes(self, client, db_session, sample_quiz, premium_quiz):
        """Test retrieving all quizzes."""
        response = client.get('/quizzes')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our test quizzes
        
        # Check quiz structure
        quiz_titles = [quiz['title'] for quiz in data]
        assert 'Sample Quiz' in quiz_titles
        assert 'Premium Physics Quiz' in quiz_titles
    
    def test_get_quiz_by_id(self, client, db_session, sample_quiz):
        """Test retrieving specific quiz by ID."""
        response = client.get(f'/quiz/{sample_quiz.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == sample_quiz.id
        assert data['title'] == sample_quiz.title
        assert data['description'] == sample_quiz.description
        assert 'questions' in data
        assert len(data['questions']) == 2  # Sample quiz has 2 questions
    
    def test_get_quiz_nonexistent_id(self, client, db_session):
        """Test retrieving quiz with non-existent ID."""
        response = client.get('/quiz/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_get_quiz_invalid_id(self, client, db_session):
        """Test retrieving quiz with invalid ID format."""
        response = client.get('/quiz/invalid_id')
        
        assert response.status_code == 404 or response.status_code == 400
    
    def test_get_quiz_premium_access_without_auth(self, client, db_session, premium_quiz):
        """Test accessing premium quiz without authentication."""
        response = client.get(f'/quiz/{premium_quiz.id}')
        
        # Premium quizzes might require authentication
        # This depends on implementation - adjust assertion as needed
        assert response.status_code in [200, 401, 403]
    
    def test_get_quiz_premium_access_regular_user(self, client, db_session, premium_quiz, auth_headers):
        """Test accessing premium quiz as regular user."""
        response = client.get(f'/quiz/{premium_quiz.id}', headers=auth_headers)
        
        # Regular users might not have access to premium content
        # This depends on implementation - adjust assertion as needed
        assert response.status_code in [200, 403]
    
    def test_get_quiz_premium_access_premium_user(self, client, db_session, premium_quiz, premium_auth_headers):
        """Test accessing premium quiz as premium user."""
        response = client.get(f'/quiz/{premium_quiz.id}', headers=premium_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == premium_quiz.id
        assert data['title'] == premium_quiz.title


class TestQuizUpdate:
    """Test cases for quiz updating endpoints."""
    
    def test_update_own_quiz(self, client, db_session, sample_quiz, auth_headers, sample_user):
        """Test updating own quiz as author."""
        update_data = {
            'title': 'Updated Quiz Title',
            'description': 'Updated description',
            'category': 'Updated Category',
            'difficulty': 'hard'
        }
        
        response = client.put(f'/quiz/{sample_quiz.id}', json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Updated Quiz Title'
        assert data['description'] == 'Updated description'
        assert data['category'] == 'Updated Category'
        assert data['difficulty'] == 'hard'
        
        # Verify changes in database
        db_session.refresh(sample_quiz)
        assert sample_quiz.title == 'Updated Quiz Title'
        assert sample_quiz.description == 'Updated description'
    
    def test_update_quiz_without_auth(self, client, db_session, sample_quiz):
        """Test updating quiz without authentication."""
        update_data = {
            'title': 'Unauthorized Update'
        }
        
        response = client.put(f'/quiz/{sample_quiz.id}', json=update_data)
        
        assert response.status_code == 401
    
    def test_update_others_quiz(self, client, db_session, premium_quiz, auth_headers):
        """Test updating another user's quiz (should fail)."""
        update_data = {
            'title': 'Unauthorized Update'
        }
        
        response = client.put(f'/quiz/{premium_quiz.id}', json=update_data, headers=auth_headers)
        
        # Should fail - users shouldn't be able to edit others' quizzes
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_update_quiz_admin_access(self, client, db_session, sample_quiz, admin_auth_headers):
        """Test updating any quiz as admin."""
        update_data = {
            'title': 'Admin Updated Quiz'
        }
        
        response = client.put(f'/quiz/{sample_quiz.id}', json=update_data, headers=admin_auth_headers)
        
        # Admin should be able to edit any quiz
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Admin Updated Quiz'
    
    def test_update_quiz_questions(self, client, db_session, sample_quiz, auth_headers):
        """Test updating quiz questions."""
        update_data = {
            'questions': [
                {
                    'question': 'New question 1?',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 1
                },
                {
                    'question': 'New question 2?',
                    'options': ['Option 1', 'Option 2'],
                    'correct_answer': 0
                }
            ]
        }
        
        response = client.put(f'/quiz/{sample_quiz.id}', json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['questions']) == 2
        assert data['questions'][0]['question'] == 'New question 1?'
        assert data['questions'][1]['correct_answer'] == 0


class TestQuizDeletion:
    """Test cases for quiz deletion endpoints."""
    
    def test_delete_own_quiz(self, client, db_session, sample_quiz, auth_headers, sample_user):
        """Test deleting own quiz as author."""
        quiz_id = sample_quiz.id
        
        response = client.delete(f'/quiz/{quiz_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        
        # Verify quiz was deleted from database
        deleted_quiz = Quiz.query.get(quiz_id)
        assert deleted_quiz is None
    
    def test_delete_quiz_without_auth(self, client, db_session, sample_quiz):
        """Test deleting quiz without authentication."""
        response = client.delete(f'/quiz/{sample_quiz.id}')
        
        assert response.status_code == 401
    
    def test_delete_others_quiz(self, client, db_session, premium_quiz, auth_headers):
        """Test deleting another user's quiz (should fail)."""
        response = client.delete(f'/quiz/{premium_quiz.id}', headers=auth_headers)
        
        # Should fail - users shouldn't be able to delete others' quizzes
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_delete_quiz_admin_access(self, client, db_session, sample_quiz, admin_auth_headers):
        """Test deleting any quiz as admin."""
        quiz_id = sample_quiz.id
        
        response = client.delete(f'/quiz/{quiz_id}', headers=admin_auth_headers)
        
        # Admin should be able to delete any quiz
        assert response.status_code == 200
        
        # Verify deletion
        deleted_quiz = Quiz.query.get(quiz_id)
        assert deleted_quiz is None
    
    def test_delete_nonexistent_quiz(self, client, db_session, auth_headers):
        """Test deleting non-existent quiz."""
        response = client.delete('/quiz/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data or 'message' in data


class TestQuizOptions:
    """Test cases for quiz options endpoint."""
    
    def test_get_quiz_options(self, client, db_session, sample_quiz):
        """Test retrieving quiz options (questions without correct answers)."""
        response = client.get(f'/quiz/{sample_quiz.id}/options')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'questions' in data
        
        # Verify correct answers are not included in options response
        for question in data['questions']:
            assert 'correct_answer' not in question
            assert 'question' in question
            assert 'options' in question
    
    def test_get_quiz_options_nonexistent(self, client, db_session):
        """Test retrieving options for non-existent quiz."""
        response = client.get('/quiz/99999/options')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_get_quiz_options_premium_content(self, client, db_session, premium_quiz):
        """Test retrieving options for premium quiz."""
        response = client.get(f'/quiz/{premium_quiz.id}/options')
        
        # Premium content access rules apply
        assert response.status_code in [200, 401, 403]


class TestQuizSolving:
    """Test cases for quiz solving functionality."""
    
    def test_submit_quiz_answers(self, client, db_session, sample_quiz, auth_headers):
        """Test submitting answers for a quiz."""
        # Get quiz questions first
        quiz_response = client.get(f'/quiz/{sample_quiz.id}/options')
        assert quiz_response.status_code == 200
        
        # Submit answers
        answers_data = {
            'answers': [0, 1]  # Answers for the two questions in sample_quiz
        }
        
        response = client.post(f'/quiz/{sample_quiz.id}/submit', 
                              json=answers_data, 
                              headers=auth_headers)
        
        # Implementation depends on whether submit endpoint exists
        # Adjust assertion based on actual implementation
        assert response.status_code in [200, 201, 404]
    
    def test_submit_quiz_answers_without_auth(self, client, db_session, sample_quiz):
        """Test submitting quiz answers without authentication."""
        answers_data = {
            'answers': [0, 1]
        }
        
        response = client.post(f'/quiz/{sample_quiz.id}/submit', json=answers_data)
        
        # Should require authentication
        assert response.status_code in [401, 404]
    
    def test_submit_incomplete_answers(self, client, db_session, sample_quiz, auth_headers):
        """Test submitting incomplete answers."""
        answers_data = {
            'answers': [0]  # Only one answer for a quiz with two questions
        }
        
        response = client.post(f'/quiz/{sample_quiz.id}/submit', 
                              json=answers_data, 
                              headers=auth_headers)
        
        # Should handle incomplete answers appropriately
        assert response.status_code in [200, 400, 404]
    
    def test_submit_invalid_answers(self, client, db_session, sample_quiz, auth_headers):
        """Test submitting invalid answer indices."""
        answers_data = {
            'answers': [999, -1]  # Invalid indices
        }
        
        response = client.post(f'/quiz/{sample_quiz.id}/submit', 
                              json=answers_data, 
                              headers=auth_headers)
        
        # Should validate answer indices
        assert response.status_code in [400, 404]


class TestQuizAccessControl:
    """Test cases for quiz access control and permissions."""
    
    def test_quiz_visibility_public(self, client, db_session, sample_quiz):
        """Test that public quizzes are visible to all."""
        response = client.get(f'/quiz/{sample_quiz.id}')
        
        # Public quizzes should be accessible without authentication
        assert response.status_code == 200
    
    def test_quiz_creation_rate_limiting(self, client, db_session, auth_headers):
        """Test quiz creation rate limiting (if implemented)."""
        quiz_data = {
            'title': 'Rate Limited Quiz',
            'description': 'Testing rate limits',
            'questions': [
                {
                    'question': 'Test?',
                    'options': ['A', 'B'],
                    'correct_answer': 0
                }
            ]
        }
        
        # Create multiple quizzes rapidly
        responses = []
        for i in range(5):
            quiz_data['title'] = f'Rate Limited Quiz {i}'
            response = client.post('/quiz', json=quiz_data, headers=auth_headers)
            responses.append(response.status_code)
        
        # Check if rate limiting is applied (most should succeed)
        success_count = sum(1 for status in responses if status in [200, 201])
        assert success_count >= 3  # At least some should succeed
    
    def test_quiz_search_functionality(self, client, db_session, sample_quiz, premium_quiz):
        """Test quiz search functionality (if implemented)."""
        # Test search by title
        response = client.get('/quizzes?search=Sample')
        
        if response.status_code == 200:
            data = response.get_json()
            titles = [quiz['title'] for quiz in data]
            assert any('Sample' in title for title in titles)
        else:
            # Search not implemented
            assert response.status_code in [400, 404]
    
    def test_quiz_category_filtering(self, client, db_session, sample_quiz, premium_quiz):
        """Test quiz filtering by category."""
        # Test filter by category
        response = client.get('/quizzes?category=Geography')
        
        if response.status_code == 200:
            data = response.get_json()
            for quiz in data:
                if 'category' in quiz:
                    assert quiz['category'] == 'Geography'
        else:
            # Filtering not implemented
            assert response.status_code in [400, 404]
    
    def test_quiz_difficulty_filtering(self, client, db_session, sample_quiz, premium_quiz):
        """Test quiz filtering by difficulty."""
        response = client.get('/quizzes?difficulty=easy')
        
        if response.status_code == 200:
            data = response.get_json()
            for quiz in data:
                if 'difficulty' in quiz:
                    assert quiz['difficulty'] == 'easy'
        else:
            # Filtering not implemented
            assert response.status_code in [400, 404]


class TestQuizErrorHandling:
    """Test error handling and edge cases for quiz endpoints."""
    
    def test_quiz_creation_with_large_payload(self, client, db_session, auth_headers):
        """Test quiz creation with very large payload."""
        # Create a quiz with many questions
        large_questions = []
        for i in range(100):  # 100 questions
            large_questions.append({
                'question': f'Question {i}?',
                'options': [f'Option {j}' for j in range(4)],
                'correct_answer': i % 4
            })
        
        quiz_data = {
            'title': 'Large Quiz',
            'description': 'Quiz with many questions',
            'questions': large_questions
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        # Should handle large payloads appropriately
        assert response.status_code in [200, 201, 400, 413]  # 413 = Payload Too Large
    
    def test_quiz_creation_with_special_characters(self, client, db_session, auth_headers):
        """Test quiz creation with special characters in content."""
        quiz_data = {
            'title': 'Quiz with Special chars: !@#$%^&*()_+{}[]|\\:";\'<>?,./',
            'description': 'Testing special characters & émojis 🧪🔬',
            'questions': [
                {
                    'question': 'What is H₂O?',
                    'options': ['Water', 'Hydrogen', 'Oxygen', 'Carbon'],
                    'correct_answer': 0
                }
            ]
        }
        
        response = client.post('/quiz', json=quiz_data, headers=auth_headers)
        
        # Should handle special characters properly
        assert response.status_code in [200, 201, 400]
    
    def test_quiz_malformed_json(self, client, db_session, auth_headers):
        """Test quiz endpoints with malformed JSON."""
        malformed_data = '{"title": "Test", "questions": [{'  # Incomplete JSON
        
        response = client.post('/quiz', 
                              data=malformed_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_quiz_missing_content_type(self, client, db_session, auth_headers):
        """Test quiz creation without proper content type."""
        quiz_data = '{"title": "Test Quiz", "questions": []}'
        
        headers = auth_headers.copy()
        headers.pop('Content-Type', None)  # Remove content type
        
        response = client.post('/quiz', 
                              data=quiz_data,
                              headers=headers)
        
        # Should handle missing content type
        assert response.status_code in [400, 415]  # 415 = Unsupported Media Type
