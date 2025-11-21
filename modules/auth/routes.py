from flask import render_template, request, redirect, url_for, flash, session, current_app
from modules.auth import auth_bp
from models import User, Employee, Department
from functools import wraps
import msal
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
import requests
import secrets

def login_required(f):
    """Decorador para requerir login en las rutas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))

        user = User.get_by_id(session['user_id'])
        if not user or user['rol'] != 'admin':
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor completa todos los campos', 'danger')
            return render_template('login.html')

        user = User.get_by_username(username)

        if user and User.verify_password(user, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nombre_completo'] = user['nombre_completo']
            session['rol'] = user['rol']

            User.update_last_access(user['id'])

            flash(f'¡Bienvenido, {user["nombre_completo"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@login_required
def users_list():
    """Lista de usuarios (solo para admins)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard'))

    active_users = User.get_all()
    inactive_users = User.get_inactive()
    return render_template('auth/users.html', active_users=active_users, inactive_users=inactive_users)

@auth_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    """Crear nuevo usuario (solo para admins)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para crear usuarios', 'danger')
        return redirect(url_for('dashboard'))

    departments = Department.get_all()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        nombre_completo = request.form.get('nombre_completo')
        rol = request.form.get('rol')
        departamento_id = request.form.get('departamento_id')
        cargo = request.form.get('cargo')

        # Validaciones
        if not all([username, password, email, nombre_completo, rol, departamento_id, cargo]):
            flash('Todos los campos son obligatorios', 'danger')
            return render_template('auth/user_create.html', departments=departments)

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/user_create.html', departments=departments)

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('auth/user_create.html', departments=departments)

        # Verificar si el usuario ya existe
        existing_user = User.get_by_username(username)
        if existing_user:
            flash('El nombre de usuario ya está en uso', 'danger')
            return render_template('auth/user_create.html', departments=departments)

        # Crear el usuario
        try:
            user_id = User.create(username, password, email, nombre_completo, rol)
            if user_id:
                # Crear empleado asociado automáticamente con departamento y cargo personalizados
                Employee.create_from_user(user_id, username, email, nombre_completo, rol,
                                        int(departamento_id), cargo)
                flash(f'Usuario y empleado creados exitosamente para {username}', 'success')
            else:
                flash(f'Usuario {username} creado exitosamente', 'success')
            return redirect(url_for('auth.users_list'))
        except Exception as e:
            flash(f'Error al crear usuario: {str(e)}', 'danger')
            return render_template('auth/user_create.html', departments=departments)

    return render_template('auth/user_create.html', departments=departments)

@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """Editar usuario (solo para admins)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para editar usuarios', 'danger')
        return redirect(url_for('dashboard'))

    user = User.get_by_id(user_id)
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.users_list'))

    # Obtener empleado asociado y departamentos
    employee = Employee.get_by_user_id(user_id)
    departments = Department.get_all()

    if request.method == 'POST':
        email = request.form.get('email')
        nombre_completo = request.form.get('nombre_completo')
        rol = request.form.get('rol')
        departamento_id = request.form.get('departamento_id')
        cargo = request.form.get('cargo')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validaciones
        if not all([email, nombre_completo, rol, departamento_id, cargo]):
            flash('Todos los campos son obligatorios', 'danger')
            return render_template('auth/user_edit.html', user=user, employee=employee, departments=departments)

        # Si se proporciona nueva contraseña, validarla
        if new_password:
            if new_password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('auth/user_edit.html', user=user, employee=employee, departments=departments)

            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'danger')
                return render_template('auth/user_edit.html', user=user, employee=employee, departments=departments)

        # Actualizar el usuario y empleado
        try:
            User.update(user_id, email, nombre_completo, rol)
            if new_password:
                User.update_password(user_id, new_password)

            # Actualizar o crear empleado
            if employee:
                Employee.update_from_user(user_id, email, nombre_completo, int(departamento_id), cargo)
            else:
                Employee.create_from_user(user_id, user['username'], email, nombre_completo, rol,
                                        int(departamento_id), cargo)

            flash('Usuario y empleado actualizados exitosamente', 'success')
            return redirect(url_for('auth.users_list'))
        except Exception as e:
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
            return render_template('auth/user_edit.html', user=user, employee=employee, departments=departments)

    return render_template('auth/user_edit.html', user=user, employee=employee, departments=departments)

