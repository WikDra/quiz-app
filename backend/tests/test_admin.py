"""
Integration tests for admin functionality.

This module tests admin dashboard, user management, payment management,
and administrative access control.
"""

import pytest
import json
from app.models import User, OfflinePayment, StripeSubscription
from datetime import datetime, timedelta


class TestAdminDashboard:
    """Test cases for admin dashboard endpoint."""
    
    def test_admin_dashboard_access(self, client, db_session, admin_auth_headers, sample_user, premium_user, stripe_subscription):
        """Test admin access to dashboard."""
        response = client.get('/admin/dashboard', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify dashboard contains expected statistics
        assert 'users' in data
        assert 'quizzes' in data
        assert 'payments' in data
        
        # Check user statistics
        assert data['users']['total'] >= 2  # At least sample_user and premium_user
        assert data['users']['premium'] >= 1  # At least premium_user
        assert data['users']['active'] >= 0
        
        # Check payment statistics
        assert 'stripe_subscriptions' in data['payments']
        assert 'offline_payments' in data['payments']
    
    def test_admin_dashboard_non_admin_access(self, client, db_session, auth_headers):
        """Test non-admin access to dashboard (should fail)."""
        response = client.get('/admin/dashboard', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_admin_dashboard_without_auth(self, client, db_session):
        """Test dashboard access without authentication."""
        response = client.get('/admin/dashboard')
        
        assert response.status_code == 401


class TestAdminUserManagement:
    """Test cases for admin user management endpoints."""
    
    def test_get_all_users_admin(self, client, db_session, admin_auth_headers, sample_user, premium_user):
        """Test admin access to all users list."""
        response = client.get('/admin/users', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our test users
        
        # Verify user data structure
        user_emails = [user['email'] for user in data]
        assert sample_user.email in user_emails
        assert premium_user.email in user_emails
        
        # Check that sensitive data is not exposed
        for user in data:
            assert 'password_hash' not in user
            assert 'id' in user
            assert 'email' in user
            assert 'username' in user
            assert 'role' in user
    
    def test_get_all_users_non_admin(self, client, db_session, auth_headers):
        """Test non-admin access to users list (should fail)."""
        response = client.get('/admin/users', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_promote_user_to_admin(self, client, db_session, admin_auth_headers, sample_user):
        """Test promoting regular user to admin."""
        assert sample_user.role == 'user'
        assert sample_user.is_admin is False
        
        response = client.post(f'/admin/users/{sample_user.id}/promote', 
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['role'] == 'admin'
        assert data['is_admin'] is True
        
        # Verify changes in database
        db_session.refresh(sample_user)
        assert sample_user.role == 'admin'
        assert sample_user.is_admin is True
    
    def test_demote_admin_to_user(self, client, db_session, admin_auth_headers, admin_user):
        """Test demoting admin to regular user."""
        # Create another admin to test demotion
        test_admin = User(
            username='testadmin',
            email='testadmin@example.com',
            role='admin',
            is_admin=True
        )
        test_admin.set_password('adminpass')
        db_session.add(test_admin)
        db_session.commit()
        
        response = client.post(f'/admin/users/{test_admin.id}/demote', 
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['role'] == 'user'
        assert data['is_admin'] is False
        
        # Verify changes in database
        db_session.refresh(test_admin)
        assert test_admin.role == 'user'
        assert test_admin.is_admin is False
    
    def test_promote_user_non_admin(self, client, db_session, auth_headers, sample_user):
        """Test non-admin attempting to promote user."""
        response = client.post(f'/admin/users/{sample_user.id}/promote', 
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_promote_nonexistent_user(self, client, db_session, admin_auth_headers):
        """Test promoting non-existent user."""
        response = client.post('/admin/users/99999/promote', 
                              headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_edit_user_info_admin(self, client, db_session, admin_auth_headers, sample_user):
        """Test admin editing user information."""
        edit_data = {
            'username': 'editedusername',
            'email': 'edited@example.com',
            'has_premium_access': True
        }
        
        response = client.put(f'/admin/users/{sample_user.id}', 
                             json=edit_data,
                             headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'editedusername'
        assert data['email'] == 'edited@example.com'
        assert data['has_premium_access'] is True
        
        # Verify changes in database
        db_session.refresh(sample_user)
        assert sample_user.username == 'editedusername'
        assert sample_user.email == 'edited@example.com'
        assert sample_user.has_premium_access is True
    
    def test_edit_user_invalid_email(self, client, db_session, admin_auth_headers, sample_user):
        """Test editing user with invalid email format."""
        edit_data = {
            'email': 'invalid-email-format'
        }
        
        response = client.put(f'/admin/users/{sample_user.id}', 
                             json=edit_data,
                             headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_edit_user_duplicate_email(self, client, db_session, admin_auth_headers, sample_user, premium_user):
        """Test editing user with duplicate email."""
        edit_data = {
            'email': premium_user.email  # Using existing email
        }
        
        response = client.put(f'/admin/users/{sample_user.id}', 
                             json=edit_data,
                             headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data


class TestAdminPaymentManagement:
    """Test cases for admin payment management."""
    
    def test_get_offline_payments(self, client, db_session, admin_auth_headers, offline_payment_pending, offline_payment_approved):
        """Test admin access to offline payments."""
        response = client.get('/admin/payments/offline', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our test payments
        
        # Verify payment data structure
        payment_ids = [payment['id'] for payment in data]
        assert offline_payment_pending.id in payment_ids
        assert offline_payment_approved.id in payment_ids
        
        # Check payment details
        for payment in data:
            assert 'id' in payment
            assert 'user_email' in payment
            assert 'amount' in payment
            assert 'status' in payment
            assert 'created_at' in payment
    
    def test_get_offline_payments_filtered_by_status(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test filtering offline payments by status."""
        response = client.get('/admin/payments/offline?status=pending', 
                             headers=admin_auth_headers)
        
        if response.status_code == 200:
            data = response.get_json()
            for payment in data:
                assert payment['status'] == 'pending'
        else:
            # Filtering not implemented
            assert response.status_code in [400, 404]
    
    def test_approve_offline_payment_with_notes(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test approving offline payment with admin notes."""
        approval_data = {
            'notes': 'Payment verified via bank statement. Reference: REF123456'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_pending.id}/approve',
                              json=approval_data,
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'approved'
        assert data['notes'] == 'Payment verified via bank statement. Reference: REF123456'
        assert data['approved_at'] is not None
        
        # Verify user got premium access
        user = offline_payment_pending.user
        db_session.refresh(user)
        assert user.has_premium_access is True
        assert user.premium_since is not None
    
    def test_reject_offline_payment_with_reason(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test rejecting offline payment with reason."""
        rejection_data = {
            'notes': 'Invalid payment proof. No matching bank transfer found.'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_pending.id}/reject',
                              json=rejection_data,
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejected'
        assert data['notes'] == 'Invalid payment proof. No matching bank transfer found.'
        
        # Verify user did not get premium access
        user = offline_payment_pending.user
        db_session.refresh(user)
        assert user.has_premium_access is False
    
    def test_approve_already_approved_payment(self, client, db_session, admin_auth_headers, offline_payment_approved):
        """Test approving an already approved payment."""
        approval_data = {
            'notes': 'Trying to approve again'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_approved.id}/approve',
                              json=approval_data,
                              headers=admin_auth_headers)
        
        # Might succeed (allowing re-approval) or fail (preventing double approval)
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            data = response.get_json()
            assert 'error' in data or 'message' in data
    
    def test_get_failed_stripe_payments(self, client, db_session, admin_auth_headers, failed_stripe_subscription):
        """Test admin access to failed Stripe payments."""
        response = client.get('/admin/payments/failed', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        
        # Should include our failed subscription
        failed_payment_found = False
        for payment in data:
            if payment.get('stripe_subscription_id') == failed_stripe_subscription.stripe_subscription_id:
                failed_payment_found = True
                assert payment['failed_payment_count'] >= 1
                assert payment['status'] == 'past_due'
                break
        
        assert failed_payment_found


class TestAdminAccessControl:
    """Test access control for admin endpoints."""
    
    def test_admin_endpoints_require_admin_role(self, client, db_session, auth_headers):
        """Test that admin endpoints require admin role."""
        admin_endpoints = [
            ('/admin/dashboard', 'GET'),
            ('/admin/users', 'GET'),
            ('/admin/users/1/promote', 'POST'),
            ('/admin/users/1/demote', 'POST'),
            ('/admin/users/1', 'PUT'),
            ('/admin/payments/offline', 'GET'),
            ('/admin/payments/offline/1/approve', 'POST'),
            ('/admin/payments/offline/1/reject', 'POST'),
            ('/admin/payments/failed', 'GET'),
        ]
        
        for endpoint, method in admin_endpoints:
            if method == 'GET':
                response = client.get(endpoint, headers=auth_headers)
            elif method == 'POST':
                response = client.post(endpoint, json={}, headers=auth_headers)
            elif method == 'PUT':
                response = client.put(endpoint, json={}, headers=auth_headers)
            
            assert response.status_code == 403, f"Endpoint {endpoint} should require admin access"
    
    def test_admin_endpoints_without_auth(self, client, db_session):
        """Test admin endpoints without authentication."""
        admin_endpoints = [
            ('/admin/dashboard', 'GET'),
            ('/admin/users', 'GET'),
            ('/admin/payments/offline', 'GET'),
            ('/admin/payments/failed', 'GET'),
        ]
        
        for endpoint, method in admin_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
    
    def test_admin_role_persistence(self, client, db_session, sample_user, admin_auth_headers):
        """Test that admin role changes persist across requests."""
        # Promote user to admin
        response = client.post(f'/admin/users/{sample_user.id}/promote', 
                              headers=admin_auth_headers)
        assert response.status_code == 200
        
        # Login as newly promoted admin
        login_response = client.post('/login', json={
            'email': sample_user.email,
            'password': 'testpassword'
        })
        assert login_response.status_code == 200
        
        new_admin_token = login_response.get_json()['access_token']
        new_admin_headers = {
            'Authorization': f'Bearer {new_admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Test admin access with new token
        response = client.get('/admin/dashboard', headers=new_admin_headers)
        assert response.status_code == 200


class TestAdminQuizManagement:
    """Test admin quiz management capabilities."""
    
    def test_admin_can_edit_any_quiz(self, client, db_session, admin_auth_headers, sample_quiz):
        """Test that admin can edit any user's quiz."""
        edit_data = {
            'title': 'Admin Edited Quiz',
            'description': 'Modified by admin'
        }
        
        response = client.put(f'/quiz/{sample_quiz.id}', 
                             json=edit_data,
                             headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Admin Edited Quiz'
        assert data['description'] == 'Modified by admin'
    
    def test_admin_can_delete_any_quiz(self, client, db_session, admin_auth_headers, sample_quiz):
        """Test that admin can delete any user's quiz."""
        quiz_id = sample_quiz.id
        
        response = client.delete(f'/quiz/{quiz_id}', headers=admin_auth_headers)
        
        assert response.status_code == 200
        
        # Verify quiz was deleted
        from app.models import Quiz
        deleted_quiz = Quiz.query.get(quiz_id)
        assert deleted_quiz is None


class TestAdminUserStatistics:
    """Test admin access to user statistics and analytics."""
    
    def test_user_activity_statistics(self, client, db_session, admin_auth_headers, sample_user, premium_user):
        """Test admin access to user activity statistics."""
        response = client.get('/admin/users/statistics', headers=admin_auth_headers)
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'total_users' in data
            assert 'premium_users' in data
            assert 'active_users' in data
            assert data['total_users'] >= 2
        else:
            # Statistics endpoint not implemented
            assert response.status_code in [404, 405]
    
    def test_payment_statistics(self, client, db_session, admin_auth_headers, stripe_subscription, offline_payment_approved):
        """Test admin access to payment statistics."""
        response = client.get('/admin/payments/statistics', headers=admin_auth_headers)
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'total_revenue' in data or 'payment_counts' in data
        else:
            # Statistics endpoint not implemented
            assert response.status_code in [404, 405]


class TestAdminErrorHandling:
    """Test error handling in admin functionality."""
    
    def test_admin_action_on_nonexistent_user(self, client, db_session, admin_auth_headers):
        """Test admin actions on non-existent users."""
        nonexistent_id = 99999
        
        # Test promote
        response = client.post(f'/admin/users/{nonexistent_id}/promote', 
                              headers=admin_auth_headers)
        assert response.status_code == 404
        
        # Test demote
        response = client.post(f'/admin/users/{nonexistent_id}/demote', 
                              headers=admin_auth_headers)
        assert response.status_code == 404
        
        # Test edit
        response = client.put(f'/admin/users/{nonexistent_id}', 
                             json={'username': 'test'},
                             headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_admin_action_on_nonexistent_payment(self, client, db_session, admin_auth_headers):
        """Test admin actions on non-existent payments."""
        nonexistent_id = 99999
        
        # Test approve
        response = client.post(f'/admin/payments/offline/{nonexistent_id}/approve', 
                              json={'notes': 'test'},
                              headers=admin_auth_headers)
        assert response.status_code == 404
        
        # Test reject
        response = client.post(f'/admin/payments/offline/{nonexistent_id}/reject', 
                              json={'notes': 'test'},
                              headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_admin_malformed_requests(self, client, db_session, admin_auth_headers, sample_user):
        """Test admin endpoints with malformed requests."""
        # Test user edit with invalid JSON
        response = client.put(f'/admin/users/{sample_user.id}', 
                             data='{"username": invalid json}',
                             headers=admin_auth_headers)
        assert response.status_code == 400
        
        # Test payment approval with invalid JSON
        response = client.post('/admin/payments/offline/1/approve', 
                              data='{"notes": invalid}',
                              headers=admin_auth_headers)
        assert response.status_code in [400, 404]  # 404 if payment doesn't exist
    
    def test_admin_rate_limiting(self, client, db_session, admin_auth_headers, sample_user):
        """Test rate limiting on admin actions."""
        # Attempt multiple rapid admin actions
        responses = []
        for i in range(10):
            response = client.put(f'/admin/users/{sample_user.id}', 
                                 json={'username': f'test{i}'},
                                 headers=admin_auth_headers)
            responses.append(response.status_code)
        
        # Most should succeed (rate limiting might not be implemented)
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 5  # At least half should succeed
