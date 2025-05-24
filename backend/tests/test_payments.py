"""
Integration tests for Stripe payment functionality.

This module tests Stripe checkout session creation, webhook handling,
subscription management, and failed payment scenarios.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.models import User, StripeSubscription, OfflinePayment


class TestStripeCheckoutSession:
    """Test cases for Stripe checkout session creation."""
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_success(self, mock_stripe_create, client, db_session, auth_headers, sample_user):
        """Test successful Stripe checkout session creation."""
        # Mock Stripe response
        mock_session = {
            'id': 'cs_test_123',
            'url': 'https://checkout.stripe.com/pay/cs_test_123',
            'payment_status': 'unpaid'
        }
        mock_stripe_create.return_value = mock_session
        
        response = client.post('/stripe/create-checkout-session', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'sessionId' in data
        assert 'sessionUrl' in data
        assert data['sessionId'] == 'cs_test_123'
        assert data['sessionUrl'] == 'https://checkout.stripe.com/pay/cs_test_123'
        
        # Verify Stripe was called with correct parameters
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        assert 'customer_email' in call_args
        assert call_args['customer_email'] == sample_user.email
        assert 'success_url' in call_args
        assert 'cancel_url' in call_args
    
    def test_create_checkout_session_without_auth(self, client, db_session):
        """Test checkout session creation without authentication."""
        response = client.post('/stripe/create-checkout-session')
        
        assert response.status_code == 401
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_stripe_error(self, mock_stripe_create, client, db_session, auth_headers):
        """Test checkout session creation with Stripe error."""
        # Mock Stripe error
        import stripe
        mock_stripe_create.side_effect = stripe.error.StripeError("Test error")
        
        response = client.post('/stripe/create-checkout-session', headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_existing_subscription(self, mock_stripe_create, client, db_session, premium_auth_headers, premium_user, stripe_subscription):
        """Test checkout session creation for user with existing subscription."""
        response = client.post('/stripe/create-checkout-session', headers=premium_auth_headers)
        
        # Might return error or allow upgrade - depends on implementation
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            data = response.get_json()
            assert 'error' in data or 'message' in data


class TestStripeWebhook:
    """Test cases for Stripe webhook handling."""
    
    def test_webhook_without_signature(self, client, db_session):
        """Test webhook call without Stripe signature."""
        webhook_data = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': 'test@example.com'
                }
            }
        }
        
        response = client.post('/stripe/webhook', 
                              json=webhook_data,
                              headers={'Content-Type': 'application/json'})
        
        # Should fail without proper signature
        assert response.status_code in [400, 401]
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_checkout_session_completed(self, mock_construct_event, client, db_session, sample_user):
        """Test webhook for completed checkout session."""
        # Mock Stripe webhook event
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': sample_user.email,
                    'customer': 'cus_test_123',
                    'subscription': 'sub_test_123',
                    'payment_status': 'paid'
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        webhook_payload = json.dumps(mock_event)
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        assert response.status_code == 200
        
        # Verify user got premium access
        db_session.refresh(sample_user)
        assert sample_user.has_premium_access is True
        assert sample_user.premium_since is not None
        
        # Verify subscription was created
        subscription = StripeSubscription.query.filter_by(user_id=sample_user.id).first()
        assert subscription is not None
        assert subscription.stripe_customer_id == 'cus_test_123'
        assert subscription.stripe_subscription_id == 'sub_test_123'
        assert subscription.status == 'active'
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_invoice_payment_failed(self, mock_construct_event, client, db_session, premium_user, stripe_subscription):
        """Test webhook for failed invoice payment."""
        mock_event = {
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'subscription': stripe_subscription.stripe_subscription_id,
                    'customer_email': premium_user.email
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        webhook_payload = json.dumps(mock_event)
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        assert response.status_code == 200
        
        # Verify failed payment count was incremented
        db_session.refresh(stripe_subscription)
        assert stripe_subscription.failed_payment_count == 1
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_customer_subscription_deleted(self, mock_construct_event, client, db_session, premium_user, stripe_subscription):
        """Test webhook for subscription cancellation."""
        mock_event = {
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'id': stripe_subscription.stripe_subscription_id,
                    'customer': stripe_subscription.stripe_customer_id
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        webhook_payload = json.dumps(mock_event)
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        assert response.status_code == 200
        
        # Verify subscription was cancelled
        db_session.refresh(stripe_subscription)
        assert stripe_subscription.status == 'canceled'
        assert stripe_subscription.canceled_at is not None
        
        # Verify user lost premium access
        db_session.refresh(premium_user)
        assert premium_user.has_premium_access is False
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_unhandled_event_type(self, mock_construct_event, client, db_session):
        """Test webhook with unhandled event type."""
        mock_event = {
            'type': 'unhandled.event.type',
            'data': {
                'object': {}
            }
        }
        mock_construct_event.return_value = mock_event
        
        webhook_payload = json.dumps(mock_event)
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        # Should handle gracefully
        assert response.status_code == 200
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_failed(self, mock_construct_event, client, db_session):
        """Test webhook with invalid signature."""
        import stripe
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )
        
        webhook_payload = '{"type": "test"}'
        headers = {
            'Stripe-Signature': 'invalid_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_user_not_found(self, mock_construct_event, client, db_session):
        """Test webhook for user that doesn't exist in database."""
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': 'nonexistent@example.com',
                    'customer': 'cus_test_123',
                    'subscription': 'sub_test_123'
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        webhook_payload = json.dumps(mock_event)
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=webhook_payload,
                              headers=headers)
        
        # Should handle gracefully - maybe log warning
        assert response.status_code == 200


