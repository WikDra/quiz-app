"""
Admin controller for managing administrative functions
"""
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from .models import User, OfflinePayment, StripeSubscription, Quiz, Payment, db
from .admin_middleware import get_current_admin_user
from datetime import datetime, timedelta

class AdminController:
    
    @staticmethod

    def get_dashboard_stats():
        """Get admin dashboard statistics"""
        try:
            # User statistics
            total_users = User.query.count()
            admin_users = User.query.filter_by(role='admin').count()
            premium_users = User.query.filter_by(has_premium_access=True).count()
            
            # Quiz statistics
            total_quizzes = Quiz.query.count()
            
            # Payment statistics
            pending_offline_payments = OfflinePayment.query.filter_by(status='pending').count()
            approved_offline_payments = OfflinePayment.query.filter_by(status='approved').count()
            active_subscriptions = StripeSubscription.query.filter_by(status='active').count()
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_users_this_month = User.query.filter(User.created_at >= thirty_days_ago).count()
            
            return {
                'stats': {
                    'users': {
                        'total': total_users,
                        'admins': admin_users,
                        'premium': premium_users,
                        'new_this_month': new_users_this_month
                    },
                    'quizzes': {
                        'total': total_quizzes
                    },
                    'payments': {
                        'pending_offline': pending_offline_payments,
                        'approved_offline': approved_offline_payments,
                        'active_subscriptions': active_subscriptions
                    }
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get dashboard stats: {str(e)}'}
    
    @staticmethod

    def get_users():
        """Get all users with pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', '')
            
            query = User.query
            
            # Search filter
            if search:
                query = query.filter(
                    db.or_(
                        User.username.contains(search),
                        User.email.contains(search),
                        User.fullName.contains(search)
                    )
                )
            
            # Pagination
            users = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'users': [user.to_dict() for user in users.items],
                'pagination': {
                    'page': page,
                    'pages': users.pages,
                    'per_page': per_page,
                    'total': users.total,
                    'has_next': users.has_next,
                    'has_prev': users.has_prev
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get users: {str(e)}'}
    
    @staticmethod

    def promote_user_to_admin(user_id):
        """Promote user to admin role"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            if user.role == 'admin':
                return {'error': 'User is already an admin'}
            
            user.promote_to_admin()
            db.session.commit()
            
            return {
                'message': f'User {user.username} promoted to admin successfully',
                'user': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to promote user: {str(e)}'}
    
    @staticmethod

    def demote_admin_to_user(user_id):
        """Demote admin to regular user"""
        try:
            admin_user = get_current_admin_user()
            target_user = User.query.get(user_id)
            
            if not target_user:
                return {'error': 'User not found'}
            
            if target_user.role != 'admin':
                return {'error': 'User is not an admin'}
            
            # Prevent self-demotion
            if admin_user.id == target_user.id:
                return {'error': 'Cannot demote yourself'}
            
            target_user.demote_to_user()
            db.session.commit()
            
            return {
                'message': f'Admin {target_user.username} demoted to user successfully',
                'user': target_user.to_dict()            }
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to demote user: {str(e)}'}
    
    @staticmethod
    def get_offline_payments():
        """Get all offline payments with pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', '')
            
            query = OfflinePayment.query
            
            # Status filter
            if status and status in ['pending', 'approved', 'rejected']:
                query = query.filter_by(status=status)
            
            # Order by most recent first
            query = query.order_by(OfflinePayment.created_at.desc())
            
            # Pagination
            payments = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'payments': [payment.to_dict() for payment in payments.items],
                'pagination': {
                    'page': page,
                    'pages': payments.pages,
                    'per_page': per_page,
                    'total': payments.total,
                    'has_next': payments.has_next,
                    'has_prev': payments.has_prev
                }
            }
        except Exception as e:
            return {'error': f'Failed to get offline payments: {str(e)}'}
    
    @staticmethod
    def create_offline_payment():
        """Create new offline payment (for testing purposes)"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['user_id', 'amount', 'evidence_text']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}
            
            user = User.query.get(data['user_id'])
            if not user:
                return {'error': 'User not found'}
            
            payment = OfflinePayment(
                user_id=data['user_id'],
                amount=float(data['amount']),
                evidence_text=data['evidence_text'],
                evidence_file_path=data.get('evidence_file_path'),
                admin_notes=data.get('admin_notes', ''),
                status='pending'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            return {
                'message': 'Offline payment created successfully',
                'payment': payment.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create offline payment: {str(e)}'}
    
    @staticmethod
    def approve_offline_payment(payment_id):
        """Approve offline payment and grant premium access"""
        try:
            admin_user = get_current_admin_user()
            payment = OfflinePayment.query.get(payment_id)
            
            if not payment:
                return {'error': 'Payment not found'}
            
            if payment.status != 'pending':
                return {'error': f'Payment is already {payment.status}'}
              # Approve payment
            payment.approve_payment()
            payment.admin_id = admin_user.id
                
            db.session.commit()
            
            # Return payment data directly for tests compatibility
            payment_data = payment.to_dict()
            payment_data['message'] = f'Payment approved and premium access granted to user {payment.user.username}'
            return payment_data
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to approve payment: {str(e)}'}
    
    @staticmethod
    def reject_offline_payment(payment_id):
        """Reject offline payment"""
        try:
            admin_user = get_current_admin_user()
            payment = OfflinePayment.query.get(payment_id)
            
            if not payment:
                return {'error': 'Payment not found'}
            
            if payment.status != 'pending':
                return {'error': f'Payment is already {payment.status}'}
              # Get rejection reason from request
            data = request.get_json() or {}
            rejection_reason = data.get('reason', 'No reason provided')
              # Reject payment
            payment.reject_payment(rejection_reason)
            payment.admin_id = admin_user.id
            db.session.commit()
            
            # Return payment data directly for tests compatibility
            payment_data = payment.to_dict()
            payment_data['message'] = 'Payment rejected successfully'
            return payment_data
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to reject payment: {str(e)}'}

    @staticmethod
    def update_user(user_id):
        """Update user information"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}
            
            # Update allowed fields
            allowed_fields = ['username', 'email', 'fullName', 'role', 'has_premium_access']
            updated_fields = []
            
            for field in allowed_fields:
                if field in data:
                    if hasattr(user, field):
                        old_value = getattr(user, field)
                        new_value = data[field]
                        
                        # Special validation for email
                        if field == 'email' and new_value != old_value:
                            existing_user = User.query.filter_by(email=new_value).first()
                            if existing_user and existing_user.id != user_id:
                                return {'error': 'Email already exists'}
                        
                        # Special validation for username
                        if field == 'username' and new_value != old_value:
                            existing_user = User.query.filter_by(username=new_value).first()
                            if existing_user and existing_user.id != user_id:
                                return {'error': 'Username already exists'}
                        
                        setattr(user, field, new_value)
                        updated_fields.append(field)
            
            if updated_fields:
                db.session.commit()
                return {
                    'message': f'User updated successfully. Updated fields: {", ".join(updated_fields)}',
                    'user': user.to_dict()
                }
            else:
                return {'message': 'No changes made', 'user': user.to_dict()}
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update user: {str(e)}'}
    
    @staticmethod

    def get_failed_payments():
        """Get failed Stripe payments for admin dashboard"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            # Get failed payments from Payment model
            query = Payment.query.filter_by(status='failed')
            
            # Get failed subscriptions
            failed_subscriptions = StripeSubscription.query.filter(
                StripeSubscription.status.in_(['past_due', 'canceled']),
                StripeSubscription.failed_payment_count > 0
            ).all()
            
            # Order by most recent first
            query = query.order_by(Payment.id.desc())
            
            # Pagination
            payments = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'failed_payments': [
                    {
                        'id': payment.id,
                        'stripe_payment_intent_id': payment.stripe_payment_intent_id,
                        'amount': payment.amount,
                        'status': payment.status,
                        'type': 'payment_intent'
                    } for payment in payments.items
                ],                'failed_subscriptions': [
                    {
                        'id': sub.id,
                        'stripe_subscription_id': sub.stripe_subscription_id,
                        'user_id': sub.user_id,
                        'user_email': sub.user.email if sub.user else None,
                        'user_name': sub.user.username if sub.user else None,
                        'status': sub.status,
                        'failed_payment_count': sub.failed_payment_count,
                        'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
                        'type': 'subscription'
                    } for sub in failed_subscriptions
                ],
                'pagination': {
                    'page': page,
                    'pages': payments.pages,
                    'per_page': per_page,
                    'total': payments.total,
                    'has_next': payments.has_next,
                    'has_prev': payments.has_prev
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get failed payments: {str(e)}'}
