from flask import Blueprint, render_template, redirect, url_for, flash, request as flask_request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash # Import generate_password_hash
# Added 'time' for combining date objects
from datetime import datetime, date, time 
from functools import wraps 
# Ensure all new models and forms are imported:
from models import db, User, Account, Bill, PaymentTransaction, CommunicationLog, Request 
from forms import LoginForm, RegistrationForm, UpdateProfileForm, PayBillForm, ServiceRequestForm, AdminBillForm # Import RegistrationForm

# Define the Blueprint for the main application
bp = Blueprint('main', __name__)

# --- Custom Decorator for Admin Access (Platform Feature) ---
def admin_required(f):
    """Custom decorator to restrict access to admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions (Simulating Monay & Nudge Logic) ---

def simulate_payment_and_nudge(bill_id, account, amount, method):
    """
    Simulates Monay (Payment) and triggers Nudge (Communication).
    Handles partial payments and updates bill status accordingly.
    """
    bill = Bill.query.get(bill_id)
    if not bill:
        return False
    
    # 1. Monay Simulation: Record Transaction
    transaction = PaymentTransaction(
        bill_id=bill_id,
        account_id=account.id,
        amount_paid=amount,
        payment_method=method,
        status='Success' 
    )
    db.session.add(transaction)
    
    # 2. Monay Simulation: Update Bill Status (Partial Payment Logic)
    
    # Calculate new amount due
    bill.amount_due -= amount
    
    # Update status based on remaining balance
    if bill.amount_due <= 0.01: # Use small tolerance for float comparison
        bill.amount_due = 0.00 # Ensure it's exactly zero
        bill.status = 'Paid'
        event = 'Payment Success - Full'
        message = f"Your full payment of ${amount:.2f} for Bill #{bill.id} has been processed. Account balance is now $0.00. Thank you!"
    else:
        # If balance remains, status is 'Partial'
        bill.status = 'Partial'
        event = 'Payment Success - Partial'
        message = f"Your partial payment of ${amount:.2f} has been processed. Remaining balance: ${bill.amount_due:.2f}."

    # 3. Nudge Simulation: Log Communication
    comm_log = CommunicationLog(
        account_id=account.id,
        trigger_event=event,
        channel=account.comm_preference, # Respecting user preference
        message_body=message
    )
    db.session.add(comm_log)
    db.session.commit()
    
    return True

def nudge_new_bill(account, bill, admin_username):
    """Triggers Nudge alert when a new bill is created (Admin function) and logs the admin."""
    message = f"A new bill (ID: {bill.id}) of ${bill.original_amount:.2f} has been issued with a due date of {bill.due_date.strftime('%Y-%m-%d')}. Created by Admin: {admin_username}. View and pay now!"
    comm_log = CommunicationLog(
        account_id=account.id,
        trigger_event='New Bill Issued',
        channel=account.comm_preference,
        message_body=message
    )
    db.session.add(comm_log)
    db.session.commit()
    return True
# --- Authentication Routes ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard')) # Redirect Admin here
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('main.login'))
        login_user(user)
        flash('Logged in successfully.', 'success')
        # Check role after login
        if user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=form, title='Sign In')

# --- NEW: Registration Route for New Customers ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # 1. Create the new Account (tilliX Core)
        last_account = Account.query.order_by(Account.id.desc()).first()
        new_account_number = f"A-{int(last_account.account_number.split('-')[1]) + 1:06}" if last_account else 'A-000001'
        
        account = Account(
            account_number=new_account_number,
            full_name=form.full_name.data,
            billing_address='Pending Setup', # Requires update post-registration
            comm_preference='Email' 
        )
        db.session.add(account)
        db.session.flush() # Flush to get the new account.id
        
        # 2. Create the User (Flask-Login)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='customer',
            account_id=account.id
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    # 🐞 ADD THIS LOGIC for debugging form issues
    elif form.errors:
        print(f"Registration validation failed. Errors: {form.errors}")
    
    return render_template('register.html', title='Register New Account', form=form)
# --- End Registration Route ---

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- tilliX (Customer Portal) & Core App Routes ---

@bp.route('/')
def index():
    # Index page no longer displays demo credentials
    return render_template('index.html', title='Welcome')

# --- NEW: About Route ---
@bp.route('/about')
def about():
    return render_template('about.html', title='About tilliX')
# --- End About Route ---

@bp.route('/dashboard')
@login_required
def dashboard():
    # Only allow customers to access the full tilliX dashboard
    if current_user.role != 'customer' or current_user.account is None:
        flash("Access Denied: Only customer accounts have a dedicated dashboard.", 'danger')
        # Redirect admins to their page, others to index
        if current_user.role == 'admin':
             return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.index'))
    
    account = current_user.account
    # Fetch data relevant to the tilliX dashboard
    bills = Bill.query.filter_by(account_id=account.id).order_by(Bill.issue_date.desc()).all()
    # Note: Status is now 'Unpaid' or 'Partial' for outstanding bills
    unpaid_bills = [b for b in bills if b.status in ('Unpaid', 'Partial')]
    total_due = sum(b.amount_due for b in unpaid_bills)

    # Nudge Log: Show the last 5 communications for the customer
    comms = CommunicationLog.query.filter_by(account_id=account.id).order_by(CommunicationLog.timestamp.desc()).limit(5).all()
    
    # Requests: Show active requests for the customer
    requests = Request.query.filter_by(account_id=account.id).filter(Request.status != 'Closed').order_by(Request.submission_date.desc()).all()

    return render_template('customer_dashboard.html', 
        title='tilliX Customer Dashboard',
        account=account,
        total_due=total_due,
        last_bill=bills[0] if bills else None,
        comms=comms,
        requests=requests
    )

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'customer' or current_user.account is None:
        flash("Access Denied.", 'danger')
        return redirect(url_for('main.index'))

    account = current_user.account
    form = UpdateProfileForm(obj=account) # Populate form with existing data
    
    if form.validate_on_submit():
        account.full_name = form.full_name.data
        account.billing_address = form.billing_address.data
        # This updates the Nudge preference setting!
        account.comm_preference = form.comm_preference.data 
        db.session.commit()
        flash('Profile and communication preferences updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('profile_update.html', form=form, title='Update Profile')

# --- NEW: Service Request Route (tilliX) ---
@bp.route('/request/submit', methods=['GET', 'POST'])
@login_required
def submit_request():
    if current_user.role != 'customer' or current_user.account is None:
        flash("Access Denied.", 'danger')
        return redirect(url_for('main.index'))
        
    form = ServiceRequestForm()
    if form.validate_on_submit():
        new_request = Request(
            account_id=current_user.account.id,
            request_type=form.request_type.data,
            description=form.description.data,
            status='New'
        )
        db.session.add(new_request)
        db.session.commit()
        
        flash(f"Service Request '{new_request.request_type}' submitted successfully! We will review it shortly.", 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('service_request.html', form=form, title='Submit Service Request')


# --- Monay (Payment) & Bill Routes ---

@bp.route('/bills')
@login_required
def bill_list():
    if current_user.role != 'customer' or current_user.account is None:
        flash("Access Denied.", 'danger')
        return redirect(url_for('main.index'))
        
    # Filter for bills that are not fully paid
    bills = Bill.query.filter_by(account_id=current_user.account.id).filter(Bill.status != 'Paid').order_by(Bill.due_date.asc()).all()
    paid_bills = Bill.query.filter_by(account_id=current_user.account.id).filter_by(status='Paid').order_by(Bill.due_date.desc()).limit(3).all()

    return render_template('bill_list.html', 
        bills=bills, 
        paid_bills=paid_bills, 
        title='Bills & Payments'
    )

@bp.route('/pay/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def pay_bill(bill_id):
    if current_user.role != 'customer' or current_user.account is None:
        flash("Access Denied.", 'danger')
        return redirect(url_for('main.index'))
    
    bill = Bill.query.get_or_404(bill_id)
    if bill.account_id != current_user.account.id:
        flash("You do not have access to this bill.", 'danger')
        return redirect(url_for('main.bill_list'))
        
    if bill.status == 'Paid':
        flash(f"Bill #{bill_id} is already fully paid.", 'info')
        return redirect(url_for('main.bill_list'))
        
    # Pre-populate amount to pay with the full amount due
    form = PayBillForm(amount_to_pay=bill.amount_due)
    
    if form.validate_on_submit():
        amount = form.amount_to_pay.data
        method = form.payment_method_type.data
        
        # New Validation: Check against remaining amount due
        if amount <= 0 or amount > bill.amount_due:
            flash(f"Invalid payment amount. Must be between $0.01 and ${bill.amount_due:.2f}.", 'danger')
            return render_template('pay_bill.html', bill=bill, form=form, title='Simulated Payment')

        # EXECUTE Monay & Nudge Logic
        if simulate_payment_and_nudge(bill.id, current_user.account, amount, method):
            flash(f'Simulated Payment of ${amount:.2f} successful! Check your Dashboard for updated status.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('An internal error occurred during transaction processing.', 'danger')
            
    return render_template('pay_bill.html', bill=bill, form=form, title='Simulated Payment')


# --- NEW: Admin Routes (Platform & Management) ---

@bp.route('/admin')
@admin_required
def admin_dashboard():
    # Admin dashboard shows key operational metrics
    total_customers = Account.query.count()
    # Fetch only 'New' requests, ordered oldest first
    unresolved_requests = Request.query.filter_by(status='New').order_by(Request.submission_date.asc()).all()
    all_accounts = Account.query.order_by(Account.account_number).all()

    return render_template('admin/admin_dashboard.html', 
        title='Admin Panel',
        total_customers=total_customers,
        unresolved_requests=unresolved_requests,
        all_accounts=all_accounts
    )

@bp.route('/admin/bill/create', methods=['GET', 'POST'])
@admin_required
def admin_create_bill():
    # Pre-populate the admin username field for logging purposes
    form = AdminBillForm(admin_username=current_user.username)
    
    if form.validate_on_submit():
        account_num = form.account_number.data
        account = Account.query.filter_by(account_number=account_num).first()
        
        if not account:
            flash(f"Account number '{account_num}' not found.", 'danger')
            return render_template('admin/bill_create.html', form=form, title='Create New Bill')

        original_amount = form.original_amount.data
        due_date_obj = form.due_date.data # Date object from WTForms
        admin_username = form.admin_username.data # Get the admin user who created it

        # Create new Bill record
        new_bill = Bill(
            account_id=account.id,
            original_amount=original_amount,
            amount_due=original_amount, # Initially, amount due is the original amount
            issue_date=datetime.utcnow(),
            # FIX: Convert date object to datetime object at midnight (00:00:00) for consistency
            due_date=datetime.combine(due_date_obj, time.min), 
            status='Unpaid'
        )
        db.session.add(new_bill)
        
        # Nudge Trigger: Log the bill creation event, passing the Admin username
        nudge_new_bill(account, new_bill, admin_username)
        
        db.session.commit()
        flash(f'New Bill #{new_bill.id} for Account {account_num} created successfully by Admin {admin_username}! Nudge alert simulated.', 'success')
        return redirect(url_for('main.admin_dashboard'))
        
    return render_template('admin/bill_create.html', form=form, title='Create New Bill')