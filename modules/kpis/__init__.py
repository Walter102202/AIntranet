from flask import Blueprint

kpis_bp = Blueprint('kpis', __name__, url_prefix='/kpis')

from . import routes
