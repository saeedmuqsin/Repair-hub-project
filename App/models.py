from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.types import JSON
import base64
import json

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(200), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(50), nullable=False)  # e.g., 'customer', 'technician'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    photo = db.Column(MEDIUMBLOB, nullable=True)
    booking = db.relationship('Booking', backref="user")
    business_profile = db.relationship(
        'BusinessProfile',
        backref="technician",
        cascade="all, delete-orphan"
    )
   
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)
    
    def Display_UserProfilePhoto(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img

class Booking(db.Model):
    __tablename__ = "booking"
    id = db.Column(db.String(200), primary_key=True)
    device_type = db.Column(db.String(200), nullable = False)
    problem  = db.Column(db.String(150), nullable = False)
    problem_description = db.Column(db.Text, nullable = False)
    status = db.Column(db.String(200), nullable=False, default='Pending')
    location = db.Column(db.String(100),nullable = False)
    device_photo = db.Column(MEDIUMBLOB, nullable = False)
    user_id = db.Column(db.String(200), db.ForeignKey('users.id'), nullable=False,)
    service_profile = db.Column(db.String(200), db.ForeignKey('business_profiles.id', ondelete='CASCADE'))

    def Display_deviceImage(self):
        encoded_img = base64.b64encode(self.device_photo).decode('utf-8')
        return encoded_img
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y %I:%M %p")
        return None


class BusinessProfile(db.Model):
    __tablename__ = 'business_profiles'
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    services_offered = db.Column(JSON, nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(MEDIUMBLOB, nullable=False)
    technician_id = db.Column(db.String(200), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_approved = db.Column(db.Boolean, default=False)
    booking = db.relationship('Booking', backref='business_profile', lazy=True, cascade="all, delete-orphan")


    def Display_photo(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img
    
    def get_services_list(self):
        if isinstance(self.services_offered, list):
            return self.services_offered
        elif isinstance(self.services_offered, dict):
            return list(self.services_offered.values())
        elif isinstance(self.services_offered, str):
            try:
                data = json.loads(self.services_offered)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return list(data.values())
            except Exception:
                return []
        return []