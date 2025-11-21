"""
Portal de Intranet Corporativo
Aplicación Flask principal
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from flask import Flask, render_template, redirect, url_for, session
from config import Config
from models import Employee, Announcement, Ticket, Vacation, Document
from database import execute_query

# Importar blueprints
from modules.auth import auth_bp
from modules.employees import employees_bp
from modules.vacations import vacations_bp
from modules.documents import documents_bp
from modules.announcements import announcements_bp
from modules.tickets import tickets_bp
from modules.chatbot import chatbot_bp
from modules.cobranzas import cobranzas_bp

# Crear aplicación
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(vacations_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(announcements_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(cobranzas_bp)


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


@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('500.html'), 500


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
    print("\nServidor iniciado en: http://127.0.0.1:5000")
    print("\nNOTA: Asegúrate de ejecutar 'python init_db.py' primero")
    print("      para inicializar la base de datos.")
    print("\nLas credenciales de acceso están en tu archivo .env")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
