import uuid
from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import geocoder

from App.models import db, Users, Booking, Technician, Invoice
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
            Booking.status.in_(['Pending', 'In Progress']),
            Booking.user_id == user_id
        ).order_by(Booking.created_at.desc()).all()
    }
    return render_template("dashboard.html", **context)


@users_bp.route('/appointment_booking')
@login_required
def booking_appointment():
    technicians = Technician.query.filter_by(is_approved=True).all()
    return render_template('bookingRepair.html', technicians=technicians)


@users_bp.route('/appointment_booking', methods=['GET', 'POST'])
@login_required
def proceed_appointment():
    if request.method == 'POST':
        technician_id = request.form.get('technician_id')
        device_type = request.form.get('device-type')
        problem_description = request.form.get('description')
        device_brand = request.form.get('device_brand')
        photo = request.files.get('device-photo')

        # Validate required fields
        if not all([technician_id, device_type, problem_description, device_brand]):
            flash('Please fill in all required fields.')
            return redirect(url_for('users.booking_appointment'))

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
        return redirect(f"/users/dashboard")
    
    technicians = Technician.query.filter_by(is_approved=True).all()
    return render_template('bookingRepair.html', technicians=technicians)


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

