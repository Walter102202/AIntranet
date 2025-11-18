from flask import render_template, request, redirect, url_for, flash, session
from modules.auth import auth_bp
from models import User, Employee, Department
from functools import wraps

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
