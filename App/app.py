import uuid
from flask import Flask, request, redirect, url_for,flash, render_template
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from .Users import users_bp
from .Technicians import technicians_bp
from .Admin import admin_bp
from .models import Users, Admin
from .config import DevelopmentConfig, ProductionConfig
from .extensions import migrate, db, mail, moment, login_manager

def create_app():
    app = Flask(__name__)

    # configurations for api to be running
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
                return redirect(f"/users/dashboard")
            
            
            #  Technicians view
            elif existingUser and existingUser.check_password(password) == True and existingUser.role == "technician" and existingUser.is_active == True:
                login_user(existingUser)
                return redirect("/technician/dashboard")
            
            else:
                flash("Invalid email or password.")
                return redirect(url_for('login'))
            
        return render_template('Login.html')
    
    @app.route("/auth/register", methods=["GET", "POST"])
    def register():
        if request.method == 'POST':
            # Handle registration logic here
            # For example, save user data to the database
            # After successful registration, redirect to login page

            username = request.form.get("full_name")
            email = request.form.get("email")
            phone_number = request.form.get("phone-number")
            password = request.form.get("password")
            role = request.form.get("role")
            gender = request.form.get("gender")
            profile_photo = request.files.get('profile-picture')
            profile_id = request.files.get('profile-id')


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

                # Handle profile ID upload
                if profile_id and profile_id.filename:
                    try:
                        new_user.profile_id = profile_id.read()
                    except Exception as e:
                        flash("Error uploading profile ID. Please try again.")
                        return redirect(url_for('register'))

                new_user.role = role

                db.session.add(new_user)
                db.session.commit()
                flash('Account successfully created.')
                return redirect(url_for('login'))
            
        return render_template('Register.html')
    
    @app.route('/auth/admin/login', methods=["GET", "POST"])
    def Admin_Login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            # Add logic to verify admin credentials
            admin = Admin.query.filter_by(email=email).first()

            # checking if the creditenials for admin are correct.
            if admin and admin.check_password(password):
                login_user(admin)
                return redirect(url_for('admin.admin_dashboard'))
            else:
                flash("Invalid credentials or not an admin.", "danger")
                return redirect(url_for('Admin_Login'))
        return render_template('admin.login.html')

    @app.route('/auth/admin/register', methods=['GET', 'POST'])
    def Admin_Register():
        if request.method == "POST":
            email = request.form.get("email")
            username = request.form.get("username")
            password = request.form.get("password")
            # Add logic to create a new admin user
            if Admin.query.filter_by(email=email).first():
                flash("Email already registered.", "warning")
                return redirect(url_for('Admin_Login'))
            
            else:
                new_admin = Admin(email=email, username=username, super_admin=True)
                new_admin.set_password(password)
                db.session.add(new_admin)
                db.session.commit()
                flash("Admin registered successfully!", "success")
                return redirect("/auth/admin/login")

        return render_template('admin.register.html')
    

    @app.route('/logout')
    def logout():
        logout_user()

        flash("Logout Successfully.")
        return redirect(url_for('login'))

    return app