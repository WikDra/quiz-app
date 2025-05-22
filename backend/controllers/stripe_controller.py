import stripe
import os
import json
from datetime import datetime
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db  # Assuming your db instance is here
from models.user import User

class StripeController:
    @staticmethod
    @jwt_required()
    def create_checkout_session():
        try:
            data = request.get_json()
            price_id = data.get('priceId') # e.g., price_12345abc or your actual Price ID from Stripe
            if not price_id:
                return jsonify({'error': 'Price ID is required'}), 400

            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                current_app.logger.warning(f"User not found for ID: {user_id} during checkout session creation.")
                return jsonify({'error': 'User not found'}), 404

            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            if not frontend_url:
                current_app.logger.error("FRONTEND_URL is not set in environment variables.")
                # Fallback or error, depending on desired behavior
                # For now, let's assume a default or handle it as an error if critical
                # return jsonify({'error': 'Application configuration error: FRONTEND_URL not set.'}), 500

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription', # ZMIANA: z 'payment' na 'subscription'
                success_url=f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}&subscription=true", # Dodano parametr subscription
                cancel_url=f"{frontend_url}/payment-cancelled",
                customer_email=user.email, # Przekazanie emaila użytkownika
                client_reference_id=str(user_id) # Przekazanie ID użytkownika do śledzenia
            )
            current_app.logger.info(f"Checkout session created for user {user_id} with session ID {checkout_session.id}")
            return jsonify({'id': checkout_session.id})

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe API error during checkout session creation: {str(e)}")
            return jsonify({'error': f'Stripe error: {e.user_message or str(e)}'}), 400
        except Exception as e:
            current_app.logger.error(f"Unexpected error during checkout session creation: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500    @staticmethod
    def handle_webhook():          
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        is_development = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'
          # Check if we have a real Stripe webhook secret
        if not endpoint_secret or endpoint_secret.startswith('whsec_test_') or endpoint_secret == 'whsec_trudny_webhook_secret' or endpoint_secret.endswith('_webhook_secret'):
            # This looks like a placeholder or test value
            current_app.logger.error(f"Found placeholder webhook secret: '{endpoint_secret}'. Please use a real webhook secret from Stripe Dashboard.")
            
            if is_development:
                # In development environment, accept the webhook without verification
                current_app.logger.warning("Using test/placeholder webhook secret. Bypassing signature verification in development mode.")
                try:
                    event = json.loads(payload)
                    current_app.logger.info(f"Successfully parsed webhook payload in development mode: {event['type']}")
                    
                    # Log helpful information
                    current_app.logger.info(f"To fix this, please get a real webhook secret from your Stripe Dashboard")
                    current_app.logger.info(f"Then run: python -m backend.utils.update_webhook_secret")
                except Exception as e:
                    current_app.logger.error(f"Failed to parse webhook payload: {str(e)}")
                    return jsonify({'error': 'Invalid payload format'}), 400
            else:
                current_app.logger.error("Invalid webhook secret configuration in production.")
                return jsonify({'error': 'Webhook secret not properly configured'}), 500
        else:
            # Normal verification flow
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, endpoint_secret
                )
            except ValueError as e:
                # Invalid payload
                current_app.logger.error(f"Webhook ValueError: {str(e)}")
                return jsonify({'error': 'Invalid payload'}), 400
            except stripe.error.SignatureVerificationError as e:
                # Invalid signature
                current_app.logger.error(f"Webhook SignatureVerificationError: {str(e)}")
                return jsonify({'error': 'Invalid signature'}), 400
            except Exception as e:
                current_app.logger.error(f"Webhook general error: {str(e)}")
                return jsonify({'error': 'Webhook processing error'}), 400
            
        # Handle the event
        current_app.logger.info(f"Processing webhook event type: {event['type']}")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            current_app.logger.info(f"Checkout session completed: {session['id']}")
            
            client_reference_id = session.get('client_reference_id')
            customer_email = session.get('customer_details', {}).get('email')
            
            current_app.logger.debug(f"Webhook session data: client_reference_id={client_reference_id}, customer_email={customer_email}")
            
            # Grant premium access to the user after successful payment
            if client_reference_id:
                try:
                    # Try to convert client_reference_id to int since it might be stored as string
                    user_id = int(client_reference_id)
                    user = User.query.get(user_id)
                    if user:                        # Update the user's premium access status and force it to True
                        user.has_premium_access = True
                        # Record when premium was activated
                        if not user.premium_since:
                            user.premium_since = datetime.utcnow()
                        db.session.add(user)
                        db.session.commit()
                        current_app.logger.info(f"User {user.id} ({user.email}) granted premium access after successful payment.")
                    else:
                        current_app.logger.warning(f"User with client_reference_id {client_reference_id} not found after payment.")
                except (ValueError, TypeError) as e:
                    current_app.logger.error(f"Invalid client_reference_id format: {client_reference_id}, error: {str(e)}")                    # Try fallback to email lookup
                    if customer_email:
                        user = User.query.filter_by(email=customer_email).first()
                        if user:
                            user.has_premium_access = True
                            if not user.premium_since:
                                user.premium_since = datetime.utcnow()
                            db.session.add(user)
                            db.session.commit()
                            current_app.logger.info(f"User {user.id} ({user.email}) granted premium access (via email) after invalid reference ID.")
                        else:
                            current_app.logger.warning(f"User with email {customer_email} not found after payment with invalid reference ID.")
            elif customer_email:                # Fallback to email if client_reference_id is not available
                user = User.query.filter_by(email=customer_email).first()
                if user:
                    user.has_premium_access = True
                    if not user.premium_since:
                        user.premium_since = datetime.utcnow()
                    db.session.add(user)
                    db.session.commit()
                    current_app.logger.info(f"User {user.id} ({user.email}) granted premium access (via email) after successful payment.")
                else:
                    current_app.logger.warning(f"User with email {customer_email} not found after payment.")
            else:
                current_app.logger.warning("Could not identify user from checkout session.")
                
        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            current_app.logger.info(f"PaymentIntent succeeded: {payment_intent['id']}")
            # Handle successful payment intent if needed (e.g. for subscriptions, etc.)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            customer_id = subscription.get('customer')
            
            # Find the user related to this subscription 
            # First, try to get the customer details
            try:
                customer = stripe.Customer.retrieve(customer_id)
                customer_email = customer.get('email')
                
                if customer_email:
                    user = User.query.filter_by(email=customer_email).first()
                    if user:                        
                        user.has_premium_access = False
                        # We don't reset premium_since to allow tracking of past subscriptions
                        db.session.add(user)
                        db.session.commit()
                        current_app.logger.info(f"Premium access revoked for user {user.id} ({user.email}) due to subscription cancellation.")
                    else:
                        current_app.logger.warning(f"User with email {customer_email} not found during subscription cancellation.")
                else:
                    current_app.logger.warning(f"No email found for customer {customer_id} during subscription cancellation.")
            except Exception as e:
                current_app.logger.error(f"Error processing subscription cancellation for customer {customer_id}: {str(e)}")
        
        # Handle other subscription events if needed
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            current_app.logger.info(f"Subscription updated: {subscription['id']}")
            # Handle subscription updates (like changes in plan, etc.)
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            current_app.logger.warning(f"Invoice payment failed: {invoice['id']}")
            # Handle failed payments, maybe notify users or admins
            
        else:
            current_app.logger.info(f"Received unhandled webhook event type: {event['type']}")

        return jsonify({'status': 'success'}), 200

def register_stripe_routes(app):
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        app.logger.warning("STRIPE_SECRET_KEY is not set. Stripe functionality will not work.")

    app.add_url_rule('/api/stripe/create-checkout-session', 'create_checkout_session_route', StripeController.create_checkout_session, methods=['POST'])
    app.add_url_rule('/api/stripe/webhook', 'stripe_webhook_route', StripeController.handle_webhook, methods=['POST'])
