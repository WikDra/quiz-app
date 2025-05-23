from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import stripe
import os
from datetime import datetime, timedelta

from app import db
from app.models.user import User

stripe_bp = Blueprint('stripe', __name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@stripe_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for premium subscription"""
    try:
        data = request.get_json()
        price_id = data.get('price_id')  # This should come from frontend
        
        if not price_id:
            return jsonify({
                'success': False,
                'message': 'Brak ID cennika'
            }), 400
        
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    'user_id': current_user.id,
                    'username': current_user.username
                }
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}/premium",
            metadata={
                'user_id': current_user.id
            }
        )
        
        return jsonify({
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'message': f'Błąd Stripe: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas tworzenia sesji płatności: {str(e)}'
        }), 500

@stripe_bp.route('/verify-session/<session_id>', methods=['GET'])
@login_required
def verify_session(session_id):
    """Verify Stripe checkout session and activate premium"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid' and session.metadata.get('user_id') == str(current_user.id):
            # Activate premium for user
            current_user.is_premium = True
            current_user.premium_expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days premium
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Premium zostało aktywowane',
                'user': current_user.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Płatność nie została zrealizowana'
            }), 400
            
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'message': f'Błąd Stripe: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas weryfikacji płatności: {str(e)}'
        }), 500

@stripe_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_successful_subscription_payment(invoice)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancellation(subscription)
    
    return jsonify({'status': 'success'})

def handle_successful_payment(session):
    """Handle successful one-time payment"""
    try:
        user_id = session.get('metadata', {}).get('user_id')
        if user_id:
            user = User.query.get(int(user_id))
            if user:
                user.is_premium = True
                user.premium_expires_at = datetime.utcnow() + timedelta(days=30)
                db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error handling successful payment: {str(e)}")

def handle_successful_subscription_payment(invoice):
    """Handle successful subscription payment"""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Extend premium by 30 days from current expiration or now
            if user.premium_expires_at and user.premium_expires_at > datetime.utcnow():
                user.premium_expires_at += timedelta(days=30)
            else:
                user.premium_expires_at = datetime.utcnow() + timedelta(days=30)
            
            user.is_premium = True
            db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error handling subscription payment: {str(e)}")

def handle_subscription_cancellation(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Don't immediately remove premium, let it expire naturally
            # user.is_premium = False
            # user.premium_expires_at = None
            # db.session.commit()
            pass
    except Exception as e:
        current_app.logger.error(f"Error handling subscription cancellation: {str(e)}")

@stripe_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        if not current_user.stripe_customer_id:
            return jsonify({
                'success': False,
                'message': 'Brak aktywnej subskrypcji'
            }), 400
        
        # Get customer's subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status='active'
        )
        
        if not subscriptions.data:
            return jsonify({
                'success': False,
                'message': 'Brak aktywnej subskrypcji'
            }), 400
        
        # Cancel the first active subscription
        subscription = subscriptions.data[0]
        stripe.Subscription.delete(subscription.id)
        
        return jsonify({
            'success': True,
            'message': 'Subskrypcja została anulowana'
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'message': f'Błąd Stripe: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas anulowania subskrypcji: {str(e)}'
        }), 500

@stripe_bp.route('/subscription-status', methods=['GET'])
@login_required
def get_subscription_status():
    """Get user's subscription status"""
    try:
        if not current_user.stripe_customer_id:
            return jsonify({
                'success': True,
                'has_subscription': False,
                'is_premium': current_user.is_premium,
                'premium_expires_at': current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None
            })
        
        # Get customer's subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status='active'
        )
        
        return jsonify({
            'success': True,
            'has_subscription': len(subscriptions.data) > 0,
            'is_premium': current_user.is_premium,
            'premium_expires_at': current_user.premium_expires_at.isoformat() if current_user.premium_expires_at else None,
            'subscription_count': len(subscriptions.data)
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'message': f'Błąd Stripe: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas sprawdzania statusu subskrypcji: {str(e)}'
        }), 500
