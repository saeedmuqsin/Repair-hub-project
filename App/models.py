from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import LargeBinary as MEDIUMBLOB
from sqlalchemy.types import JSON
import base64
import json
import psycopg2

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(200), primary_key=True)
    profile_id = db.Column(MEDIUMBLOB, nullable=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(50), nullable=False)  # e.g., 'customer', 'technician'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    photo = db.Column(MEDIUMBLOB, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    booking = db.relationship('Booking', backref="user", cascade="all, delete-orphan")
    technician = db.relationship(
        'Technician',
        backref="technician",
        cascade="all, delete-orphan"
    )
   
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)
    
    def User_ProfilePhoto(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img
    
    def Display_ProfileID(self):
        encoded_img = base64.b64encode(self.profile_id).decode('utf-8')
        return encoded_img
    
    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y %I:%M %p")
        return None
    

class Booking(db.Model):
    __tablename__ = "booking"
    id = db.Column(db.String(200), primary_key=True)
    device_type = db.Column(db.String(200), nullable = False)
    problem_description = db.Column(db.Text, nullable = False)
    status = db.Column(db.String(200), nullable=False, default='Pending')
    location = db.Column(db.String(100),nullable = False)
    device_photo = db.Column(MEDIUMBLOB, nullable = False)
    user_id = db.Column(db.String(200), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    service_profile = db.Column(db.String(200), db.ForeignKey('Technician.id', ondelete='CASCADE'), default="Profile Deleted", nullable=False)
    completed_date = db.Column(db.String(200), default = 'Not yet')
    device_brand = db.Column(db.String(100), nullable=False)

    def Display_deviceImage(self):
        encoded_img = base64.b64encode(self.device_photo).decode('utf-8')
        return encoded_img
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y %I:%M %p")
        return None

class Technician(db.Model):
    __tablename__ = 'Technician'
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    services_offered = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(MEDIUMBLOB, nullable=False)
    user_id = db.Column(db.String(200), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_approved = db.Column(db.Boolean, default=False)
    booking = db.relationship('Booking', backref='Technician', cascade="all, delete-orphan")


    def Display_photo(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img


    def Total_Booking(self, id):
        total_booking  = Booking.query.filter_by(service_profile = id).count()
        return total_booking
    
    def status_count(self, id):
        bookings_stats = {
            'Pending': Booking.query.filter_by(service_profile=id, status='Pending').count(),
            'In Progress': Booking.query.filter_by(service_profile=id, status='In Progress').count(),
            'Completed': Booking.query.filter_by(service_profile=id, status='Completed').count(),
            'Declined': Booking.query.filter_by(service_profile=id, status='Declined').count()
        }
        return bookings_stats
    
    
class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    id = db.Column(db.String(200), primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    service_profile = db.Column(db.String(200), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def formatted_timestamp(self):
        if self.timestamp:
            return self.timestamp.strftime("%B %d, %Y %I:%M %p")
        return None


class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    super_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)