from flask import render_template, request, redirect, url_for, flash, session
from modules.announcements import announcements_bp
from modules.auth.routes import login_required
from models import Announcement

@announcements_bp.route('/')
@login_required
def index():
    """Lista de anuncios"""
    announcements = Announcement.get_active()
    return render_template('announcements/index.html', announcements=announcements)

@announcements_bp.route('/all')
@login_required
def all_announcements():
    """Todos los anuncios (incluidos expirados)"""
    announcements = Announcement.get_all()
    return render_template('announcements/all.html', announcements=announcements)

@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crear nuevo anuncio"""
    if session.get('rol') not in ['admin']:
        flash('No tienes permisos para crear anuncios', 'danger')
        return redirect(url_for('announcements.index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')
        tipo = request.form.get('tipo')
        prioridad = request.form.get('prioridad')
        fecha_expiracion = request.form.get('fecha_expiracion') or None

        Announcement.create(titulo, contenido, tipo, prioridad, session['user_id'], fecha_expiracion)
        flash('Anuncio creado exitosamente', 'success')
        return redirect(url_for('announcements.index'))

    return render_template('announcements/create.html')

@announcements_bp.route('/view/<int:announcement_id>')
@login_required
def view(announcement_id):
    """Ver detalle de un anuncio"""
    Announcement.increment_views(announcement_id)
    # Aquí podrías implementar una vista detallada
    flash('Vista de anuncio en desarrollo', 'info')
    return redirect(url_for('announcements.index'))
