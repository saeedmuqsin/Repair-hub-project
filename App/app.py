import uuid
from flask import Flask, request, redirect, url_for,flash, render_template
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from .Users import users_bp
from .Technicians import technicians_bp
from .Admin import admin_bp
from .models import Users, Admin, Technician
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
                    return redirect("/technician/dashboard")
                else:
                    login_user(existingUser)
                    return """

      <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        /* Clock rotation animation */
        @keyframes spinSlow {
            from {
                transform: rotate(0deg);
            }

            to {
                transform: rotate(360deg);
            }
        }

        .clock-animate {
            animation: spinSlow 3s linear infinite;
        }

        /* Fade-in animation */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in {
            animation: fadeIn 0.8s ease-out;
        }
    </style>

</head>

<body class="bg-gray-100 flex items-center justify-center min-h-screen">

    <!-- Card -->
    <div class="bg-white shadow-lg rounded-xl p-8 text-center max-w-md w-full fade-in">

        <!-- Animated Clock Icon -->
        <div class="text-blue-400 text-5xl mb-4">

            <i class="fa-solid fa-clock clock-animate"></i>

        </div>

        <!-- Message -->
        <h2 class="text-xl font-semibold text-gray-800 mb-2">
            Profile Pending Approval
        </h2>

        <p class="text-gray-600 text-sm mb-4">
            Your profile has been successfully created.
        </p>

        <p class="text-gray-500 text-sm">
            Please wait within <span class="font-semibold text-gray-700">24 hours</span>
            for approval by the admin.
        </p>

        <!-- Status Badge -->
        <div class="mt-6">

            <a href="/auth/login" class="bg-blue-400 text-white px-4 py-2 rounded-full text-sm font-medium">
                Go back to login
            </a>

        </div>

    </div>

</body>

</html>
"""
            
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
                    
                # checking the role of the user
                # the role of the user is customer then a customer account will be created and 
                # if the role is technician then a technician account will be created.

                if role =="customer":
                    new_user.role = role
                    new_user.role = role
                    db.session.add(new_user)
                    db.session.commit()

                elif role == "technician":
                    new_user.role = role
                    db.session.add(new_user)
                    db.session.commit()

                    login_user(new_user)
                    return redirect(url_for('technicians.create_profile'))
                
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