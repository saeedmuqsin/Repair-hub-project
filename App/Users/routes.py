import uuid
from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import geocoder

from App.models import db, Users, Booking, Technician
from App.extensions import mail
from . import users_bp


@users_bp.route("/dashboard")
@login_required
def home():
    user_id = current_user.id
    
    # Use single query with aggregation instead of multiple counts
    bookings_query = Booking.query.filter_by(user_id=user_id)
    
    context = {
        "total_bookings": bookings_query.count(),
        "completed_bookings": bookings_query.filter_by(status='Completed').count(),
        "pending_bookings": bookings_query.filter_by(status='Pending').count(),
        "cancelled_bookings": bookings_query.filter_by(status='Cancelled').count(),
        "bookings": Booking.query.filter(
            Booking.status.in_(['Pending', 'In progress']),
            Booking.user_id == user_id
        ).order_by(Booking.created_at.desc()).all()
    }
    return render_template("dashboard.html", **context)


@users_bp.route('/appointment_booking')
@login_required
def booking_appointment():
    technicians = Technician.query.filter_by(is_approved=True).all()
    return render_template('bookingRepair.html', technicians=technicians)


@users_bp.route('/appointment_booking/', methods=['GET', 'POST'])
@login_required
def proceed_appointment():
    technician_id = request.args.get('id')

    if request.method == 'POST':
        device_type = request.form.get('device-type')
        problem_description = request.form.get('description')
        device_brand = request.form.get('device_brand')
        photo = request.files.get('device-photo')

        # Validate required fields
        if not all([device_type, problem_description, device_brand]):
            flash('Please fill in all required fields.')
            return redirect(url_for('users.proceed_appointment', id=technician_id))

        new_booking = Booking(
            id=str(uuid.uuid4()),
            device_type=device_type,
            problem_description=problem_description,
            location=geocoder.ip('me').city,
            user_id=current_user.id,
            device_photo=photo.read() if photo else None,
            service_profile=technician_id,
            device_brand=device_brand
        )

        db.session.add(new_booking)
        db.session.commit()
        flash('Your booking has been created successfully!')
        return redirect(url_for('users.home', id=current_user.id))
    
    return render_template('bookingRepair.html')


@users_bp.route('/booking/history')
@login_required
def history():
    bookings = Booking.query.filter(
        Booking.status.in_(['Completed', 'Cancelled']),
        Booking.user_id == current_user.id
    ).order_by(Booking.created_at.desc()).all()
    
    return render_template("booking_history.html", bookings=bookings)


@users_bp.route('/profile_settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    user = current_user

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.phone_number = request.form.get('phone-number')
        profile_photo = request.files.get('profile-photo')

        if profile_photo:
            user.photo = profile_photo.read()

        db.session.commit()
        flash('Your profile has been updated successfully!')
        return redirect(url_for('users.home', id=current_user.id))
    
    context = {
        "current_user": user,
        "current_location": geocoder.ip('me')
    }
    return render_template("settings.html", **context)


@users_bp.route('/send_password_reset')
@login_required
def send_message():
    reset_link = url_for('users.reset_password', id=current_user.id, _external=True)
    msg = Message('Password Reset Request', recipients=[current_user.email])
    msg.body = f'Click the link to reset your password: {reset_link}'
    
    mail.send(msg)
    flash('A password reset link has been sent to your email address.')
    return redirect(url_for('users.home', id=current_user.id))


@users_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    user_id = request.args.get('id')
    user = Users.query.filter_by(id=user_id).first_or_404()

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        
        if not new_password or len(new_password) < 8:
            flash('Password must be at least 8 characters long.')
            return render_template('reset_password.html')
        
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Your password has been reset successfully!')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html')