"""
Blueprint para el módulo de Cobranzas
"""
from flask import Blueprint

cobranzas_bp = Blueprint('cobranzas', __name__,
                         url_prefix='/cobranzas',
                         template_folder='../../templates/cobranzas')

from . import routes
