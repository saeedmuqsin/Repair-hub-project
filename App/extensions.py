# extensions.py handles the registration of Flask extensions and blueprints.
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_mail import Mail

db = SQLAlchemy()

migrate = Migrate()
moment = Moment()
mail = Mail()

# login manager for users 
login_manager = LoginManager()