"""
Main entrypoint for the Admin Panel Application.
Gunicorn will use this Flask app directly.
"""
import logging
import os
import sys
import threading
import time
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            static_folder='admin/static',
            template_folder='admin/templates')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Placeholder for Telegram bot - commented out temporarily
def start_telegram_bot():
    logger.info("Telegram bot functionality temporarily disabled")
    """
    # This code will be enabled once all dependencies are installed correctly
    logger.info("Starting Telegram bot in background thread")
    import asyncio
    from bot.main import start_bot
    
    # Run the bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
    finally:
        loop.close()
    """

# Define models for admin panel
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Add context processor for datetime and current user
@app.context_processor
def inject_context():
    from datetime import datetime
    
    # Get current user if user_id is in session
    current_user = None
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        
    return {
        'now': datetime.now(),
        'current_user': current_user
    }

# Create tables and default admin user
with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin')
        admin.set_password('adminpassword')
        db.session.add(admin)
        db.session.commit()
        logger.info("Created default admin user")

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', title="Dashboard")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/staff')
def staff():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('staff.html', title="Staff Management")

@app.route('/bookings')
def bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('bookings.html', title="Bookings")

@app.route('/schedule')
def schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('schedule.html', title="Schedule Management")

# API endpoints for AJAX requests
@app.route('/bookings/stats/total')
def bookings_stats_total():
    if 'user_id' not in session:
        return "0", 401
    return "42"  # Sample data

@app.route('/bookings/stats/today')
def bookings_stats_today():
    if 'user_id' not in session:
        return "0", 401
    return "7"  # Sample data

@app.route('/bookings/stats/pending-payments')
def bookings_stats_pending_payments():
    if 'user_id' not in session:
        return "0", 401
    return "3"  # Sample data

@app.route('/staff/stats/active')
def staff_stats_active():
    if 'user_id' not in session:
        return "0", 401
    return "5"  # Sample data

@app.route('/bookings/recent')
def bookings_recent():
    if 'user_id' not in session:
        return "No data", 401
    
    # Return HTML for the recent bookings table
    html = """
    <tr>
        <td>1</td>
        <td>
            <div>John Doe</div>
            <small class="text-muted">+1234567890</small>
        </td>
        <td>Dr. Smith</td>
        <td>18 Apr 2025 13:00</td>
        <td>
            <span class="badge status-confirmed">CONFIRMED</span>
        </td>
        <td>
            <div class="btn-group">
                <a href="/bookings/1" class="btn btn-sm btn-primary">
                    <i class="fas fa-eye"></i>
                </a>
                <button class="btn btn-sm btn-danger delete-btn" data-id="1" data-type="bookings">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    </tr>
    <tr>
        <td>2</td>
        <td>
            <div>Jane Smith</div>
            <small class="text-muted">+0987654321</small>
        </td>
        <td>Dr. Johnson</td>
        <td>19 Apr 2025 15:30</td>
        <td>
            <span class="badge status-pending">PENDING</span>
        </td>
        <td>
            <div class="btn-group">
                <a href="/bookings/2" class="btn btn-sm btn-primary">
                    <i class="fas fa-eye"></i>
                </a>
                <button class="btn btn-sm btn-danger delete-btn" data-id="2" data-type="bookings">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    </tr>
    """
    return html

# Start the bot in a separate thread when the app starts
bot_thread = threading.Thread(target=start_telegram_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
