from . import admin_bp
from flask import flash, redirect, render_template, request
from App.models import Booking, BusinessProfile, Users, db

# Admin routes will be defined in the routes.py file within the Admin directory

@admin_bp.route('/')
def admin_dashboard():
    context = {
        'total_booking': Booking.query.count(),
        'total_users': Users.query.filter(Users.role != 'admin', Users.is_active == True).count(),
        'total_profiles': BusinessProfile.query.filter_by(is_approved=True).count(),
        'all_profiles': BusinessProfile.query.filter_by(is_approved=True).all(),

    }
    stats = {
            'users': Users.query.filter(Users.role != 'admin', Users.is_active == True).count(),
            'bookings': Booking.query.count(),
            'profiles': BusinessProfile.query.filter_by(is_approved=True).count()
        }
    return render_template('admin.dashboard.html', context=context,stats=stats)


@admin_bp.route('/users/')
def all_users():
    context= {
        'active_users': Users.query.all(),
    }
    return render_template('admin.users.html', context=context)

@admin_bp.route('/approve_users')
def approve_users():
    user_id =  request.args.get('id')
    user = Users.query.filter_by(id=user_id).first()
    if user:
        user.is_active = True
        db.session.commit()
        flash(" User Approved Successfully", "success")
    return redirect('/admin/users/')

@admin_bp.route('/delete_user')
def delete_user():
    user_id =  request.args.get('id')
    user = Users.query.filter_by(id=user_id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User Deleted Successfully", "success")
    return redirect('/admin/users/')

@admin_bp.route('/bookings/')
def bookings():
    context = {
        'all_bookings': Booking.query.all(),
    }
    return render_template('admin.bookings.html', context=context)

@admin_bp.route('/profiles/')
def profiles():
    context = {
        'all_profiles': BusinessProfile.query.all(),
    }
    return render_template('admin.profiles.html', context=context)

@admin_bp.route('/approve_profile')
def approve_profile():
    profile_id =  request.args.get('id')
    profile = BusinessProfile.query.filter_by(id=profile_id).first()
    if profile:
        profile.is_approved = True
        db.session.commit()
        flash(" Profile Approved Successfully", "success")
    return redirect('/admin/profiles/')

@admin_bp.route('/revoke_profile')
def revoke_profile():
    profile_id =  request.args.get('id')
    profile = BusinessProfile.query.filter_by(id=profile_id).first()
    if profile:
        profile.is_approved = False
        db.session.commit()
        flash(" Profile Approval Revoked Successfully", "success")
    return redirect('/admin/profiles/')