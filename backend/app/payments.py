import stripe
import os
import json
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from flask_restful import Resource
from .models import Payment, User, StripeSubscription, _process_subscription_by_email, db  

class CreatePaymentIntent(Resource):
    def post(self):
        data = request.json
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(data['amount']) * 100,  # Kwota w centach
                currency=data.get('currency', 'usd'),
                payment_method_types=["card"],
            )
            return {
                'client_secret': intent['client_secret'],
                'payment_intent_id': intent['id']
            }, 200
        except Exception as e:
            return {'error': str(e)}, 400

class StripeWebhook(Resource):
    def post(self):
        """Enhanced webhook handler that supports both payment intents and subscriptions"""
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        payload = request.get_data()
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

            # Handle subscription-related events (from stripe_controller.py)
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
                
                # Handle subscription payment failure
                subscription_id = invoice.get('subscription')
                customer_id = invoice.get('customer')
                
                if subscription_id:
                    subscription = StripeSubscription.query.filter_by(
                        stripe_subscription_id=subscription_id
                    ).first()
                    
                    if subscription:
                        # Mark subscription as past_due or failed
                        subscription.status = 'past_due'
                        subscription.failed_payment_count = (subscription.failed_payment_count or 0) + 1
                        
                        # If too many failed attempts, suspend premium access
                        if subscription.failed_payment_count >= 3:
                            subscription.status = 'canceled'
                            subscription.user.has_premium_access = False
                            current_app.logger.error(f"Subscription {subscription.id} canceled after 3 failed payments")
                        
                        db.session.commit()
                        current_app.logger.info(f"Subscription {subscription.id} marked as past_due due to payment failure")
                    else:
                        current_app.logger.warning(f"Subscription not found for failed payment: {subscription_id}")
            
            elif event_type == 'payment_intent.payment_failed':
                intent = event['data']['object']
                current_app.logger.warning(f"Payment intent failed: {intent['id']}")
                
                # Update payment record if it exists
                payment = Payment.query.filter_by(
                    stripe_payment_intent_id=intent['id']
                ).first()
                
                if payment:
                    payment.status = 'failed'
                    db.session.commit()
                    current_app.logger.info(f"Payment {payment.id} marked as failed")
                else:
                    # Create failed payment record for tracking
                    amount = intent['amount'] / 100
                    payment = Payment(
                        stripe_payment_intent_id=intent['id'],
                        amount=amount,
                        status='failed'
                    )
                    db.session.add(payment)
                    db.session.commit()
                    current_app.logger.info(f"Failed payment record created: {intent['id']}")

            # Handle payment intent events (original functionality)
            elif event_type == 'payment_intent.succeeded':
                intent = event['data']['object']
                amount = intent['amount'] / 100

                # Save payment to database
                payment = Payment(
                    stripe_payment_intent_id=intent['id'],
                    amount=amount,
                    status='succeeded'
                )
                db.session.add(payment)
                db.session.commit()
                current_app.logger.info(f"Payment saved: {intent['id']}")

        except Exception as e:
            current_app.logger.error(f"Error processing webhook {event_type}: {str(e)}")
            return jsonify({'error': 'Webhook processing error'}), 500

        return jsonify({'status': 'success'}), 200