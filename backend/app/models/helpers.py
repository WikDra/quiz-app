"""Helper functions for payment processing."""

from .user import User
from .payment import StripeSubscription
from ..extensions import db
from flask import current_app
from datetime import datetime, timedelta


def _process_subscription_by_email(customer_email, session):
    """Helper function to process subscription by email"""
    user = User.query.filter_by(email=customer_email).first()
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
        current_app.logger.info(f"Subscription created/updated for user {user.id} (via email)")
    else:
        current_app.logger.warning(f"User with email {customer_email} not found after payment.")
