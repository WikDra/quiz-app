"""OfflinePayment model definition."""

from ..extensions import db
from datetime import datetime


class OfflinePayment(db.Model):
    """Model for tracking offline payments approved by admin"""
    __tablename__ = 'offline_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='PLN')
    description = db.Column(db.Text, nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    payment_method = db.Column(db.String(50), nullable=True)  # cash, bank_transfer, etc.
    reference_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='offline_payments')
    admin = db.relationship('User', foreign_keys=[admin_id])
    
    def approve_payment(self, admin_notes=None):
        """Approve the offline payment"""
        self.status = 'approved'
        self.approved_at = datetime.utcnow()
        if admin_notes:
            self.notes = admin_notes
        
        # Grant premium access to user
        self.user.has_premium_access = True
        self.user.premium_since = datetime.utcnow()
    
    def reject_payment(self, admin_notes=None):
        """Reject the offline payment"""
        self.status = 'rejected'
        if admin_notes:
            self.notes = admin_notes
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'user_name': self.user.username if self.user else None,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'admin_id': self.admin_id,
            'admin_name': self.admin.username if self.admin else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }
