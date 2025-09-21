import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
from App.models import db, Users, Booking, BusinessProfile
from flask_login import login_required, current_user

from . import users_bp

@users_bp.route("/")
@login_required
def home():
    user_id = request.args.get('id')
    return render_template("dashboard.html")

@users_bp.route('/appointment_booking')
@login_required
def booking_appointment():
    business_profiles = BusinessProfile.query.filter_by(is_approved=True).all()
    # total_bookings = Booking.query.filter_by(service_profile=business_profiles.id).count()
    return render_template('select_technician.html', business_profiles=business_profiles)

@users_bp.route('/appointment_booking/', methods=['GET', 'POST'])
@login_required
def proceed_appointment():
    service_provider_id = request.args.get('id')

    if request.method == 'POST':
        device_type = request.form.get('device-type')
        problem_description = request.form.get('problem-description')
        location = request.form.get('location')
        device_fault = request.form.get('device-fault')
        device_photo = request.files.get('device-photo')


        new_booking = Booking(
            id=str(uuid.uuid4()),
            device_type=device_type,
            problem_description=problem_description,
            location=location,
            problem=device_fault,
            user_id=current_user.id,
            device_photo=device_photo.read() if device_photo else None,
            service_profile=service_provider_id
        )

        db.session.add(new_booking)
        db.session.commit()
        return """
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Booking Successful</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <!-- Bootstrap CSS -->
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body {
                                background: #f8fafc;
                                color: #212529;
                            }
                            .success-illustration {
                                width: 120px;
                                height: 120px;
                                margin-bottom: 1rem;
                                animation: bounceIn 1s;
                            }
                            @keyframes bounceIn {
                                0% { transform: scale(0.5); opacity: 0; }
                                60% { transform: scale(1.1); opacity: 1; }
                                80% { transform: scale(0.95); }
                                100% { transform: scale(1); }
                            }
                            .checkmark {
                                stroke-dasharray: 60;
                                stroke-dashoffset: 60;
                                animation: drawCheck 1s 0.5s forwards;
                            }
                            @keyframes drawCheck {
                                to { stroke-dashoffset: 0; }
                            }
                            .confetti {
                                position: absolute;
                                top: 0; left: 0; width: 100%; height: 100%;
                                pointer-events: none;
                                z-index: 0;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="position-relative min-vh-100 d-flex flex-column justify-content-center align-items-center">
                            <!-- Confetti SVG -->
                            <svg class="confetti">
                                <circle cx="30" cy="30" r="6" fill="#ffc107" />
                                <circle cx="120" cy="60" r="5" fill="#0d6efd" />
                                <circle cx="200" cy="40" r="4" fill="#198754" />
                                <circle cx="80" cy="120" r="7" fill="#dc3545" />
                                <circle cx="220" cy="110" r="5" fill="#6f42c1" />
                                <circle cx="160" cy="150" r="6" fill="#fd7e14" />
                            </svg>
                            <!-- Success Illustration -->
                            <div class="success-illustration mb-3 mx-auto d-block">
                                <svg width="100" height="100" viewBox="0 0 120 120" fill="none">
                                    <circle cx="60" cy="60" r="55" fill="#e9f7ef" stroke="#198754" stroke-width="4"/>
                                    <polyline class="checkmark" points="40,65 55,80 80,50" fill="none" stroke="#198754" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </div>
                            <!-- Success Text -->
                            <h2 class="fw-bold mb-2">Booking Confirmed!</h2>
                            <p class="mb-4 fs-5 text-dark" style="font-size: 16px;">Your booking was successful.<br>We look forward to serving you.</p>
                            <a href="/users/" class="btn btn-dark px-4 py-2 fw-semibold shadow-sm">Go to Home</a>
                        </div>
                        <!-- Bootstrap JS (optional for some animations) -->
                        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
                    </body>
                    </html>
                    """

@users_bp.route('/history')
@login_required
def history():
    bookings = Booking.query.order_by(Booking.created_at).all()
    return render_template("history.html", bookings=bookings)



@users_bp.route('/delete_booking/<booking_id>')
@login_required
def delete_booking(booking_id):
  booking = Booking.query.get(booking_id)
  if booking and booking.user_id == current_user.id:
      db.session.delete(booking)
      db.session.commit()
      flash('Booking deleted successfully.', 'success')
      return redirect(url_for('users.history'))
    
  else:
      flash('Booking not found or unauthorized.', 'danger')
  return redirect(url_for('users.history'))
       

@users_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        profile_photo = request.files.get('profile-picture')

        if not phone_number.isdigit() or len(phone_number) < 10:
            flash("Invalid phone number")
            return redirect(url_for('users.settings'))

        current_user.username = username
        current_user.email = email
        current_user.phone_number = phone_number
        if profile_photo:
            current_user.photo = profile_photo.read()

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('users.home'))
    return render_template("settings.html", current_user=current_user)


