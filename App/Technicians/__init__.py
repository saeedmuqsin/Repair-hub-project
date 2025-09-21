from flask import Blueprint


technicians_bp = Blueprint(
    'technicians',
    __name__,
    template_folder='templates/technicians',
    static_folder='static/technicians',
    url_prefix='/technician'
)

from . import routes