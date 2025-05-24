import stripe
import os
import json
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, StripeSubscription, _process_subscription_by_email

class StripeCheckoutSessionResource(Resource):
    @jwt_required()
    def post(self):
        """Create Stripe checkout session"""
        try:
            data = request.get_json()
            price_id = data.get('priceId')
            if not price_id:
                return {'error': 'Price ID is required'}, 400
                
            user_id = get_jwt_identity()
            current_app.logger.info(f"Creating checkout session for user_id: {user_id}")
            
            # For OAuth users with Google ID, find user by google_id
            user = None
            try:
                # Try to convert to int to see if it's a regular user ID
                numeric_id = int(user_id)
                if numeric_id < 1000000000:  # Small number, likely regular user ID
                    user = User.query.get(numeric_id)
                else:
                    # Large number, likely Google ID - search by google_id as string
                    user = User.query.filter_by(google_id=user_id).first()
            except (ValueError, TypeError, OverflowError):
                # If conversion fails, try as Google ID string
                user = User.query.filter_by(google_id=user_id).first()
            
            # If still not found, try both fields
            if not user:
                user = User.query.filter_by(google_id=user_id).first()
                if not user:
                    try:
                        numeric_id = int(user_id)
                        user = User.query.get(numeric_id)
                    except (ValueError, TypeError, OverflowError):
                        pass

            if not user:
                current_app.logger.warning(f"User not found for ID: {user_id} during checkout session creation.")
                return {'error': 'User not found'}, 404

            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{frontend_url}/premium',                customer_email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'user_email': user.email
                }
            )
            
            current_app.logger.info(f"Checkout session created: {session.id} for user {user.email}")
            return {
                'sessionId': session.id,
                'url': session.url
            }, 200
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error during checkout session creation: {str(e)}")
            return {'error': f'Stripe error: {str(e)}'}, 400
        except Exception as e:
            current_app.logger.error(f"Error creating checkout session: {str(e)}")
            return {'error': 'Internal server error'}, 500

class StripeWebhookResource(Resource):
    def post(self):
        """Handle Stripe webhook events"""
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            current_app.logger.error(f"Invalid payload: {e}")
            return {'error': 'Invalid payload'}, 400        
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Invalid signature: {e}")
            return {'error': 'Invalid signature'}, 400

        event_type = event['type']
        current_app.logger.info(f"Received Stripe webhook: {event_type}")

        try:
            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                current_app.logger.info(f"Processing checkout session: {session['id']}")
                
                # Get customer email from session metadata or customer_email field
                customer_email = session.get('customer_email')
                metadata = session.get('metadata', {})
                
                # If no customer_email, try to get it from metadata
                if not customer_email and metadata.get('user_email'):
                    customer_email = metadata.get('user_email')
                
                if customer_email:
                    # Pass the entire session object to _process_subscription_by_email
                    _process_subscription_by_email(customer_email, session)
                    current_app.logger.info(f"Premium access granted to {customer_email}")
                else:
                    current_app.logger.warning(f"No customer email found in session {session['id']}")

            elif event_type == 'customer.subscription.updated':
                subscription = event['data']['object']
                current_app.logger.info(f"Processing subscription update: {subscription['id']}")
                
                customer_id = subscription.get('customer')
                subscription_id = subscription['id']
                status = subscription['status']
                
                if customer_id:
                    customer = stripe.Customer.retrieve(customer_id)
                    customer_email = customer.get('email')
                    
                    if customer_email:
                        _process_subscription_by_email(customer_email, subscription_id, status)
                        current_app.logger.info(f"Subscription {subscription_id} updated to {status} for {customer_email}")

            elif event_type == 'customer.subscription.deleted':
                subscription = event['data']['object']
                current_app.logger.info(f"Processing subscription deletion: {subscription['id']}")
                
                customer_id = subscription.get('customer')
                subscription_id = subscription['id']
                
                if customer_id:
                    customer = stripe.Customer.retrieve(customer_id)
                    customer_email = customer.get('email')
                    
                    if customer_email:
                        _process_subscription_by_email(customer_email, subscription_id, 'canceled')
                        current_app.logger.info(f"Premium access revoked for {customer_email}")

            elif event_type == 'invoice.payment_failed':
                invoice = event['data']['object']
                current_app.logger.warning(f"Invoice payment failed: {invoice['id']}")
                # TODO: Consider notifying user or admin about payment failure

        except Exception as e:
            current_app.logger.error(f"Error processing webhook {event_type}: {str(e)}")
            return {'error': 'Webhook processing error'}, 500

        return {'status': 'success'}, 200
