import logging
import uuid
from flask import render_template, request, redirect, url_for, flash, session, send_file, abort
from modules.documents import documents_bp
from modules.auth.routes import login_required
from models import Document
from werkzeug.utils import secure_filename
import os
from config import Config

logger = logging.getLogger(__name__)

# Mapeo de extensiones permitidas a tipos MIME válidos
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'xls': ['application/vnd.ms-excel'],
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'txt': ['text/plain'],
    'png': ['image/png'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
}


def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_file_mime(file, extension):
    """Valida que el tipo MIME del archivo coincida con la extensión"""
    allowed_mimes = ALLOWED_MIME_TYPES.get(extension, [])
    if not allowed_mimes:
        return False
    # content_type reportado por el navegador
    return file.content_type in allowed_mimes


@documents_bp.route('/')
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

        # Validar extensión del archivo
        if not allowed_file(file.filename):
            flash('Tipo de archivo no permitido. Formatos aceptados: PDF, DOC, DOCX, XLS, XLSX, TXT, PNG, JPG', 'danger')
            return render_template('documents/upload.html')

        # Obtener extensión y validar MIME type
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

        if not validate_file_mime(file, file_ext):
            logger.warning(
                f"Usuario {session['user_id']} intentó subir archivo con MIME inválido: "
                f"ext={file_ext}, mime={file.content_type}, filename={file.filename}"
            )
            flash('El tipo de archivo no coincide con su extensión', 'danger')
            return render_template('documents/upload.html')

        # Crear directorio de uploads si no existe
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Generar nombre único para evitar colisiones y path traversal
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        # Obtener información del archivo
        file_size = os.path.getsize(filepath)

        # Guardar en base de datos
        Document.create(
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            nombre_archivo=original_filename,
            ruta_archivo=filepath,
            tamanio=file_size,
            tipo_archivo=file_ext,
            subido_por=session['user_id']
        )

        flash('Documento subido exitosamente', 'success')
        return redirect(url_for('documents.index'))

    return render_template('documents/upload.html')

@documents_bp.route('/download/<int:doc_id>')
@login_required
def download(doc_id):
    """Descargar documento"""
    doc = Document.get_by_id(doc_id)
    if not doc:
        flash('Documento no encontrado', 'danger')
        return redirect(url_for('documents.index'))

    filepath = doc.get('ruta_archivo') or doc.get('ruta')
    if not filepath or not os.path.exists(filepath):
        flash('El archivo no está disponible en el servidor', 'danger')
        return redirect(url_for('documents.index'))

    Document.increment_downloads(doc_id)
    return send_file(
        filepath,
        as_attachment=True,
        download_name=doc.get('nombre_archivo', 'documento')
    )
