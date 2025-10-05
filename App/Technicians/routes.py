import uuid
from flask import redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user
from App.models import Booking, BusinessProfile, db, TaskLog
from . import technicians_bp
import json
import time

@technicians_bp.route('/dashboard')
@login_required
def dashboard():
   business_profile = BusinessProfile.query.filter_by(technician_id=current_user.id).first()
   bookings_pending = 0
   bookings_in_progress = 0
   bookings_declined = 0
   bookings_completed = 0

   if business_profile:
      bookings_pending = Booking.query.filter_by(service_profile=business_profile.id, status='Pending').count()
      bookings_in_progress = Booking.query.filter_by(service_profile=business_profile.id, status='In Progress').count()
      bookings_declined = Booking.query.filter_by(service_profile=business_profile.id, status='Declined').count()
      bookings_completed = Booking.query.filter_by(service_profile=business_profile.id, status='Completed').count()

   context = {
      "bookings_pending": bookings_pending,
      "bookings_in_progress": bookings_in_progress,
      "bookings_declined": bookings_declined,
      "bookings_completed": bookings_completed,
      "business_profile": business_profile,
      "task_logs": TaskLog.query.filter_by(technician_id=current_user.id).order_by(TaskLog.timestamp.desc()).limit(10).all(),
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
   business_profile = BusinessProfile.query.filter_by(technician_id=current_user.id).first()
   bookings = Booking.query.filter_by(service_profile=business_profile.id).all() if business_profile else 0
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
         technician_id=current_user.id
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
   business_profiles = BusinessProfile.query.filter_by(technician_id=current_user.id).all()
   context = {
      "business_profiles": business_profiles,
      "number_of_profile": len(business_profiles),
      "total_bookings": sum(Booking.query.filter_by(service_profile=profile.id).count() for profile in business_profiles)
   }

   return render_template('technicians.settings.html', context=context)


@technicians_bp.route('/create_business/', methods=['GET', 'POST'])
@login_required
def create_business_profile():
   # Ensure only technicians can create business profiles
   if not hasattr(current_user, 'role') or current_user.role != 'technician':
      flash('Only technicians can create business profiles.', 'danger')
      return redirect(url_for('technicians.dashboard'))

   if request.method == 'POST':
      name = request.form.get('business_name')
      location = request.form.get('location')
      services_offered = request.form.getlist('services')
      description = request.form.get('business_description')
      business_photo = request.files.get('business_photo')

      if not all([name, location, services_offered, description, business_photo]):
         flash('All fields are required.', 'warning')
         return redirect(url_for('technicians.create_business_profile'))

      # Check if technician already has a business profile
      existing_profile = BusinessProfile.query.filter_by(technician_id=current_user.id).first()
      if existing_profile:
         flash('You already have a business profile.', 'info')
         return redirect(url_for('technicians.dashboard'))

      profile = BusinessProfile(
         id=str(uuid.uuid4()),
         name=name,
         location=location,
         services_offered=json.dumps(services_offered),  # Store as JSON string
         description=description,
         photo=business_photo.read(),
         technician_id=current_user.id
      )
      db.session.add(profile)
      db.session.commit()
      flash('Business profile created successfully!', 'success')
      return redirect(url_for('technicians.dashboard'))

   # GET request: render the business profile creation form
   return redirect(url_for('technicians.settings'))

# route that deletes business profiles
@technicians_bp.route('/delete_business_profile')
@login_required
def Delete_BusinessProfile():
   business_profile_id = request.args.get('id')
   delete_profile = BusinessProfile.query.filter_by(id=business_profile_id, technician_id=current_user.id).first()
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
      booking.status = 'Declined'
      db.session.commit()
   return redirect(url_for('technicians.bookings'))