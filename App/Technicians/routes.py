from flask import redirect, render_template, request, url_for, flash, jsonify
from flask_login import login_required, current_user
from App.models import Booking, Technician, db, Users, Invoice
from . import technicians_bp
from sqlalchemy import extract, func
from App.extensions import mail
from flask_mail import Message
from weasyprint import HTML
import datetime, uuid, datetime


@technicians_bp.route('/dashboard')
@login_required
def dashboard():
   id = request.args.get('profile')
   Technician_Profile = Technician.query.filter_by(user_id=id).first()
   results = db.session.query(
        extract('month', Booking.created_at).label('month'),
        func.count(Booking.id)
    ).group_by('month').order_by('month').all()
   
   data = {month: count for month, count in results}

   contexts = {
      "total_bookings": Booking.query.filter_by(service_profile=Technician_Profile.id).all() if Technician_Profile else 0,
      "completed_bookings": Booking.query.filter_by(service_profile=Technician_Profile.id, status='Completed').count() if Technician_Profile else 0,
      "pending_bookings": Booking.query.filter_by(service_profile=Technician_Profile.id, status='Pending').count() if Technician_Profile else 0,
      "cancelled_bookings": Booking.query.filter_by(service_profile=Technician_Profile.id, status='Cancelled').count() if Technician_Profile else 0,
      "phone": Booking.query.filter_by(service_profile=Technician_Profile.id, device_type='phone', status="Completed").count(),
      "laptop": Booking.query.filter_by(service_profile=Technician_Profile.id, device_type='laptop', status="Completed").count(),
      "tablets": Booking.query.filter_by(service_profile=Technician_Profile.id, device_type='tablet', status="Completed").count(),
   }
   return render_template('technicians.dashboard.html', **contexts)

@technicians_bp.route('/bookings-per-month', methods=["GET"])
def BookingPerMonth():
   profile = Technician.query.filter_by(user_id=current_user.id).first()
   CurrentYear = datetime.datetime.now().year

   results = db.session.query(
      extract('month', Booking.created_at),
      func.count(Booking.id)
   ).filter(
      extract('year', Booking.created_at) == CurrentYear,
      Booking.status == 'Completed',
      Booking.service_profile == profile.id if profile else None
   ).group_by(
      extract('month', Booking.created_at)
   ).all()

   data = {int(month): count for month, count in results}
   return jsonify(data)

@technicians_bp.route('/active_bookings')
@login_required
def bookings():
   id = request.args.get("profile")
   profile = Technician.query.filter_by(user_id=id).first()
   contexts = {
      "bookings": Booking.query.filter_by(service_profile=profile.id, status="Pending").all()
   }
   return render_template('technicians.AcceptBooking.html', **contexts)

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
   flash("Booking request has been accepted successfully.")
   return redirect(f'/technician/dashboard?profile={current_user.id}')

@technicians_bp.route('/decline-booking/<id>')
@login_required
def Decline_Booking(id):
   # Logic to decline the booking goes here
   booking = Booking.query.filter_by(id=id).first()
   if booking:
      booking.status = 'Cancelled'
      db.session.commit()
   flash("Booking was successfully declined.")
   return redirect(f"/technician/active_bookings?profile={current_user.id}")

@technicians_bp.route('/generate_invoice', methods=["GET", "POST"])
@login_required
def GenerateInvoice():

   id = request.args.get("profile")
   profile = Technician.query.filter_by(user_id=id).first()
   contexts = {
      "bookings": Booking.query.filter_by(service_profile=profile.id, status="In Progress").all()
   }
   return render_template('technicians.GenerateInvoice.html', **contexts)

@technicians_bp.route('/generate_invoice/<id>', methods=['GET', 'POST'])
@login_required
def Complete_Booking(id):
   if request.method == "POST":
      booking = Booking.query.filter_by(id=id).first()
      service_cost = request.form.get("service_price")
      parts_cost = request.form.get("parts_price")
      booking.status = "Completed"

      current_time = datetime.datetime.now()
      booking.completed_date = current_time.strftime("%B %d, %Y %I:%M %p")
      db.session.commit()

      # creates an invoice the user
      new_invoice = Invoice()

      # Sending a email to the customer for successful
      # service from the technician
      # converting the html-content into a pdf
      contexts = {
         "booking": booking,
         "service_cost": service_cost,
         "parts_cost": parts_cost,
         "total_cost": int(service_cost) + int(parts_cost) 
      }
      html_template = render_template("includes/invoice.html", **contexts)

      pdf_document = HTML(string=html_template).write_pdf()

      msg = Message("Your Booking Completed Successfully", recipients=[booking.user.email])
      msg.body = f"Hello {booking.user.username}, Your repair booking for device has been completed. Download the invoice below"
      msg.attach(f"{booking.id}.pdf", "application/pdf", pdf_document)
      mail.send(msg)

      # creating an invoice for the booking
      NewInvoice = Invoice(
         id = str(uuid.uuid4()),
         parts_cost = parts_cost,
         service_cost = service_cost,
         total_cost = int(parts_cost) + int(service_cost),
         booking_id = booking.id
      )

      db.session.add(NewInvoice)
      db.session.commit()

      flash('Invoice sent to the customer successfully')
      return redirect(f'/technician/dashboard?profile={ current_user.id }')
   
@technicians_bp.route("/history")
def BookingHistory():
   id = request.args.get("profile")
   profile = Technician.query.filter_by(user_id=id).first()

   # Querying booking with status 'Completed'
   completed_bookings = Booking.query.filter(
        Booking.status.in_(['Completed', 'Cancelled']),
        Booking.service_profile == profile.id
    ).order_by(Booking.created_at.desc()).all()
   contexts = {
      "completed_bookings": completed_bookings
   }
   return render_template("technicians.BookingHistory.html", **contexts)



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
     flash("Your profile has been created successfully. Please wait for the admin approval.")
     return redirect("/auth/login")
  
  if request.method == 'GET':
     return render_template('technicians.CreateProfile.html')

@technicians_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def update_profile():
   user = current_user
   profile = Technician.query.filter_by(user_id=current_user.id).first()
   if request.method == 'POST':
      user.username = request.form.get('username')
      user.email = request.form.get('email')
      user.phone_number = request.form.get('phone-number')

      profile_photo = request.files.get('profile-photo')

      if profile_photo:
         user.photo = profile_photo.read()

      profile.name = request.form.get('brand-name')
      profile.location = request.form.get('brand-location')
      profile.services_offered = request.form.get('services_offered')
      brand_photo = request.files.get("brand-photo")

      if brand_photo:
         profile.photo = brand_photo.read()


      db.session.commit()
      flash("Profile has been updated successfully.")
      return redirect(f"/technician/dashboard?profile={ current_user.id }")

   contexts = {
      "profile": profile
   }
   return render_template('technicians.settings.html', **contexts)