@auth_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
def user_deactivate(user_id):
    """Desactivar usuario (solo para admins)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para desactivar usuarios', 'danger')
        return redirect(url_for('dashboard'))

    # No permitir desactivar el propio usuario
    if user_id == session.get('user_id'):
        flash('No puedes desactivar tu propio usuario', 'danger')
        return redirect(url_for('auth.users_list'))

    try:
        User.deactivate(user_id)
        flash('Usuario desactivado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al desactivar usuario: {str(e)}', 'danger')

    return redirect(url_for('auth.users_list'))

@auth_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
def user_activate(user_id):
    """Activar usuario (solo para admins)"""
    if session.get('rol') != 'admin':
        flash('No tienes permisos para activar usuarios', 'danger')
        return redirect(url_for('dashboard'))

    try:
        User.activate(user_id)
        flash('Usuario activado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al activar usuario: {str(e)}', 'danger')

    return redirect(url_for('auth.users_list'))


# ==================== RUTAS OAUTH ====================

@auth_bp.route('/microsoft')
def microsoft_login():
    """Iniciar sesión con Microsoft"""
    # Verificar que las credenciales estén configuradas
    if not current_app.config['MICROSOFT_CLIENT_ID'] or not current_app.config['MICROSOFT_CLIENT_SECRET']:
        flash('La autenticación con Microsoft no está configurada', 'danger')
        return redirect(url_for('auth.login'))

    # Crear cliente MSAL
    msal_app = msal.ConfidentialClientApplication(
        current_app.config['MICROSOFT_CLIENT_ID'],
        authority=current_app.config['MICROSOFT_AUTHORITY'],
        client_credential=current_app.config['MICROSOFT_CLIENT_SECRET']
    )

    # Generar state para CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Generar URL de autorización
    auth_url = msal_app.get_authorization_request_url(
        scopes=current_app.config['MICROSOFT_SCOPE'],
        state=state,
        redirect_uri=current_app.config['MICROSOFT_REDIRECT_URI']
    )

    return redirect(auth_url)


@auth_bp.route('/microsoft/callback')
def microsoft_callback():
    """Callback de Microsoft OAuth"""
    # Verificar state para CSRF protection
    if request.args.get('state') != session.get('oauth_state'):
        flash('Error de autenticación: estado inválido', 'danger')
        return redirect(url_for('auth.login'))

    # Limpiar state
    session.pop('oauth_state', None)

    # Verificar si hay error en la respuesta
    if 'error' in request.args:
        error_description = request.args.get('error_description', 'Error desconocido')
        flash(f'Error de autenticación de Microsoft: {error_description}', 'danger')
        return redirect(url_for('auth.login'))

    # Obtener código de autorización
    code = request.args.get('code')
    if not code:
        flash('Error de autenticación: código no recibido', 'danger')
        return redirect(url_for('auth.login'))

    # Crear cliente MSAL
    msal_app = msal.ConfidentialClientApplication(
        current_app.config['MICROSOFT_CLIENT_ID'],
        authority=current_app.config['MICROSOFT_AUTHORITY'],
        client_credential=current_app.config['MICROSOFT_CLIENT_SECRET']
    )

    # Intercambiar código por token
    try:
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=current_app.config['MICROSOFT_SCOPE'],
            redirect_uri=current_app.config['MICROSOFT_REDIRECT_URI']
        )

        if 'error' in result:
            flash(f'Error al obtener token: {result.get("error_description")}', 'danger')
            return redirect(url_for('auth.login'))

        # Obtener información del usuario
        user_info = result.get('id_token_claims', {})
        oauth_id = user_info.get('oid') or user_info.get('sub')
        email = user_info.get('preferred_username') or user_info.get('email')
        nombre_completo = user_info.get('name', email)

        if not oauth_id or not email:
            flash('Error: No se pudo obtener información del usuario', 'danger')
            return redirect(url_for('auth.login'))

        # Buscar usuario existente por OAuth
        user = User.get_by_oauth('microsoft', oauth_id)

        # Si no existe, buscar por email
        if not user:
            user = User.get_by_email(email)
            if user:
                # Usuario existe con el mismo email pero sin OAuth - actualizar o informar
                flash('Ya existe una cuenta con este email. Por favor contacta al administrador.', 'warning')
                return redirect(url_for('auth.login'))

        # Si no existe, crear nuevo usuario
        if not user:
            user = User.create_oauth_user(
                email=email,
                nombre_completo=nombre_completo,
                oauth_provider='microsoft',
                oauth_id=oauth_id
            )

            if not user:
                flash('Error al crear cuenta de usuario', 'danger')
                return redirect(url_for('auth.login'))

            flash(f'Cuenta creada exitosamente. ¡Bienvenido, {nombre_completo}!', 'success')

        # Crear sesión
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['nombre_completo'] = user['nombre_completo']
        session['rol'] = user['rol']

        User.update_last_access(user['id'])

        flash(f'¡Bienvenido, {user["nombre_completo"]}!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error en la autenticación: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/google')
def google_login():
    """Iniciar sesión con Google"""
    # Verificar que las credenciales estén configuradas
    if not current_app.config['GOOGLE_CLIENT_ID'] or not current_app.config['GOOGLE_CLIENT_SECRET']:
        flash('La autenticación con Google no está configurada', 'danger')
        return redirect(url_for('auth.login'))

    # Generar state para CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Crear configuración del cliente OAuth
    client_config = {
        "web": {
            "client_id": current_app.config['GOOGLE_CLIENT_ID'],
            "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
        }
    }

    # Crear flow de OAuth
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=current_app.config['GOOGLE_SCOPE'],
        redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
    )

    # Generar URL de autorización
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        state=state
    )

    return redirect(auth_url)


@auth_bp.route('/google/callback')
def google_callback():
    """Callback de Google OAuth"""
    # Verificar state para CSRF protection
    if request.args.get('state') != session.get('oauth_state'):
        flash('Error de autenticación: estado inválido', 'danger')
        return redirect(url_for('auth.login'))

    # Limpiar state
    session.pop('oauth_state', None)

    # Verificar si hay error en la respuesta
    if 'error' in request.args:
        error_description = request.args.get('error', 'Error desconocido')
        flash(f'Error de autenticación de Google: {error_description}', 'danger')
        return redirect(url_for('auth.login'))

    # Crear configuración del cliente OAuth
    client_config = {
        "web": {
            "client_id": current_app.config['GOOGLE_CLIENT_ID'],
            "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
        }
    }

    # Crear flow de OAuth
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=current_app.config['GOOGLE_SCOPE'],
        redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
    )

    try:
        # Intercambiar código por token
        flow.fetch_token(authorization_response=request.url)

        # Obtener credenciales
        credentials = flow.credentials

        # Verificar el ID token
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID']
        )

        # Obtener información del usuario
        oauth_id = id_info.get('sub')
        email = id_info.get('email')
        nombre_completo = id_info.get('name', email)
        email_verified = id_info.get('email_verified', False)

        if not oauth_id or not email:
            flash('Error: No se pudo obtener información del usuario', 'danger')
            return redirect(url_for('auth.login'))

        if not email_verified:
            flash('Error: El email de Google no está verificado', 'danger')
            return redirect(url_for('auth.login'))

        # Buscar usuario existente por OAuth
        user = User.get_by_oauth('google', oauth_id)

        # Si no existe, buscar por email
        if not user:
            user = User.get_by_email(email)
            if user:
                # Usuario existe con el mismo email pero sin OAuth - actualizar o informar
                flash('Ya existe una cuenta con este email. Por favor contacta al administrador.', 'warning')
                return redirect(url_for('auth.login'))

        # Si no existe, crear nuevo usuario
        if not user:
            user = User.create_oauth_user(
                email=email,
                nombre_completo=nombre_completo,
                oauth_provider='google',
                oauth_id=oauth_id
            )

            if not user:
                flash('Error al crear cuenta de usuario', 'danger')
                return redirect(url_for('auth.login'))

            flash(f'Cuenta creada exitosamente. ¡Bienvenido, {nombre_completo}!', 'success')

        # Crear sesión
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['nombre_completo'] = user['nombre_completo']
        session['rol'] = user['rol']

        User.update_last_access(user['id'])

        flash(f'¡Bienvenido, {user["nombre_completo"]}!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error en la autenticación: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))
