from datetime import datetime, timedelta
import token
from turtle import reset
import uuid, secrets
from flask import Flask, jsonify, request, redirect, url_for,flash, render_template
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from .Users import users_bp
from .Technicians import technicians_bp
from .Admin import admin_bp
from .models import Users, Admin, Technician, PasswordResetToken, AccountActivationCode
from .config import DevelopmentConfig, ProductionConfig
from .extensions import migrate, db, mail, moment, login_manager

def create_app():
    app = Flask(__name__)

    # configurations for api to be running
    # Temporarily switch to DevelopmentConfig for local development
    app.config.from_object(DevelopmentConfig)

    # initializing extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'login'
    @login_manager.user_loader
    def load_user(user_id):
        # Validate user_id parameter
        if not user_id:
            return None

        try:
            # Try to load from Users table first
            user = Users.query.get(user_id)
            if user and user.is_active:
                return user

            # If not found in Users, try Admin table
            try:
                admin_id = int(user_id)
                admin = Admin.query.get(admin_id)
                return admin
            
            except (ValueError, TypeError):
                # user_id is not a valid integer for Admin
                return None

        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error loading user {user_id}: {str(e)}")
            return None
    

    # registering all the flask blueprints.
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(technicians_bp)


    with app.app_context():
        # Initialize your database here and creates all models as tables in
        # the database
        db.create_all()

    @app.route("/")
    @app.route("/auth/login", methods=["GET", "POST"])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get("password")

            # --> validating credientials
            existingUser = Users.query.filter_by(email=email).first()

            # Customers view 
            if existingUser and existingUser.check_password(password) == True and existingUser.role == "customer" and existingUser.is_active == True:
                # Login successful
                login_user(existingUser)
                return redirect(f"/users/dashboard?id={current_user.id}")
            
            
            #  Technicians view
            elif existingUser and existingUser.check_password(password) == True and existingUser.role == "technician" and existingUser.is_active == True:
                if Technician.query.filter_by(user_id= existingUser.id, is_approved=True).first():
                    login_user(existingUser)
                    return redirect(f'/technician/dashboard?profile={current_user.id}')
                
                elif Technician.query.filter_by(user_id= existingUser.id, is_approved=False).first():
                    return render_template('PendingApproval.html')

                else:
                    login_user(existingUser)
                    return redirect('/technician/create_profile')
                
            elif email == "admin@info.com" and password =='admin':
                return redirect("/admin/dashboard")

            elif existingUser and existingUser.check_password(password) == True and existingUser.role == "customer" and existingUser.is_active == False:
                flash("Your account is not activated yet. Please check your email for the activation code.")
                return redirect(url_for('account_activation'))
            
            else:
                flash("Invalid email or password.")
                return redirect(url_for('login'))
            
        return render_template('Login.html')

    @app.route("/account-activation", methods=["GET", "POST"])
    def account_activation():
        account_activation_code = request.args.get("code")
        if request.method == "POST":
            input_code = request.form.get("activation_code")
            activation_record = AccountActivationCode.query.filter_by(code=input_code, used=False).first()

            if activation_record and activation_record.expires_at > datetime.now():
                user = Users.query.filter_by(id=activation_record.user_id).first()
                if user:
                    user.is_active = True
                    activation_record.used = True
                    db.session.commit()
                    flash("Account activated successfully. Please log in.")
                    return redirect('/auth/login')
                
            else:
                flash("Invalid or expired activation code. Please try again.")
                user.AccountActivation()
                return redirect('/account-activation')
        
        return render_template('AccountActivation.html', code=account_activation_code)   
    
    @app.route("/auth/register", methods=["GET", "POST"])
    def register():
        if request.method == 'POST':
            # Handle registration logic here
            # For example, save user data to the database
            # After successful registration, redirect to login page

            username = request.form.get("username")
            email = request.form.get("email")
            phone_number = request.form.get("phone-number")
            password = request.form.get("password")
            role = request.form.get("role")
            gender = request.form.get("gender")
            profile_photo = request.files.get('profile-photo')


            existing_user = Users.query.filter((Users.email == email) | (Users.phone_number == phone_number)).first()
            if existing_user:
                # Handle user already exists case
                flash("Account already exists.")
                return redirect(url_for('login'))
                
            else:
                new_user = Users()
                # Generate a unique ID for the user

                id = str(uuid.uuid4())
                new_user.id = id

                new_user.email = email

                # Validate phone number
                if not phone_number or not phone_number.isdigit() or len(phone_number) < 10:
                    flash("Invalid phone number. Please enter a valid phone number with at least 10 digits.")
                    return redirect(url_for('register'))

                new_user.phone_number = phone_number
                
            
                new_user.set_password(password)
                new_user.username = username
                new_user.gender = gender

                # Handle profile photo upload
                if profile_photo and profile_photo.filename:
                    try:
                        new_user.photo = profile_photo.read()
                    except Exception as e:
                        flash("Error uploading profile photo. Please try again.")
                        return redirect(url_for('register'))

                # checking the role of the user
                # the role of the user is customer then a customer account will be created and 
                # if the role is technician then a technician account will be created.

                if role =="customer":
                    new_user.role = role
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect(f'/account-activation?code={new_user.AccountActivation()}')

                elif role == "technician":
                    new_user.role = role
                    db.session.add(new_user)
                    db.session.commit()
                    # new_user.AccountActivation()
                    return redirect(f'/account-activation?code={new_user.AccountActivation()}')
                                                
        return render_template('Register.html')
    
    @app.route('/forget_password', methods=["GET", "POST"])
    def forget_password():
        if request.method == "POST":
            email = request.form.get("email")
            # Add logic to handle password reset

            # checking if the user's email really exists in the database or not.
            user = Users.query.filter_by(email=email).first()
            if user:
                token = secrets.token_urlsafe(32)
                reset_token = PasswordResetToken(
                    user_id=user.id,
                    token=token,
                    expires_at=datetime.now() + timedelta(minutes=10)
                )
                db.session.add(reset_token)
                db.session.commit()

                message = Message("Password Reset Request", recipients=[email])
                reset_link = f"http://127.0.0.1:5000/reset_password/{token}"
                message.body = f"Click the link to reset your password: {reset_link}"
                mail.send(message)

                # after email hase been sent then
                # redirects to the login page 
                flash("Password reset link has been sent to your email.")
                return redirect('/auth/login')
        return render_template('forget_password.html')
    

    # @app.route('/reset_password/<token>')
    # def reset_password(token):
    #     return render_template("reset_password.html", token=token)
    
    @app.route('/reset_password/<token>', methods=["GET", "POST"])
    def Reset_password(token):
        if request.method == "POST":
            reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
            print(token)
            if not reset or reset.expires_at < datetime.now():
                flash("Invalid or expired token.")
                return redirect('/auth/login')

            new_password = request.form.get('new_password')
            print(new_password)

            user = Users.query.filter_by(id=reset.user_id).first()
            user.password = generate_password_hash(new_password)

            reset.used = True
            db.session.commit()

            flash("Password reset successful. Please log in with your new password.")
            return redirect('/auth/login')
        return render_template("reset_password.html", token=token)

    @app.route('/logout')
    def logout():
        logout_user()

        flash("Logout Successfully.")
        return redirect(url_for('login'))


    @app.route("/logout/admin")
    def Admin_Logout():
        flash("Successfully logout admin account")
        return redirect('/auth/login')

    return app