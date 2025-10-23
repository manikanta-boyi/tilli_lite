from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from models import User

class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """User registration form (for initial customer setup)."""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UpdateProfileForm(FlaskForm):
    """tilliX: Form for customer to update profile and communication preferences."""
    full_name = StringField('Full Name', validators=[DataRequired()])
    billing_address = StringField('Billing Address', validators=[DataRequired()])
    # Nudge Preference
    comm_preference = SelectField('Preferred Communication', choices=[
        ('Email', 'Email'), 
        ('SMS', 'SMS')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class PayBillForm(FlaskForm):
    """Monay: Simulated payment form."""
    # Amount to pay now. Validator ensures it's positive.
    amount_to_pay = FloatField('Amount to Pay ($)', validators=[
        DataRequired(), 
        NumberRange(min=0.01, message='Amount must be greater than zero.')
    ])
    
    # Simulated Payment Card/Method
    simulated_card = StringField('Simulated Card Number', validators=[
        DataRequired(), 
        Length(min=16, max=16, message='Must be 16 digits for simulation')
    ])
    
    payment_method_type = SelectField('Payment Type', choices=[
        ('Visa', 'Visa (Simulated)'), 
        ('MasterCard', 'MasterCard (Simulated)'),
        ('ACH', 'ACH Transfer (Simulated)')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Complete Simulated Payment')

# --- NEW FORM FOR SERVICE REQUESTS (tilliX) ---
class ServiceRequestForm(FlaskForm):
    """tilliX: Form for customer to submit service requests."""
    request_type = SelectField('Request Type', choices=[
        ('Billing Dispute', 'Billing Dispute'), 
        ('Move-In/Move-Out', 'Move-In/Move-Out'),
        ('Meter Reading Issue', 'Meter Reading Issue'),
        ('General Inquiry', 'General Inquiry')
    ], validators=[DataRequired()])
    description = TextAreaField('Detailed Description', validators=[
        DataRequired(), 
        Length(max=500, message='Description must be less than 500 characters.')
    ])
    submit = SubmitField('Submit Request')


# --- NEW FORM FOR ADMIN USE ---
class AdminBillForm(FlaskForm):
    """Admin: Form for creating new bills."""
    account_number = StringField('Account Number', validators=[DataRequired()])
    original_amount = FloatField('Original Amount Billed ($)', validators=[
        DataRequired(), 
        NumberRange(min=0.01, message='Amount must be positive.')
    ])
    # Changed label for better clarity
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    
    # *** IMPORTANT ADDITION: Field to track the admin user for logging ***
    admin_username = StringField('Admin Username (Logging)', validators=[DataRequired()])
    
    submit = SubmitField('Create Bill')
    
    pass