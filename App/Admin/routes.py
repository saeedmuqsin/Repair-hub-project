from . import admin_bp
from flask import render_template


# Admin routes will be defined in the routes.py file within the Admin directory

@admin_bp.route('/')
def admin_dashboard():
    return render_template('admin.dashboard.html')