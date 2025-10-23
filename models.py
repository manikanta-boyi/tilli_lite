from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize SQLAlchemy instance globally
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User Model: Stores customer and admin/employee authentication details.
    Leverages Flask-Login.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer') # 'customer' or 'admin'
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    
    # Relationships
    account = db.relationship('Account', back_populates='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

class Account(db.Model):
    """
    Account Model (tilliX Core): Stores primary customer service information.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    billing_address = db.Column(db.String(256))
    
    # Nudge Feature: Stores the customer's preferred communication channel
    comm_preference = db.Column(db.String(10), default='Email') # 'Email' or 'SMS'

    # Relationships
    user = db.relationship('User', back_populates='account', uselist=False)
    bills = db.relationship('Bill', backref='account', lazy='dynamic')
    comms = db.relationship('CommunicationLog', backref='account', lazy='dynamic')
    requests = db.relationship('Request', backref='account', lazy='dynamic') # New: for Service Requests

    def __repr__(self):
        return f'<Account {self.account_number}>'

class Bill(db.Model):
    """
    Bill Model (tilliX Core): Tracks amounts owed by the customer.
    Modified to track original amount and remaining balance for Monay partial payments.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    
    # Original amount billed
    original_amount = db.Column(db.Float, nullable=False)
    # The remaining amount owed (this changes with payments)
    amount_due = db.Column(db.Float, nullable=False) 
    
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Unpaid') # 'Unpaid', 'Partial', 'Paid'

    # Relationships
    transactions = db.relationship('PaymentTransaction', backref='bill', lazy='dynamic')

    def __repr__(self):
        return f'<Bill {self.id} - ${self.amount_due}>'

class PaymentTransaction(db.Model):
    """
    PaymentTransaction Model (Monay): Logs simulated payment attempts.
    """
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Success') # 'Success' or 'Failed'

    # Relationship to Account (for easy querying)
    account_fk = db.relationship('Account', foreign_keys=[account_id])
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.status}>'

class CommunicationLog(db.Model):
    """
    CommunicationLog Model (Nudge): Simulates outbound messages based on events.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    trigger_event = db.Column(db.String(50)) # e.g., 'Bill Issued', 'Payment Success'
    channel = db.Column(db.String(10)) # e.g., 'Email', 'SMS'
    message_body = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Nudge {self.trigger_event} via {self.channel}>'

class Request(db.Model):
    """
    Request Model (tilliX/Admin): Tracks customer service requests.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False) # e.g., 'Move-In', 'Billing Dispute'
    description = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='New') # 'New', 'In Progress', 'Closed'
    
    def __repr__(self):
        return f'<Request {self.id} - {self.request_type}>'