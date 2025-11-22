"""
Rutas del módulo de KPIs con Power BI
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from modules.kpis import kpis_bp
from modules.auth.routes import login_required
from models import PowerBIReport
from modules.chatbot.screenshot_service import ScreenshotService
import logging

logger = logging.getLogger(__name__)


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


@kpis_bp.route('/screenshot/<int:report_id>')
@login_required
def get_screenshot(report_id):
    """
    Obtiene screenshot de un reporte PowerBI para análisis con IA

    Este endpoint es usado internamente por el chatbot para capturar
    una imagen del reporte y analizarla con el modelo de visión.

    Args:
        report_id: ID del reporte a capturar

    Returns:
        JSON con el screenshot en base64 o error
    """
    try:
        # Obtener reporte
        report = PowerBIReport.get_by_id(report_id)
        if not report:
            logger.warning(f"Intento de screenshot de reporte inexistente: {report_id}")
            return jsonify({
                'success': False,
                'error': f'Reporte con ID {report_id} no encontrado'
            }), 404

        # Verificar que el reporte esté activo
        if not report.get('activo', True):
            logger.warning(f"Intento de screenshot de reporte inactivo: {report_id}")
            return jsonify({
                'success': False,
                'error': 'El reporte no está activo'
            }), 403

        logger.info(f"Usuario {session.get('username')} solicitó screenshot del reporte {report_id}: {report['titulo']}")

        # Capturar screenshot del reporte
        screenshot_base64 = ScreenshotService.capture_powerbi_report(
            embed_url=report['embed_url'],
            width=1920,
            height=1080,
            wait_time=8000  # 8 segundos para que cargue PowerBI
        )

        logger.info(f"Screenshot del reporte {report_id} capturado exitosamente")

        return jsonify({
            'success': True,
            'report': {
                'id': report['id'],
                'titulo': report['titulo'],
                'descripcion': report.get('descripcion', ''),
                'categoria': report.get('categoria', 'general')
            },
            'screenshot': screenshot_base64,
            'metadata': {
                'size': len(screenshot_base64),
                'format': 'base64'
            }
        })

    except Exception as e:
        logger.error(f"Error capturando screenshot del reporte {report_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error al capturar el reporte: {str(e)}'
        }), 500
