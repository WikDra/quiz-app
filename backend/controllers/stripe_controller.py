import stripe
import os
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
                client_reference_id=user_id # Przekazanie ID użytkownika do śledzenia
            )
            current_app.logger.info(f"Checkout session created for user {user_id} with session ID {checkout_session.id}")
            return jsonify({'id': checkout_session.id})

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe API error during checkout session creation: {str(e)}")
            return jsonify({'error': f'Stripe error: {e.user_message or str(e)}'}), 400
        except Exception as e:
            current_app.logger.error(f"Unexpected error during checkout session creation: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500

    @staticmethod
    def handle_webhook():
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

        if not endpoint_secret:
            current_app.logger.error("STRIPE_WEBHOOK_SECRET is not set.")
            return jsonify({'error': 'Webhook secret not configured'}), 500

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
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            current_app.logger.info(f"Checkout session completed: {session['id']}")
            
            client_reference_id = session.get('client_reference_id')
            customer_email = session.get('customer_details', {}).get('email')

            # Add your business logic here
            # For example, find the user and update their subscription status or grant access
            if client_reference_id:
                user = User.query.get(client_reference_id)
                if user:
                    # Example: Add a custom field to your User model like `has_premium_access`
                    # user.has_premium_access = True 
                    # db.session.add(user)
                    # db.session.commit()
                    current_app.logger.info(f"User {user.id} ({user.email}) granted access after successful payment.")
                else:
                    current_app.logger.warning(f"User with client_reference_id {client_reference_id} not found after payment.")
            elif customer_email:
                # Fallback to email if client_reference_id is not available
                user = User.query.filter_by(email=customer_email).first()
                if user:
                    # user.has_premium_access = True
                    # db.session.add(user)
                    # db.session.commit()
                    current_app.logger.info(f"User {user.id} ({user.email}) granted access (via email) after successful payment.")
                else:
                    current_app.logger.warning(f"User with email {customer_email} not found after payment.")
            else:
                current_app.logger.warning("Could not identify user from checkout session.")

        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            current_app.logger.info(f"PaymentIntent succeeded: {payment_intent['id']}")
            # Handle successful payment intent if needed (e.g. for subscriptions, etc.)

        else:
            current_app.logger.info(f"Received unhandled webhook event type: {event['type']}")

        return jsonify({'status': 'success'}), 200

def register_stripe_routes(app):
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        app.logger.warning("STRIPE_SECRET_KEY is not set. Stripe functionality will not work.")

    app.add_url_rule('/api/stripe/create-checkout-session', 'create_checkout_session_route', StripeController.create_checkout_session, methods=['POST'])
    app.add_url_rule('/api/stripe/webhook', 'stripe_webhook_route', StripeController.handle_webhook, methods=['POST'])
