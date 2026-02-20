"""
Portal de Intranet Corporativo
Aplicación Flask principal
"""
import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from models import Employee, Announcement, Ticket, Vacation, Document
from database import execute_query

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Importar blueprints
from modules.auth import auth_bp
from modules.employees import employees_bp
from modules.vacations import vacations_bp
from modules.documents import documents_bp
from modules.announcements import announcements_bp
from modules.tickets import tickets_bp
from modules.chatbot import chatbot_bp
from modules.cobranzas import cobranzas_bp
from modules.kpis import kpis_bp

# Crear aplicación
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Inicializar protección CSRF
csrf = CSRFProtect(app)

# Eximir endpoints JSON/API de CSRF (usan autenticación por sesión, no formularios)
csrf.exempt(chatbot_bp)
csrf.exempt('cobranzas.api_ml_comparar_modelos')

# Inicializar rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Límites específicos para rutas sensibles
limiter.limit("5 per minute")(auth_bp)  # Login y autenticación
limiter.limit("30 per minute")(chatbot_bp)  # Chatbot API

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(vacations_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(announcements_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(cobranzas_bp)
app.register_blueprint(kpis_bp)


# Filtros personalizados de Jinja2
@app.template_filter('days_since')
def days_since_filter(date_value):
    """Calcula los días desde una fecha hasta hoy"""
    if not date_value:
        return None
    from datetime import datetime, date
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    elif isinstance(date_value, str):
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()

    today = date.today()
    delta = today - date_value
    return delta.days


@app.route('/')
def index():
    """Página principal - redirige al login o dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))


@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Obtener estadísticas
    stats = {
        'total_employees': 0,
        'total_documents': 0,
        'open_tickets': 0,
        'active_announcements': 0
    }

    # Contar empleados
    employees = Employee.get_all()
    stats['total_employees'] = len(employees) if employees else 0

    # Contar documentos
    documents = Document.get_all()
    stats['total_documents'] = len(documents) if documents else 0

    # Contar tickets abiertos
    query = "SELECT COUNT(*) as count FROM tickets WHERE estado IN ('abierto', 'en_proceso')"
    result = execute_query(query, fetch=True)
    stats['open_tickets'] = result[0]['count'] if result else 0

    # Contar anuncios activos
    announcements_active = Announcement.get_active()
    stats['active_announcements'] = len(announcements_active) if announcements_active else 0

    # Obtener anuncios recientes (últimos 5)
    announcements = announcements_active[:5] if announcements_active else []

    # Obtener datos del empleado actual
    employee = Employee.get_by_user_id(session['user_id'])

    # Obtener vacaciones del empleado
    my_vacations = []
    if employee:
        my_vacations = Vacation.get_by_employee(employee['id'])
        my_vacations = my_vacations[:3] if my_vacations else []

    # Obtener tickets del usuario
    my_tickets = Ticket.get_by_user(session['user_id'])
    my_tickets = my_tickets[:3] if my_tickets else []

    return render_template('dashboard.html',
                         stats=stats,
                         announcements=announcements,
                         my_vacations=my_vacations,
                         my_tickets=my_tickets)


@app.errorhandler(404)
def not_found(error):
    """Página de error 404"""
    return render_template('404.html'), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    """Límite de peticiones excedido"""
    if request.path.startswith('/chatbot/') or request.path.startswith('/cobranzas/api/'):
        return jsonify({'success': False, 'error': 'Demasiadas peticiones. Intenta de nuevo en unos minutos.'}), 429
    flash('Has excedido el límite de peticiones. Intenta de nuevo en unos minutos.', 'warning')
    return redirect(url_for('auth.login')), 429


@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('500.html'), 500


@app.after_request
def set_security_headers(response):
    """Agregar headers de seguridad a todas las respuestas"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if not Config.DEBUG:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.context_processor
def inject_user():
    """Inyectar información del usuario en todos los templates"""
    return dict(session=session)


if __name__ == '__main__':
    import os

    # Crear directorio de uploads si no existe
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)

    print("\n" + "="*50)
    print("PORTAL DE INTRANET CORPORATIVO")
    print("="*50)
    print(f"\nModo: {'DESARROLLO' if Config.DEBUG else 'PRODUCCION'}")
    print("\nServidor iniciado en: http://127.0.0.1:5000")
    print("\nNOTA: Asegúrate de ejecutar 'python init_db.py' primero")
    print("      para inicializar la base de datos.")
    print("\nLas credenciales de acceso están en tu archivo .env")
    print("="*50 + "\n")

    host = '0.0.0.0' if Config.DEBUG else '127.0.0.1'
    app.run(debug=Config.DEBUG, host=host, port=5000)
