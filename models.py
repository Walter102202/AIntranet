"""
Modelos para interactuar con la base de datos
"""
from database import execute_query
from werkzeug.security import check_password_hash, generate_password_hash

class User:
    @staticmethod
    def get_by_username(username):
        """Obtiene un usuario por su username"""
        query = "SELECT * FROM usuarios WHERE username = %s AND activo = TRUE"
        result = execute_query(query, (username,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_id(user_id):
        """Obtiene un usuario por su ID"""
        query = "SELECT * FROM usuarios WHERE id = %s"
        result = execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def verify_password(user, password):
        """Verifica la contraseña del usuario"""
        return check_password_hash(user['password_hash'], password)

    @staticmethod
    def update_last_access(user_id):
        """Actualiza el último acceso del usuario"""
        query = "UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s"
        execute_query(query, (user_id,))

    @staticmethod
    def get_all():
        """Obtiene todos los usuarios activos"""
        query = "SELECT id, username, email, nombre_completo, rol, fecha_creacion FROM usuarios WHERE activo = TRUE ORDER BY fecha_creacion DESC"
        return execute_query(query, fetch=True)

    @staticmethod
    def create(username, password, email, nombre_completo, rol='empleado'):
        """Crea un nuevo usuario"""
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO usuarios (username, password_hash, email, nombre_completo, rol, activo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """
        return execute_query(query, (username, password_hash, email, nombre_completo, rol))

    @staticmethod
    def update(user_id, email, nombre_completo, rol):
        """Actualiza un usuario existente"""
        query = """
            UPDATE usuarios
            SET email = %s, nombre_completo = %s, rol = %s
            WHERE id = %s
        """
        return execute_query(query, (email, nombre_completo, rol, user_id))

    @staticmethod
    def update_password(user_id, new_password):
        """Actualiza la contraseña de un usuario"""
        password_hash = generate_password_hash(new_password)
        query = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
        return execute_query(query, (password_hash, user_id))

    @staticmethod
    def get_inactive():
        """Obtiene todos los usuarios inactivos"""
        query = "SELECT id, username, email, nombre_completo, rol, fecha_creacion FROM usuarios WHERE activo = FALSE ORDER BY fecha_creacion DESC"
        return execute_query(query, fetch=True)

    @staticmethod
    def deactivate(user_id):
        """Desactiva un usuario"""
        query = "UPDATE usuarios SET activo = FALSE WHERE id = %s"
        return execute_query(query, (user_id,))

    @staticmethod
    def activate(user_id):
        """Activa un usuario"""
        query = "UPDATE usuarios SET activo = TRUE WHERE id = %s"
        return execute_query(query, (user_id,))


class Employee:
    @staticmethod
    def get_all():
        """Obtiene todos los empleados con información de departamento"""
        query = """
            SELECT e.*, d.nombre as departamento_nombre
            FROM empleados e
            LEFT JOIN departamentos d ON e.departamento_id = d.id
            WHERE e.activo = TRUE
            ORDER BY e.apellido, e.nombre
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(employee_id):
        """Obtiene un empleado por su ID"""
        query = """
            SELECT e.*, d.nombre as departamento_nombre
            FROM empleados e
            LEFT JOIN departamentos d ON e.departamento_id = d.id
            WHERE e.id = %s
        """
        result = execute_query(query, (employee_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_user_id(user_id):
        """Obtiene un empleado por el ID de usuario"""
        query = """
            SELECT e.*, d.nombre as departamento_nombre
            FROM empleados e
            LEFT JOIN departamentos d ON e.departamento_id = d.id
            WHERE e.usuario_id = %s
        """
        result = execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def search(search_term):
        """Busca empleados por nombre, apellido, email o cargo"""
        query = """
            SELECT e.*, d.nombre as departamento_nombre
            FROM empleados e
            LEFT JOIN departamentos d ON e.departamento_id = d.id
            WHERE e.activo = TRUE
            AND (e.nombre LIKE %s OR e.apellido LIKE %s OR e.email LIKE %s OR e.cargo LIKE %s)
            ORDER BY e.apellido, e.nombre
        """
        search_pattern = f"%{search_term}%"
        return execute_query(query, (search_pattern, search_pattern, search_pattern, search_pattern), fetch=True)

    @staticmethod
    def create_from_user(user_id, username, email, nombre_completo, rol, departamento_id=None, cargo=None):
        """Crea un empleado automáticamente desde un usuario"""
        from datetime import date

        # Separar nombre completo en nombre y apellido
        nombre_completo_parts = nombre_completo.split()
        if len(nombre_completo_parts) >= 2:
            nombre = nombre_completo_parts[0]
            apellido = ' '.join(nombre_completo_parts[1:])
        else:
            nombre = nombre_completo
            apellido = ''

        # Si no se proporciona departamento o cargo, determinarlos según el rol
        if departamento_id is None or cargo is None:
            if rol == 'admin':
                departamento_id = departamento_id or 1  # Tecnología
                cargo = cargo or 'Administrador de Sistemas'
            elif rol == 'rrhh':
                departamento_id = departamento_id or 2  # Recursos Humanos
                cargo = cargo or 'Especialista de RRHH'
            elif rol == 'soporte':
                departamento_id = departamento_id or 1  # Tecnología
                cargo = cargo or 'Técnico de Soporte'
            else:  # empleado
                departamento_id = departamento_id or 4  # Operaciones
                cargo = cargo or 'Empleado'

        query = """
            INSERT INTO empleados (
                usuario_id, nombre, apellido, email, telefono, extension,
                departamento_id, cargo, fecha_ingreso, activo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (
            user_id,
            nombre,
            apellido,
            email,
            '555-0000',  # Teléfono por defecto
            '100',       # Extensión por defecto
            departamento_id,
            cargo,
            date.today(),
            True
        ))

    @staticmethod
    def update_from_user(user_id, email, nombre_completo, departamento_id, cargo):
        """Actualiza un empleado desde los datos del usuario"""
        # Separar nombre completo en nombre y apellido
        nombre_completo_parts = nombre_completo.split()
        if len(nombre_completo_parts) >= 2:
            nombre = nombre_completo_parts[0]
            apellido = ' '.join(nombre_completo_parts[1:])
        else:
            nombre = nombre_completo
            apellido = ''

        query = """
            UPDATE empleados
            SET nombre = %s, apellido = %s, email = %s, departamento_id = %s, cargo = %s
            WHERE usuario_id = %s
        """
        return execute_query(query, (nombre, apellido, email, departamento_id, cargo, user_id))


class Vacation:
    @staticmethod
    def get_all():
        """Obtiene todas las solicitudes de vacaciones"""
        query = """
            SELECT v.*, e.nombre, e.apellido, e.email,
                   u.nombre_completo as aprobador_nombre
            FROM vacaciones v
            JOIN empleados e ON v.empleado_id = e.id
            LEFT JOIN usuarios u ON v.aprobador_id = u.id
            ORDER BY v.fecha_solicitud DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_employee(employee_id):
        """Obtiene las solicitudes de vacaciones de un empleado"""
        query = """
            SELECT v.*, u.nombre_completo as aprobador_nombre
            FROM vacaciones v
            LEFT JOIN usuarios u ON v.aprobador_id = u.id
            WHERE v.empleado_id = %s
            ORDER BY v.fecha_solicitud DESC
        """
        return execute_query(query, (employee_id,), fetch=True)

    @staticmethod
    def create(employee_id, fecha_inicio, fecha_fin, dias, tipo, motivo):
        """Crea una nueva solicitud de vacaciones"""
        query = """
            INSERT INTO vacaciones (empleado_id, fecha_inicio, fecha_fin, dias_solicitados, tipo, motivo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (employee_id, fecha_inicio, fecha_fin, dias, tipo, motivo))

    @staticmethod
    def update_status(vacation_id, estado, aprobador_id, comentarios=None):
        """Actualiza el estado de una solicitud de vacaciones"""
        query = """
            UPDATE vacaciones
            SET estado = %s, aprobador_id = %s, fecha_respuesta = NOW(), comentarios_aprobador = %s
            WHERE id = %s
        """
        return execute_query(query, (estado, aprobador_id, comentarios, vacation_id))


class Document:
    @staticmethod
    def get_all():
        """Obtiene todos los documentos activos"""
        query = """
            SELECT d.*, u.nombre_completo as subido_por_nombre
            FROM documentos d
            JOIN usuarios u ON d.subido_por = u.id
            WHERE d.activo = TRUE
            ORDER BY d.fecha_subida DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_category(categoria):
        """Obtiene documentos por categoría"""
        query = """
            SELECT d.*, u.nombre_completo as subido_por_nombre
            FROM documentos d
            JOIN usuarios u ON d.subido_por = u.id
            WHERE d.activo = TRUE AND d.categoria = %s
            ORDER BY d.fecha_subida DESC
        """
        return execute_query(query, (categoria,), fetch=True)

    @staticmethod
    def create(titulo, descripcion, categoria, nombre_archivo, ruta_archivo, tamanio, tipo_archivo, subido_por):
        """Crea un nuevo documento"""
        query = """
            INSERT INTO documentos (titulo, descripcion, categoria, nombre_archivo, ruta_archivo,
                                  tamanio, tipo_archivo, subido_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (titulo, descripcion, categoria, nombre_archivo, ruta_archivo,
                                    tamanio, tipo_archivo, subido_por))

    @staticmethod
    def increment_downloads(doc_id):
        """Incrementa el contador de descargas"""
        query = "UPDATE documentos SET descargas = descargas + 1 WHERE id = %s"
        execute_query(query, (doc_id,))


class Announcement:
    @staticmethod
    def get_active():
        """Obtiene anuncios activos y no expirados"""
        query = """
            SELECT a.*, u.nombre_completo as autor_nombre
            FROM anuncios a
            JOIN usuarios u ON a.autor_id = u.id
            WHERE a.activo = TRUE
            AND (a.fecha_expiracion IS NULL OR a.fecha_expiracion >= CURDATE())
            ORDER BY a.fecha_publicacion DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_all():
        """Obtiene todos los anuncios"""
        query = """
            SELECT a.*, u.nombre_completo as autor_nombre
            FROM anuncios a
            JOIN usuarios u ON a.autor_id = u.id
            ORDER BY a.fecha_publicacion DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def create(titulo, contenido, tipo, prioridad, autor_id, fecha_expiracion=None):
        """Crea un nuevo anuncio"""
        query = """
            INSERT INTO anuncios (titulo, contenido, tipo, prioridad, autor_id, fecha_expiracion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (titulo, contenido, tipo, prioridad, autor_id, fecha_expiracion))

    @staticmethod
    def increment_views(announcement_id):
        """Incrementa el contador de vistas"""
        query = "UPDATE anuncios SET vistas = vistas + 1 WHERE id = %s"
        execute_query(query, (announcement_id,))


class Ticket:
    @staticmethod
    def get_all():
        """Obtiene todos los tickets"""
        query = """
            SELECT t.*, u1.nombre_completo as solicitante_nombre,
                   u2.nombre_completo as asignado_nombre
            FROM tickets t
            JOIN usuarios u1 ON t.solicitante_id = u1.id
            LEFT JOIN usuarios u2 ON t.asignado_a = u2.id
            ORDER BY t.fecha_creacion DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_user(user_id):
        """Obtiene tickets creados por un usuario"""
        query = """
            SELECT t.*, u.nombre_completo as asignado_nombre
            FROM tickets t
            LEFT JOIN usuarios u ON t.asignado_a = u.id
            WHERE t.solicitante_id = %s
            ORDER BY t.fecha_creacion DESC
        """
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def get_by_id(ticket_id):
        """Obtiene un ticket por su ID"""
        query = """
            SELECT t.*, u1.nombre_completo as solicitante_nombre,
                   u2.nombre_completo as asignado_nombre
            FROM tickets t
            JOIN usuarios u1 ON t.solicitante_id = u1.id
            LEFT JOIN usuarios u2 ON t.asignado_a = u2.id
            WHERE t.id = %s
        """
        result = execute_query(query, (ticket_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(titulo, descripcion, categoria, prioridad, solicitante_id):
        """Crea un nuevo ticket"""
        query = """
            INSERT INTO tickets (titulo, descripcion, categoria, prioridad, solicitante_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(query, (titulo, descripcion, categoria, prioridad, solicitante_id))

    @staticmethod
    def update_status(ticket_id, estado, asignado_a=None):
        """Actualiza el estado de un ticket"""
        query = """
            UPDATE tickets
            SET estado = %s, asignado_a = %s, fecha_actualizacion = NOW()
            WHERE id = %s
        """
        return execute_query(query, (estado, asignado_a, ticket_id))

    @staticmethod
    def add_comment(ticket_id, user_id, comentario):
        """Agrega un comentario a un ticket"""
        query = """
            INSERT INTO ticket_comentarios (ticket_id, usuario_id, comentario)
            VALUES (%s, %s, %s)
        """
        result = execute_query(query, (ticket_id, user_id, comentario))
        # Actualizar fecha de actualización del ticket
        execute_query("UPDATE tickets SET fecha_actualizacion = NOW() WHERE id = %s", (ticket_id,))
        return result

    @staticmethod
    def get_comments(ticket_id):
        """Obtiene los comentarios de un ticket"""
        query = """
            SELECT c.*, u.nombre_completo as usuario_nombre
            FROM ticket_comentarios c
            JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.ticket_id = %s
            ORDER BY c.fecha_comentario ASC
        """
        return execute_query(query, (ticket_id,), fetch=True)


class Department:
    @staticmethod
    def get_all():
        """Obtiene todos los departamentos activos"""
        query = "SELECT * FROM departamentos WHERE activo = TRUE ORDER BY nombre"
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(dept_id):
        """Obtiene un departamento por su ID"""
        query = "SELECT * FROM departamentos WHERE id = %s"
        result = execute_query(query, (dept_id,), fetch=True)
        return result[0] if result else None
