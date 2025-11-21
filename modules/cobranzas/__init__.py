"""
Blueprint para el módulo de Cobranzas
"""
from modules.cobranzas.routes import routes
from flask import Blueprint

cobranzas_bp = Blueprint('cobranzas', __name__,
                         url_prefix='/cobranzas',
                         template_folder='../../templates/cobranzas')
