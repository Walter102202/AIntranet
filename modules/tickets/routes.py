from flask import render_template, request, redirect, url_for, flash, session
from modules.tickets import tickets_bp
from modules.auth.routes import login_required
from models import Ticket

@tickets_bp.route('/')
@login_required
def index():
    """Lista de tickets"""
    # Mostrar tickets del usuario
    my_tickets = Ticket.get_by_user(session['user_id'])

    # Si es admin o soporte, mostrar todos
    if session.get('rol') in ['admin', 'soporte']:
        all_tickets = Ticket.get_all()
    else:
        all_tickets = []

    return render_template('tickets/index.html',
                         my_tickets=my_tickets,
                         all_tickets=all_tickets)

@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crear nuevo ticket"""
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        prioridad = request.form.get('prioridad')

        Ticket.create(titulo, descripcion, categoria, prioridad, session['user_id'])
        flash('Ticket creado exitosamente', 'success')
        return redirect(url_for('tickets.index'))

    return render_template('tickets/create.html')

@tickets_bp.route('/<int:ticket_id>')
@login_required
def detail(ticket_id):
    """Ver detalle de ticket"""
    ticket = Ticket.get_by_id(ticket_id)

    if not ticket:
        flash('Ticket no encontrado', 'danger')
        return redirect(url_for('tickets.index'))

    # Verificar permisos
    if ticket['solicitante_id'] != session['user_id'] and session.get('rol') not in ['admin', 'soporte']:
        flash('No tienes permisos para ver este ticket', 'danger')
        return redirect(url_for('tickets.index'))

    comments = Ticket.get_comments(ticket_id)

    return render_template('tickets/detail.html', ticket=ticket, comments=comments)

@tickets_bp.route('/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    """Agregar comentario a ticket"""
    ticket = Ticket.get_by_id(ticket_id)

    if not ticket:
        flash('Ticket no encontrado', 'danger')
        return redirect(url_for('tickets.index'))

    # Verificar permisos
    if ticket['solicitante_id'] != session['user_id'] and session.get('rol') not in ['admin', 'soporte']:
        flash('No tienes permisos para comentar en este ticket', 'danger')
        return redirect(url_for('tickets.index'))

    comentario = request.form.get('comentario')
    if comentario:
        Ticket.add_comment(ticket_id, session['user_id'], comentario)
        flash('Comentario agregado exitosamente', 'success')

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

@tickets_bp.route('/<int:ticket_id>/update_status', methods=['POST'])
@login_required
def update_status(ticket_id):
    """Actualizar estado del ticket"""
    if session.get('rol') not in ['admin', 'soporte']:
        flash('No tienes permisos para actualizar tickets', 'danger')
        return redirect(url_for('tickets.index'))

    estado = request.form.get('estado')
    asignado_a = request.form.get('asignado_a') or None

    Ticket.update_status(ticket_id, estado, asignado_a)
    flash('Estado del ticket actualizado', 'success')

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))
