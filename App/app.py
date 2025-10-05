import uuid
from flask import Flask, request, redirect, url_for,flash, render_template
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from .Users import users_bp
from .Technicians import technicians_bp
from .Admin import admin_bp
from .models import Users
from .config import DevelopmentConfig, ProductionConfig
from .extensions import migrate, login_manager, db, mail, moment

def create_app():
    app = Flask(__name__)

    # configurations for api to be running
    app.config.from_object(DevelopmentConfig)

    # initializing extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(user_id)
    
    # registering all the flask blueprints.
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(technicians_bp)


    with app.app_context():
        # Initialize your database here
        db.create_all()
        pass

   
    @app.route('/')
    @app.route("/login", methods=["GET", "POST"])
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
                return redirect(f"/users/")
            
            
            #  Technical_View
            elif existingUser and existingUser.check_password(password) == True and existingUser.role == "technician" and existingUser.is_active == True:
                login_user(existingUser)
                return redirect(f"/technician/dashboard")
            
            # Unactive Account View
            elif existingUser and existingUser.check_password(password) == True and existingUser.is_active == False:
                flash("Account is not active. Please contact admin.")
                return redirect(url_for('login'))
            
            elif email == 'Admin@gmail.com' and password == 'admin':
                return redirect(f'/admin/')
            
            else:
                flash("Invalid email or password.")
                return redirect(url_for('login'))
        return render_template('Login.html')
    
    @app.route("/register", methods=["GET", "POST"])
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
        
                if not phone_number.isdigit() or len(phone_number) < 10:
                    # Handle invalid phone number case
                    flash("Invalid phone number")
                    return redirect(url_for('register'))
                
                else:
                    new_user.phone_number = phone_number
                
            
                new_user.set_password(password)
                new_user.username = username
                new_user.gender = gender
                new_user.photo = profile_photo.read() if profile_photo else None
                new_user.profile_id = profile_id.read() if profile_id else None
                new_user.role = role

                db.session.add(new_user)
                db.session.commit()
                flash('Account successfully created.')
                return redirect(url_for('login'))
            
        return render_template('Register.html')

    @app.route('/logout')
    def logout():
        logout_user()

        flash("Logout Successfully.")
        return redirect(url_for('login'))

    return app