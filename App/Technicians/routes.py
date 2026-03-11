import uuid
from flask import redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from App.models import Booking, Technician, db, TaskLog, Users
from . import technicians_bp
import json
import time

@technicians_bp.route('/dashboard')
def dashboard():
   technician = Technician.query.filter_by(user_id=current_user.id).first()
   bookings_pending = 0
   bookings_in_progress = 0
   bookings_declined = 0
   bookings_completed = 0

   if technician:
      bookings_pending = Booking.query.filter_by(service_profile=technician.id, status='Pending').count()
      bookings_in_progress = Booking.query.filter_by(service_profile=technician.id, status='In Progress').count()
      bookings_declined = Booking.query.filter_by(service_profile=technician.id, status='Declined').count()
      bookings_completed = Booking.query.filter_by(service_profile=technician.id, status='Completed').count()

   context = {
      "bookings_pending": bookings_pending,
      "bookings_in_progress": bookings_in_progress,
      "bookings_declined": bookings_declined,
      "bookings_completed": bookings_completed,
      "technician": technician,
      "task_logs": TaskLog.query.filter_by(service_profile=current_user.id).order_by(TaskLog.timestamp.desc()).limit(10).all(),
      "stats": {
         "bookings_pending": bookings_pending,
         "bookings_in_progress": bookings_in_progress,
         "bookings_declined": bookings_declined,
         "bookings_completed": bookings_completed
      },
   }
   return render_template('technicians.dashboard.html', context=context)

@technicians_bp.route('/bookings')
@login_required
def bookings():
   technician = Technician.query.filter_by(user_id=current_user.id).first()
   bookings = Booking.query.filter_by(service_profile=technician.id).all() if technician else 0
   context = {
      "bookings": bookings
   }
   return render_template('technicians.bookings.html', context=context)

@technicians_bp.route('/accept-booking')
@login_required
def booking_acceptance():
   booking_id = request.args.get('id')
   # Logic to accept the booking goes here
   # For now, just redirecting to the bookings page
   booking = Booking.query.get(booking_id)
   if booking: 
      booking.status = 'In Progress'
      db.session.commit()
   return redirect(url_for('technicians.bookings'))

@technicians_bp.route('/complete-booking')
def Complete_Booking():
   booking_id = request.args.get('id')
   # Logic to complete the booking goes here
   booking = Booking.query.filter_by(id=booking_id).first()
   if booking:
      booking.status = 'Completed'
      booking.completed_date = time.strftime("%B %d, %Y %I:%M %p")
      task_log = TaskLog(
         id=str(uuid.uuid4()),
         action=booking.problem+' fixed',
         service_profile=current_user.id
      )
      db.session.add(task_log)
      db.session.commit()
   return redirect(url_for('technicians.bookings'))

@technicians_bp.route('/settings')
@login_required
def settings():
   id = request.args.get('id')
   # Logic to fetch technician settings by id can be added here
   # For now, just rendering the settings pager
   business_profiles = Technician.query.filter_by(service_profile=current_user.id).all()
   context = {
      "business_profiles": business_profiles,
      "number_of_profile": len(business_profiles),
      "total_bookings": sum(Booking.query.filter_by(service_profile=profile.id).count() for profile in business_profiles)
   }

   return render_template('technicians.settings.html', context=context)


@technicians_bp.route('/create_profile/', methods=['GET', 'POST'])
@login_required
def create_profile():
  if request.method == 'POST':
     # retrieving the details from the create_technician profile form
     name = request.form.get('profile_name')
     location = request.form.get('location')
     services_offered = request.form.get('services_offered')
     description = request.form.get('description')
     brand_logo = request.files.get('brand_photo')

     id = str(uuid.uuid4())
     New_Profile = Technician(
        id = id,
        name = name,
        location = location,
        services_offered = services_offered,
        description = description,
        photo = brand_logo.read(),
        user_id = current_user.id
     )
     print(current_user.id)

     db.session.add(New_Profile)
     db.session.commit()
     return """

      <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profile Pending Approval</title>

    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        /* Clock rotation animation */
        @keyframes spinSlow {
            from {
                transform: rotate(0deg);
            }

            to {
                transform: rotate(360deg);
            }
        }

        .clock-animate {
            animation: spinSlow 3s linear infinite;
        }

        /* Fade-in animation */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in {
            animation: fadeIn 0.8s ease-out;
        }
    </style>

</head>

<body class="bg-gray-100 flex items-center justify-center min-h-screen">

    <!-- Card -->
    <div class="bg-white shadow-lg rounded-xl p-8 text-center max-w-md w-full fade-in">

        <!-- Animated Clock Icon -->
        <div class="text-yellow-500 text-5xl mb-4">

            <i class="fa-solid fa-clock clock-animate"></i>

        </div>

        <!-- Message -->
        <h2 class="text-xl font-semibold text-gray-800 mb-2">
            Profile Pending Approval
        </h2>

        <p class="text-gray-600 text-sm mb-4">
            Your profile has been successfully created.
        </p>

        <p class="text-gray-500 text-sm">
            Please wait within <span class="font-semibold text-gray-700">24 hours</span>
            for approval by the admin.
        </p>

        <!-- Status Badge -->
        <div class="mt-6">

            <a href="/auth/login" class="bg-blue-300 text-white px-4 py-2 rounded-full text-sm font-medium">
                Go back to login
            </a>

        </div>

    </div>

</body>

</html>
"""
  if request.method == 'GET':
     return render_template('technicians.CreateProfile.html')

# route that deletes business profiles
@technicians_bp.route('/delete_business_profile')
@login_required
def Delete_BusinessProfile():
   service_profile = request.args.get('id')
   delete_profile = Technician.query.filter_by(id=service_profile, service_profile=current_user.id).first()
   if not delete_profile:
      flash("Business profile not found or you don't have permission to delete it.", "danger")
      return redirect(url_for('technicians.dashboard'))
   
      # Optionally, handle associated bookings if needed
      # For now, we'll just delete the profile

   db.session.delete(delete_profile)
   db.session.commit()
   flash("Business profile deleted successfully!", "success")
   return redirect(url_for('technicians.dashboard'))


@technicians_bp.route('/decline-booking')
@login_required
def Decline_Booking():
   booking_id = request.args.get('id')
   # Logic to decline the booking goes here
   booking = Booking.query.filter_by(id=booking_id).first()
   if booking:
      booking.status = 'Cancelled'
      db.session.commit()
   return redirect(url_for('technicians.bookings'))


@technicians_bp.route('/settings/update_profile', methods=['POST'])
@login_required
def update_profile():
   # Logic to update technician profile settings goes here
   if request.method == 'POST':
      username = request.form.get('username')
      email = request.form.get('email')
      phone_number = request.form.get('phone_number')

      # Update the user's profile information
      updated_user = Users.query.filter_by(id=current_user.id).first()
      if not updated_user:
         flash("User not found.", "danger")
         return redirect(url_for('technicians.dashboard'))
      else:
         updated_user.username = username
         updated_user.email = email
         updated_user.phone_number = phone_number
         db.session.commit()
         flash('Profile updated successfully!', 'success')
         return redirect(url_for('technicians.dashboard'))

   return redirect(url_for('technicians.dashboard'))