"""
Rutas del módulo de KPIs con Power BI
"""
from flask import render_template, request, redirect, url_for, flash, session
from modules.kpis import kpis_bp
from modules.auth.routes import login_required
from models import PowerBIReport


@kpis_bp.route('/')
@login_required
def index():
    """Lista de reportes de Power BI"""
    reports = PowerBIReport.get_all()
    return render_template('kpis/index.html', reports=reports)


@kpis_bp.route('/view/<int:report_id>')
@login_required
def view(report_id):
    """Ver un reporte específico en pantalla completa"""
    report = PowerBIReport.get_by_id(report_id)
    if not report:
        flash('Reporte no encontrado', 'danger')
        return redirect(url_for('kpis.index'))
    return render_template('kpis/view.html', report=report)


@kpis_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crear un nuevo reporte de Power BI (solo admin)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para crear reportes', 'danger')
        return redirect(url_for('kpis.index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        embed_url = request.form.get('embed_url', '').strip()
        categoria = request.form.get('categoria', 'general')

        if not titulo or not embed_url:
            flash('Título y URL de embed son requeridos', 'danger')
            return render_template('kpis/create.html')

        PowerBIReport.create(
            titulo=titulo,
            descripcion=descripcion,
            embed_url=embed_url,
            categoria=categoria,
            creado_por=session['user_id']
        )
        flash('Reporte creado exitosamente', 'success')
        return redirect(url_for('kpis.index'))

    return render_template('kpis/create.html')


@kpis_bp.route('/edit/<int:report_id>', methods=['GET', 'POST'])
@login_required
def edit(report_id):
    """Editar un reporte existente (solo admin)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para editar reportes', 'danger')
        return redirect(url_for('kpis.index'))

    report = PowerBIReport.get_by_id(report_id)
    if not report:
        flash('Reporte no encontrado', 'danger')
        return redirect(url_for('kpis.index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        embed_url = request.form.get('embed_url', '').strip()
        categoria = request.form.get('categoria', 'general')
        activo = request.form.get('activo') == 'on'

        if not titulo or not embed_url:
            flash('Título y URL de embed son requeridos', 'danger')
            return render_template('kpis/edit.html', report=report)

        PowerBIReport.update(report_id, titulo, descripcion, embed_url, categoria, activo)
        flash('Reporte actualizado exitosamente', 'success')
        return redirect(url_for('kpis.index'))

    return render_template('kpis/edit.html', report=report)


@kpis_bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete(report_id):
    """Eliminar un reporte (solo admin)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para eliminar reportes', 'danger')
        return redirect(url_for('kpis.index'))

    PowerBIReport.delete(report_id)
    flash('Reporte eliminado', 'success')
    return redirect(url_for('kpis.index'))
