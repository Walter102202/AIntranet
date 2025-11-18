from flask import render_template, request, redirect, url_for, flash, session
from modules.vacations import vacations_bp
from modules.auth.routes import login_required
from models import Vacation, Employee
from datetime import datetime

@vacations_bp.route('/')
@login_required
def index():
    """Lista de solicitudes de vacaciones"""
    employee = Employee.get_by_user_id(session['user_id'])

    if employee:
        my_vacations = Vacation.get_by_employee(employee['id'])
    else:
        my_vacations = []

    # Si es admin o RRHH, mostrar todas las solicitudes
    if session.get('rol') in ['admin', 'rrhh']:
        all_vacations = Vacation.get_all()
    else:
        all_vacations = []

    return render_template('vacations/index.html',
                         my_vacations=my_vacations,
                         all_vacations=all_vacations)

@vacations_bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_vacation():
    """Solicitar vacaciones"""
    employee = Employee.get_by_user_id(session['user_id'])

    if not employee:
        flash('No tienes un perfil de empleado asociado', 'danger')
        return redirect(url_for('vacations.index'))

    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        tipo = request.form.get('tipo')
        motivo = request.form.get('motivo')

        # Calcular días
        start = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        end = datetime.strptime(fecha_fin, '%Y-%m-%d')
        dias = (end - start).days + 1

        if dias <= 0:
            flash('La fecha de fin debe ser posterior a la fecha de inicio', 'danger')
            return render_template('vacations/request.html')

        Vacation.create(employee['id'], fecha_inicio, fecha_fin, dias, tipo, motivo)
        flash('Solicitud de vacaciones creada exitosamente', 'success')
        return redirect(url_for('vacations.index'))

    return render_template('vacations/request.html')

@vacations_bp.route('/approve/<int:vacation_id>')
@login_required
def approve(vacation_id):
    """Aprobar solicitud de vacaciones"""
    if session.get('rol') not in ['admin', 'rrhh']:
        flash('No tienes permisos para aprobar solicitudes', 'danger')
        return redirect(url_for('vacations.index'))

    Vacation.update_status(vacation_id, 'aprobada', session['user_id'])
    flash('Solicitud aprobada exitosamente', 'success')
    return redirect(url_for('vacations.index'))

@vacations_bp.route('/reject/<int:vacation_id>', methods=['POST'])
@login_required
def reject(vacation_id):
    """Rechazar solicitud de vacaciones"""
    if session.get('rol') not in ['admin', 'rrhh']:
        flash('No tienes permisos para rechazar solicitudes', 'danger')
        return redirect(url_for('vacations.index'))

    comentarios = request.form.get('comentarios', 'Sin comentarios')
    Vacation.update_status(vacation_id, 'rechazada', session['user_id'], comentarios)
    flash('Solicitud rechazada', 'info')
    return redirect(url_for('vacations.index'))
