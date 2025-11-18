from flask import render_template, request, redirect, url_for, flash, session, send_file
from modules.documents import documents_bp
from modules.auth.routes import login_required
from models import Document
from werkzeug.utils import secure_filename
import os
from config import Config

@documents_bp.route('/') # documents_bp viene del archivo init.py
@login_required
def index():
    """Lista de documentos"""
    categoria = request.args.get('categoria')

    if categoria:
        documents = Document.get_by_category(categoria)
    else:
        documents = Document.get_all()

    return render_template('documents/index.html',
                         documents=documents,
                         selected_category=categoria)

@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Subir documento"""
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('Por favor selecciona un archivo', 'danger')
            return render_template('documents/upload.html')

        if not titulo:
            flash('Por favor ingresa un título', 'danger')
            return render_template('documents/upload.html')

        # Crear directorio de uploads si no existe
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Guardar archivo
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Obtener información del archivo
        file_size = os.path.getsize(filepath)
        file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'

        # Guardar en base de datos
        Document.create(
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            nombre_archivo=filename,
            ruta_archivo=filepath,
            tamanio=file_size,
            tipo_archivo=file_type,
            subido_por=session['user_id']
        )

        flash('Documento subido exitosamente', 'success')
        return redirect(url_for('documents.index'))

    return render_template('documents/upload.html')

@documents_bp.route('/download/<int:doc_id>')
@login_required
def download(doc_id):
    """Descargar documento"""
    # Aquí implementarías la descarga del archivo
    Document.increment_downloads(doc_id)
    flash('Función de descarga en desarrollo', 'info')
    return redirect(url_for('documents.index'))
