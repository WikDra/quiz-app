import stripe
import os
import json
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, StripeSubscription, _process_subscription_by_email

class StripeController:
    @staticmethod
    @jwt_required()
    def create_checkout_session():
        try:
            data = request.get_json()
            price_id = data.get('priceId')
            if not price_id:
                return jsonify({'error': 'Price ID is required'}), 400
                
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
                return jsonify({'error': 'User not found'}), 404

            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}&subscription=true",
                cancel_url=f"{frontend_url}/payment-cancelled",
                customer_email=user.email,
                client_reference_id=str(user.id)  # Use user.id instead of user_id to avoid large Google ID
            )
            current_app.logger.info(f"Checkout session created for user {user.id} with session ID {checkout_session.id}")
            return jsonify({'id': checkout_session.id})

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe API error during checkout session creation: {str(e)}")
            return jsonify({'error': f'Stripe error: {e.user_message or str(e)}'}), 400
        except Exception as e:
            current_app.logger.error(f"Unexpected error during checkout session creation: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500

    @staticmethod
    def handle_webhook():
        """Handle incoming webhook events from Stripe."""
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        is_development = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'

        # Verify webhook signature
        try:
            if not endpoint_secret or endpoint_secret.startswith('whsec_test_'):
                if is_development:
                    current_app.logger.warning("Using test webhook secret. Bypassing signature verification in development mode.")
                    event = json.loads(payload)
                else:
                    current_app.logger.error("Invalid webhook secret configuration in production.")
                    return jsonify({'error': 'Webhook secret not properly configured'}), 500
            else:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            current_app.logger.error(f"Webhook verification error: {str(e)}")
            return jsonify({'error': 'Invalid payload or signature'}), 400

        try:
            event_type = event['type']
            current_app.logger.info(f"Processing webhook event type: {event_type}")

            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                client_reference_id = session.get('client_reference_id')
                customer_email = session.get('customer_details', {}).get('email')
                
                current_app.logger.info(f"Processing completed checkout: {session['id']}")
                
                if client_reference_id:
                    try:
                        user_id = int(client_reference_id)
                        user = User.query.get(user_id)
                        if user:
                            subscription = StripeSubscription.query.filter_by(user_id=user.id).first()
                            
                            if not subscription:
                                subscription = StripeSubscription(
                                    user_id=user.id,
                                    stripe_customer_id=session.get('customer'),
                                    stripe_subscription_id=session.get('subscription'),
                                    status='active',
                                    current_period_start=datetime.utcnow(),
                                    current_period_end=datetime.utcnow() + timedelta(days=30)
                                )
                                db.session.add(subscription)
                            else:
                                subscription.status = 'active'
                                subscription.stripe_customer_id = session.get('customer')
                                subscription.stripe_subscription_id = session.get('subscription')
                                subscription.current_period_start = datetime.utcnow()
                                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                            
                            user.has_premium_access = True
                            if not user.premium_since:
                                user.premium_since = datetime.utcnow()
                            
                            db.session.commit()
                            current_app.logger.info(f"Subscription created/updated for user {user.id}")
                        else:
                            current_app.logger.warning(f"User with ID {user_id} not found")
                    except ValueError:
                        current_app.logger.error(f"Invalid client_reference_id: {client_reference_id}")
                        if customer_email:
                            _process_subscription_by_email(customer_email, session)
                elif customer_email:
                    _process_subscription_by_email(customer_email, session)
                else:
                    current_app.logger.warning("No client_reference_id or customer_email in session")

            elif event_type == 'customer.subscription.deleted':
                subscription_data = event['data']['object']
                subscription = StripeSubscription.query.filter_by(
                    stripe_subscription_id=subscription_data['id']
                ).first()
                
                if subscription:
                    subscription.status = 'canceled'
                    subscription.canceled_at = datetime.utcnow()
                    subscription.user.has_premium_access = False
                    db.session.commit()
                    current_app.logger.info(f"Subscription {subscription.id} canceled for user {subscription.user_id}")
                else:
                    current_app.logger.warning(f"Subscription not found: {subscription_data['id']}")

            elif event_type == 'customer.subscription.updated':
                subscription_data = event['data']['object']
                subscription = StripeSubscription.query.filter_by(
                    stripe_subscription_id=subscription_data['id']
                ).first()
                
                if subscription:
                    subscription.status = subscription_data['status']
                    subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
                    db.session.commit()
                    current_app.logger.info(f"Subscription {subscription.id} updated for user {subscription.user_id}")
                else:
                    current_app.logger.warning(f"Subscription not found: {subscription_data['id']}")

            elif event_type == 'invoice.payment_failed':
                invoice = event['data']['object']
                current_app.logger.warning(f"Invoice payment failed: {invoice['id']}")
                # TODO: Consider notifying user or admin about payment failure

        except Exception as e:
            current_app.logger.error(f"Error processing webhook {event_type}: {str(e)}")
            return jsonify({'error': 'Webhook processing error'}), 500

        return jsonify({'status': 'success'}), 200

def register_stripe_routes(app):
    """Register Stripe-related routes with the Flask app."""
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        app.logger.warning("STRIPE_SECRET_KEY is not set. Stripe functionality will not work.")

    # Register routes to match frontend expectations
    app.add_url_rule('/stripe/create-checkout-session', 'create_checkout_session_route', 
                     StripeController.create_checkout_session, methods=['POST'])
    app.add_url_rule('/stripe/webhook', 'stripe_webhook_route', 
                     StripeController.handle_webhook, methods=['POST'])
