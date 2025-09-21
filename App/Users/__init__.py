from flask import Blueprint

# Create a Blueprint for user-related routes
# - 'users' is the blueprint name
# - __name__ helps Flask locate resources
# - template_folder specifies where to find HTML templates for this blueprint
# - static_folder specifies where to find static files (CSS, JS, images) for this blueprint
users_bp = Blueprint(
    'users',
    __name__,
    template_folder='templates/users',
    static_folder='static/users',
    url_prefix='/users'
)

from . import routes  # Import views to register routes with the blueprint