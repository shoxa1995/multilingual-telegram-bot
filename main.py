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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///admin.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

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

# User model methods
def set_password(self, password):
    self.password_hash = generate_password_hash(password)
    
def check_password(self, password):
    return check_password_hash(self.password_hash, password)

# Add methods to the User model imported from models.py
from models import User
User.set_password = set_password
User.check_password = check_password

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
    
    from models import Staff
    # Get staff data from the database
    staff_list = Staff.query.all()
    
    return render_template('staff.html', title="Staff Management", staff_list=staff_list)

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
    
    from models import Booking
    # Count total bookings
    total_count = Booking.query.count()
    return str(total_count)

@app.route('/bookings/stats/today')
def bookings_stats_today():
    if 'user_id' not in session:
        return "0", 401
    
    from models import Booking
    from datetime import datetime, time
    # Count today's bookings
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    today_count = Booking.query.filter(
        Booking.booking_date >= today_start,
        Booking.booking_date <= today_end
    ).count()
    
    return str(today_count)

@app.route('/bookings/stats/pending-payments')
def bookings_stats_pending_payments():
    if 'user_id' not in session:
        return "0", 401
    
    from models import Booking, BookingStatus
    # Count pending payment bookings
    pending_payments = Booking.query.filter_by(status=BookingStatus.PAYMENT_PENDING).count()
    return str(pending_payments)

@app.route('/staff/stats/active')
def staff_stats_active():
    if 'user_id' not in session:
        return "0", 401
    
    from models import Staff
    # Count active staff members
    active_count = Staff.query.filter_by(is_active=True).count()
    return str(active_count)

@app.route('/bookings/recent')
def bookings_recent():
    if 'user_id' not in session:
        return "No data", 401
    
    from models import Booking, BookingStatus
    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    if not recent_bookings:
        return "<tr><td colspan='6' class='text-center'>No bookings found</td></tr>"
    
    html = ""
    for booking in recent_bookings:
        status_class = ""
        if booking.status == BookingStatus.CONFIRMED:
            status_class = "status-confirmed"
        elif booking.status == BookingStatus.PENDING:
            status_class = "status-pending"
        elif booking.status == BookingStatus.PAYMENT_PENDING:
            status_class = "status-payment-pending"
        elif booking.status == BookingStatus.CANCELLED:
            status_class = "status-cancelled"
        elif booking.status == BookingStatus.COMPLETED:
            status_class = "status-completed"
        
        html += f"""
        <tr>
            <td>{booking.id}</td>
            <td>
                <div>{booking.user.first_name} {booking.user.last_name or ''}</div>
                <small class="text-muted">{booking.user.phone_number or 'No phone'}</small>
            </td>
            <td>{booking.staff.name}</td>
            <td>{booking.booking_date.strftime('%d %b %Y %H:%M')}</td>
            <td>
                <span class="badge {status_class}">{booking.status.value.upper()}</span>
            </td>
            <td>
                <div class="btn-group">
                    <a href="/bookings/{booking.id}" class="btn btn-sm btn-primary">
                        <i class="fas fa-eye"></i>
                    </a>
                    <button class="btn btn-sm btn-danger delete-btn" data-id="{booking.id}" data-type="bookings">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
        """
    
    return html

@app.route('/staff/add', methods=['GET', 'POST'])
def add_staff():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    from models import Staff
    
    if request.method == 'POST':
        # Create a new staff member
        new_staff = Staff(
            name=request.form.get('name'),
            bitrix_user_id=request.form.get('bitrix_user_id'),
            description_en=request.form.get('description_en'),
            description_ru=request.form.get('description_ru'),
            description_uz=request.form.get('description_uz'),
            photo_url=request.form.get('photo_url'),
            price=int(request.form.get('price', 0)),
            is_active=bool(request.form.get('is_active', False))
        )
        
        db.session.add(new_staff)
        db.session.commit()
        
        flash('Staff member added successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('staff_form.html', title="Add Staff Member", staff=None)

@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    from models import Staff
    
    # Get staff from database
    staff = Staff.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        # Update staff data
        staff.name = request.form.get('name')
        staff.bitrix_user_id = request.form.get('bitrix_user_id')
        staff.description_en = request.form.get('description_en')
        staff.description_ru = request.form.get('description_ru')
        staff.description_uz = request.form.get('description_uz')
        staff.photo_url = request.form.get('photo_url')
        staff.price = int(request.form.get('price', 0))
        staff.is_active = 'is_active' in request.form
        
        db.session.commit()
        
        flash('Staff member updated successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('staff_form.html', title="Edit Staff Member", staff=staff)

@app.route('/staff/toggle/<int:staff_id>', methods=['POST'])
def toggle_staff(staff_id):
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    from models import Staff
    
    # Toggle staff active status
    staff = Staff.query.get_or_404(staff_id)
    staff.is_active = not staff.is_active
    db.session.commit()
    
    return "success"

@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    from models import Staff
    
    # Delete staff from database
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    
    return "success"

# Start the bot in a separate thread when the app starts
bot_thread = threading.Thread(target=start_telegram_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
