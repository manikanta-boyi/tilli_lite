from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash # werkzeug.security is needed for CLI setup
from datetime import datetime, timedelta
from config import Config
# NOTE: Ensure Request is imported from models, assuming you defined it there
from models import db, User, Account, Bill, PaymentTransaction, CommunicationLog, Request 
from routes import bp as main_bp

# Flask Extensions setup
login = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db) 

    # Set up Flask-Login configuration
    login.login_view = 'main.login'
    login.login_message = 'Please log in to access this page.'

    # Register blueprints
    app.register_blueprint(main_bp)

    with app.app_context():
        # Ensure all models are imported so Migrate sees them
        pass 
        
        # Helper for Flask-Login
        @login.user_loader
        def load_user(id):
            return User.query.get(int(id))

    return app

# Add this section to make the application instance accessible to the 'flask' command
app = create_app()

@app.cli.command('setup_demo_data')
def setup_demo_data():
    """Creates the initial demo users (customer and admin) and bills."""
    with app.app_context():
        # Check if the primary customer already exists
        if User.query.filter_by(username='demo_customer').first() is None:
            print("--- Creating Mock Data (Customer & Admin) ---")
            
            # 1. Create a Customer Account (tilliX Core)
            customer_account = Account(
                account_number='A-948102',
                full_name='Alex Johnson',
                billing_address='123 Synergy Way, McLean, VA 22102',
                comm_preference='Email' 
            )
            db.session.add(customer_account)
            db.session.flush() 
            
            # 2. Create the Customer User (Flask-Login)
            customer_user = User(
                username='demo_customer',
                email='alex@example.com',
                password_hash=generate_password_hash('password'),
                role='customer',
                account_id=customer_account.id
            )
            db.session.add(customer_user)

            # --- START ADMIN USER SETUP ---
            # 3. Create an Admin Account (a required link for all Users)
            admin_account = Account(
                account_number='A-000000',
                full_name='System Administrator',
                billing_address='999 Backend Ave',
                comm_preference='None'
            )
            db.session.add(admin_account)
            db.session.flush()
            
            # 4. Create the Admin User
            admin_user = User(
                username='admin',
                email='admin@tilliX.com',
                password_hash=generate_password_hash('password'),
                role='admin',
                account_id=admin_account.id
            )
            db.session.add(admin_user)
            # --- END ADMIN USER SETUP ---


            # 5. Create Mock Bills
            bill1 = Bill(
                account_id=customer_account.id, 
                original_amount=155.50,
                amount_due=155.50, 
                issue_date=datetime.utcnow() - timedelta(days=30),
                due_date=datetime.utcnow() - timedelta(days=10),
                status='Unpaid'
            )
            bill2 = Bill(
                account_id=customer_account.id, 
                original_amount=210.00,
                amount_due=210.00, 
                issue_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=20),
                status='Unpaid'
            )
            paid_bill = Bill(
                account_id=customer_account.id, 
                original_amount=100.00,
                amount_due=0.00, 
                issue_date=datetime.utcnow() - timedelta(days=60),
                due_date=datetime.utcnow() - timedelta(days=40),
                status='Paid'
            )
            
            db.session.add_all([bill1, bill2, paid_bill])
            db.session.commit()
            print("--- Mock Data Creation Complete: Customer 'demo_customer', Admin 'admin'. Password for both is 'password'. ---")
        else:
            print("--- Demo data already exists. Skipping setup. ---")

if __name__ == '__main__':
    app.run(debug=True)