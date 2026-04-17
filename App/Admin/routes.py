from . import admin_bp
from flask import flash, redirect, render_template, request, url_for, jsonify
from App.models import Booking, Technician, Users, db, Admin, Invoice
from  flask_login import login_user, logout_user, login_required
from sqlalchemy import extract, func
from App.extensions import mail
import datetime
from flask_mail import Message

@admin_bp.route('/dashboard')
def admin_dashboard():
    context = {
        'total_bookings': len([booking for booking in Booking.query.all()]),
        'active_users': len([users for users in Users.query.filter_by(is_active=True).all()]),
        'active_brands': len([brand for brand in Technician.query.filter_by(is_approved=True).all()]),
        'total_invoice': len([invoice for invoice in Invoice.query.all()])
    }
    return render_template('admin.dashboard.html', **context)


@admin_bp.route('/customers')
def ActiveCustomers():
    contexts = {
        "active_customers": Users.query.filter_by(role="customer").all()
    }
    return render_template('admin.ActiveCustomers.html', **contexts)

@admin_bp.route('/technicians')
def ActiveTechnician():
    contexts = {
        "active_technicians": Technician.query.all()
    }
    return render_template("admin.ActiveTechnicians.html", **contexts)

@admin_bp.route("/approve-technician/<id>")
def ApproveTechnician(id):
    profile = Technician.query.filter_by(id=id).first()

    msg = Message("Your profile is been approved successfully.", recipients=[profile.technician.email])
    msg.body= f"Hello! {profile.technician.username}, Your profile has been approved sucessfully"
    mail.send(msg)

    # approved by changing the profile approval to true
    profile.is_approved = True
    db.session.commit()

    flash("Profile has beeen approved successfully")
    return redirect(f"/admin/dashboard")

@admin_bp.route('/revoke-technician/<id>')
def RevokeTechnician(id):
    profile = Technician.query.filter_by(id=id).first()

    msg = Message("Your profile is revoked", recipients=[profile.technician.email])
    msg.body= f"Hello! {profile.technician.username}, Your profile has been revoked due to the voilation of the terms of the community."
    mail.send(msg)

    profile.is_approved = False
    db.session.commit()

    flash("Operation done successfully")
    return redirect(f'/admin/dashboard')

@admin_bp.route('/bookings')
def Bookings():
    contexts = {
        'bookings': Booking.query.all()
    }
    return render_template('admin.Bookings.html', **contexts)

@admin_bp.route('/monthly-metrics')
def monthly_metrics():
    CurrentYear = datetime.datetime.now().year
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Get bookings per month
    bookings_data = db.session.query(
        extract('month', Booking.created_at),
    ).filter(
        extract('year', Booking.created_at) == CurrentYear
    ).all()
    bookings_count = {0: 0}
    for month in bookings_data:
        month_num = int(month[0]) if month[0] else 0
        bookings_count[month_num] = bookings_count.get(month_num, 0) + 1
    
    # Get users created per month
    users_data = db.session.query(
        extract('month', Users.created_at),
    ).filter(
        extract('year', Users.created_at) == CurrentYear
    ).all()
    users_count = {0: 0}
    for month in users_data:
        month_num = int(month[0]) if month[0] else 0
        users_count[month_num] = users_count.get(month_num, 0) + 1
    
    # Get active brands approved per month
    brands_data = db.session.query(
        extract('month', Technician.created_at),
    ).filter(
        extract('year', Technician.created_at) == CurrentYear,
        Technician.is_approved == True
    ).all()
    brands_count = {0: 0}
    for month in brands_data:
        month_num = int(month[0]) if month[0] else 0
        brands_count[month_num] = brands_count.get(month_num, 0) + 1
    
    # Build arrays for all months
    bookings_array = [bookings_count.get(i, 0) for i in range(1, 13)]
    users_array = [users_count.get(i, 0) for i in range(1, 13)]
    brands_array = [brands_count.get(i, 0) for i in range(1, 13)]
    
    return jsonify({
        'months': month_labels,
        'bookings': bookings_array,
        'users': users_array,
        'brands': brands_array
    })

@admin_bp.route('/top-brands')
def top_brands():
    # Get top 10 brands with most bookings
    top_10_brands = db.session.query(
        Technician.id,
        Technician.name,
        Technician.photo,
        func.count(Booking.id).label('booking_count')
    ).outerjoin(
        Booking, Booking.service_profile == Technician.id
    ).group_by(
        Technician.id,
        Technician.name,
        Technician.photo
    ).order_by(
        func.count(Booking.id).desc()
    ).limit(10).all()
    
    brands_data = []
    for brand in top_10_brands:
        import base64
        encoded_photo = base64.b64encode(brand.photo).decode('utf-8') if brand.photo else ''
        brands_data.append({
            'id': brand.id,
            'name': brand.name,
            'photo': encoded_photo,
            'booking_count': brand.booking_count if brand.booking_count else 0
        })
    
    return jsonify({'brands': brands_data})