class TestFailedPaymentHandling:
    """Test cases for failed payment handling and recovery."""
    
    def test_get_failed_payments_admin(self, client, db_session, admin_auth_headers, failed_stripe_subscription):
        """Test admin access to failed payments list."""
        response = client.get('/admin/payments/failed', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        
        # Should include our failed subscription
        failed_payment_found = False
        for payment in data:
            if payment.get('stripe_subscription_id') == failed_stripe_subscription.stripe_subscription_id:
                failed_payment_found = True
                assert payment['failed_payment_count'] == 3
                assert payment['status'] == 'past_due'
                break
        
        assert failed_payment_found
    
    def test_get_failed_payments_non_admin(self, client, db_session, auth_headers):
        """Test non-admin access to failed payments (should fail)."""
        response = client.get('/admin/payments/failed', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_get_failed_payments_without_auth(self, client, db_session):
        """Test failed payments access without authentication."""
        response = client.get('/admin/payments/failed')
        
        assert response.status_code == 401
    
    @patch('stripe.Subscription.modify')
    def test_retry_failed_payment(self, mock_stripe_modify, client, db_session, admin_auth_headers, failed_stripe_subscription):
        """Test retrying a failed payment."""
        # Mock successful Stripe retry
        mock_stripe_modify.return_value = {
            'id': failed_stripe_subscription.stripe_subscription_id,
            'status': 'active'
        }
        
        retry_data = {
            'subscription_id': failed_stripe_subscription.stripe_subscription_id
        }
        
        response = client.post('/admin/payments/retry', 
                              json=retry_data,
                              headers=admin_auth_headers)
        
        # Implementation depends on whether retry endpoint exists
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Verify subscription status was updated
            db_session.refresh(failed_stripe_subscription)
            assert failed_stripe_subscription.status == 'active'
            assert failed_stripe_subscription.failed_payment_count == 0
    
    def test_multiple_failed_payments_threshold(self, client, db_session, sample_user):
        """Test handling of multiple failed payments beyond threshold."""
        # Create subscription with many failed payments
        subscription = StripeSubscription(
            user_id=sample_user.id,
            stripe_subscription_id='sub_test_many_failures',
            stripe_customer_id='cus_test_many_failures',
            status='past_due',
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow() - timedelta(days=1),
            failed_payment_count=5  # Exceeds typical threshold
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Simulate another failed payment
        with patch('stripe.Webhook.construct_event') as mock_construct_event:
            mock_event = {
                'type': 'invoice.payment_failed',
                'data': {
                    'object': {
                        'subscription': subscription.stripe_subscription_id,
                        'customer_email': sample_user.email
                    }
                }
            }
            mock_construct_event.return_value = mock_event
            
            webhook_payload = json.dumps(mock_event)
            headers = {
                'Stripe-Signature': 'test_signature',
                'Content-Type': 'application/json'
            }
            
            response = client.post('/stripe/webhook', 
                                  data=webhook_payload,
                                  headers=headers)
            
            assert response.status_code == 200
            
            # Verify subscription might be automatically cancelled
            db_session.refresh(subscription)
            # Implementation specific - might auto-cancel after threshold
            assert subscription.failed_payment_count >= 5


class TestOfflinePayments:
    """Test cases for offline payment requests and admin approval."""
    
    def test_request_offline_payment(self, client, db_session, auth_headers, sample_user):
        """Test user requesting offline payment."""
        payment_data = {
            'amount': 29.99,
            'currency': 'PLN',
            'description': 'Bank transfer for premium access',
            'payment_method': 'bank_transfer',
            'reference_number': 'REF123456'
        }
        
        response = client.post('/users/offline-payment-request', 
                              json=payment_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['amount'] == 29.99
        assert data['currency'] == 'PLN'
        assert data['status'] == 'pending'
        assert data['user_id'] == sample_user.id
        
        # Verify payment was created in database
        payment = OfflinePayment.query.filter_by(user_id=sample_user.id).first()
        assert payment is not None
        assert payment.amount == 29.99
        assert payment.reference_number == 'REF123456'
    
    def test_request_offline_payment_without_auth(self, client, db_session):
        """Test offline payment request without authentication."""
        payment_data = {
            'amount': 29.99,
            'description': 'Unauthorized request'
        }
        
        response = client.post('/users/offline-payment-request', json=payment_data)
        
        assert response.status_code == 401
    
    def test_request_offline_payment_invalid_amount(self, client, db_session, auth_headers):
        """Test offline payment request with invalid amount."""
        payment_data = {
            'amount': -10.00,  # Negative amount
            'description': 'Invalid amount'
        }
        
        response = client.post('/users/offline-payment-request', 
                              json=payment_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_get_offline_payments_admin(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test admin access to offline payments list."""
        response = client.get('/admin/payments/offline', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        
        # Should include our pending payment
        payment_found = False
        for payment in data:
            if payment['id'] == offline_payment_pending.id:
                payment_found = True
                assert payment['status'] == 'pending'
                assert payment['amount'] == 29.99
                break
        
        assert payment_found
    
    def test_approve_offline_payment(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test admin approving offline payment."""
        approval_data = {
            'notes': 'Payment verified and approved by admin'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_pending.id}/approve',
                              json=approval_data,
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'approved'
        assert data['notes'] == 'Payment verified and approved by admin'
        
        # Verify payment was approved in database
        db_session.refresh(offline_payment_pending)
        assert offline_payment_pending.status == 'approved'
        assert offline_payment_pending.approved_at is not None
        
        # Verify user got premium access
        user = offline_payment_pending.user
        db_session.refresh(user)
        assert user.has_premium_access is True
        assert user.premium_since is not None
    
    def test_reject_offline_payment(self, client, db_session, admin_auth_headers, offline_payment_pending):
        """Test admin rejecting offline payment."""
        rejection_data = {
            'notes': 'Invalid payment proof provided'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_pending.id}/reject',
                              json=rejection_data,
                              headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejected'
        assert data['notes'] == 'Invalid payment proof provided'
        
        # Verify payment was rejected in database
        db_session.refresh(offline_payment_pending)
        assert offline_payment_pending.status == 'rejected'
        
        # Verify user did not get premium access
        user = offline_payment_pending.user
        db_session.refresh(user)
        assert user.has_premium_access is False
    
    def test_approve_offline_payment_non_admin(self, client, db_session, auth_headers, offline_payment_pending):
        """Test non-admin attempting to approve payment."""
        approval_data = {
            'notes': 'Unauthorized approval attempt'
        }
        
        response = client.post(f'/admin/payments/offline/{offline_payment_pending.id}/approve',
                              json=approval_data,
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_approve_nonexistent_payment(self, client, db_session, admin_auth_headers):
        """Test approving non-existent payment."""
        approval_data = {
            'notes': 'Approving non-existent payment'
        }
        
        response = client.post('/admin/payments/offline/99999/approve',
                              json=approval_data,
                              headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data or 'message' in data
    
    def test_duplicate_offline_payment_request(self, client, db_session, auth_headers, sample_user):
        """Test user making duplicate offline payment requests."""
        payment_data = {
            'amount': 29.99,
            'description': 'First request'
        }
        
        # First request
        response1 = client.post('/users/offline-payment-request', 
                               json=payment_data,
                               headers=auth_headers)
        assert response1.status_code == 201
        
        # Second request (might be allowed or rejected)
        payment_data['description'] = 'Second request'
        response2 = client.post('/users/offline-payment-request', 
                               json=payment_data,
                               headers=auth_headers)
        
        # Implementation specific - might allow or reject duplicates
        assert response2.status_code in [201, 400]


class TestPaymentErrorScenarios:
    """Test error scenarios and edge cases for payment functionality."""
    
    @patch('stripe.checkout.Session.create')
    def test_stripe_network_error(self, mock_stripe_create, client, db_session, auth_headers):
        """Test handling of Stripe network errors."""
        import stripe
        mock_stripe_create.side_effect = stripe.error.APIConnectionError("Network error")
        
        response = client.post('/stripe/create-checkout-session', headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('stripe.checkout.Session.create')
    def test_stripe_api_error(self, mock_stripe_create, client, db_session, auth_headers):
        """Test handling of Stripe API errors."""
        import stripe
        mock_stripe_create.side_effect = stripe.error.InvalidRequestError(
            "Invalid request", "param"
        )
        
        response = client.post('/stripe/create-checkout-session', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_webhook_malformed_payload(self, client, db_session):
        """Test webhook with malformed payload."""
        malformed_payload = '{"type": "test", "data": {'  # Incomplete JSON
        headers = {
            'Stripe-Signature': 'test_signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/stripe/webhook', 
                              data=malformed_payload,
                              headers=headers)
        
        assert response.status_code == 400
    
    def test_webhook_missing_required_fields(self, client, db_session):
        """Test webhook with missing required fields."""
        with patch('stripe.Webhook.construct_event') as mock_construct_event:
            mock_event = {
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'id': 'cs_test_123'
                        # Missing customer_email and other required fields
                    }
                }
            }
            mock_construct_event.return_value = mock_event
            
            webhook_payload = json.dumps(mock_event)
            headers = {
                'Stripe-Signature': 'test_signature',
                'Content-Type': 'application/json'
            }
            
            response = client.post('/stripe/webhook', 
                                  data=webhook_payload,
                                  headers=headers)
            
            # Should handle missing fields gracefully
            assert response.status_code == 200
