from flask import redirect
from .extensions import db, mail
from flask_login import UserMixin
from flask_mail import Message
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import LargeBinary as MEDIUMBLOB
from sqlalchemy.types import JSON
import base64, json, psycopg2,random

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
    is_active = db.Column(db.Boolean, default=False)
    booking = db.relationship('Booking', backref="user", cascade="all, delete-orphan")
    technician = db.relationship('Technician',backref="technician", cascade="all, delete-orphan")
    account_activation_code = db.relationship('AccountActivationCode', backref='users', cascade="all, delete-orphan")
    password_reset_tokens = db.relationship('PasswordResetToken', backref='users', cascade="all, delete-orphan")
   
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)
    
    def User_ProfilePhoto(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img
    
    
    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y")
        return None
    
    def TotalBooking(self, id):
        total_booking = len([booking for booking in Booking.query.filter_by(user_id=id).all()])
        return total_booking

    def AccountActivation(self):
        user = Users.query.filter_by(id=self.id).first()
        if user:
            activation_code = AccountActivationCode(
                user_id=user.id,
                code = random.randint(1000,9000),
                expires_at=datetime.now() + timedelta(minutes=10),
                used=False
            )
            db.session.add(activation_code)
            db.session.commit()

        # send the activation code to the user's email address
        # You can use a library like Flask-Mail to send the email with the activation code
        message = Message("Account Activation", recipients=[self.email])
        message.body = f"Your account activation code is: {activation_code.code}. This code will expire in 10 minutes."
        mail.send(message)

        return activation_code.code

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
    invoice = db.relationship("Invoice", backref='Booking', cascade="all, delete-orphan")

    def DisplayDeviceImage(self):
        encoded_img = base64.b64encode(self.device_photo).decode('utf-8')
        return encoded_img
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y %I:%M %p")
        return None
    
    def get_BookingInvoice(self):
        invoice = Invoice.query.filter_by(booking_id=self.id).first()
        return invoice
    
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

    def formatted_created_at(self):
        if self.created_at:
            return self.created_at.strftime("%B %d, %Y ")
        return None
    def Display_photo(self):
        encoded_img = base64.b64encode(self.photo).decode('utf-8')
        return encoded_img

    def get_TotalBooking(self, id):
        total_booking  = Booking.query.filter_by(service_profile = id).count()
        return total_booking
    

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

class Invoice(db.Model):
    __tablename__ = "invoice"
    id = db.Column(db.String(100), primary_key=True, nullable=False)
    parts_cost = db.Column(db.Integer, nullable=True)
    service_cost = db.Column(db.Integer, nullable=True)
    total_cost = db.Column(db.Integer, nullable=True)
    booking_id = db.Column(db.String(200), db.ForeignKey("booking.id", ondelete="CASCADE"), nullable=False)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)

class AccountActivationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)