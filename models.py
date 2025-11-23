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
    def get_by_email(email):
        """Obtiene un usuario por su email"""
        query = "SELECT * FROM usuarios WHERE email = %s AND activo = TRUE"
        result = execute_query(query, (email,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_oauth(oauth_provider, oauth_id):
        """Obtiene un usuario por su proveedor OAuth e ID"""
        query = "SELECT * FROM usuarios WHERE oauth_provider = %s AND oauth_id = %s AND activo = TRUE"
        result = execute_query(query, (oauth_provider, oauth_id), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create_oauth_user(email, nombre_completo, oauth_provider, oauth_id, username=None, rol='empleado'):
        """Crea un nuevo usuario OAuth"""
        # Si no se proporciona username, usar el email como base
        if not username:
            username = email.split('@')[0]

        # Verificar si el username ya existe, si es así, añadir sufijo
        existing = User.get_by_username(username)
        if existing:
            import random
            username = f"{username}_{random.randint(1000, 9999)}"

        query = """
            INSERT INTO usuarios (username, email, nombre_completo, oauth_provider, oauth_id, rol, activo)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """
        result = execute_query(query, (username, email, nombre_completo, oauth_provider, oauth_id, rol))

        # Obtener el usuario recién creado
        if result:
            return User.get_by_oauth(oauth_provider, oauth_id)
        return None

    @staticmethod
    def verify_password(user, password):
        """Verifica la contraseña del usuario"""
        # Si el usuario es OAuth, no tiene contraseña
        if user.get('oauth_provider'):
            return False
        # Si no hay password_hash, el usuario no puede usar login tradicional
        if not user.get('password_hash'):
            return False
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


# ==================== MÓDULO DE COBRANZAS ====================

class Cliente:
    @staticmethod
    def get_all():
        """Obtiene todos los clientes activos"""
        query = "SELECT * FROM clientes WHERE activo = TRUE ORDER BY razon_social"
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(cliente_id):
        """Obtiene un cliente por su ID"""
        query = "SELECT * FROM clientes WHERE id = %s"
        result = execute_query(query, (cliente_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_codigo(codigo):
        """Obtiene un cliente por su código"""
        query = "SELECT * FROM clientes WHERE codigo = %s"
        result = execute_query(query, (codigo,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def search(search_term):
        """Busca clientes por código, razón social o RFC"""
        query = """
            SELECT * FROM clientes
            WHERE activo = TRUE
            AND (codigo LIKE %s OR razon_social LIKE %s OR rfc LIKE %s)
            ORDER BY razon_social
        """
        pattern = f"%{search_term}%"
        return execute_query(query, (pattern, pattern, pattern), fetch=True)

    @staticmethod
    def get_resumen_cartera(cliente_id):
        """Obtiene resumen completo de cartera de un cliente"""
        query = """
            SELECT
                c.id, c.codigo, c.razon_social, c.rfc, c.email, c.telefono,
                c.limite_credito, c.dias_credito,
                COUNT(f.id) as total_facturas,
                SUM(CASE WHEN f.estado IN ('pendiente', 'parcial') THEN 1 ELSE 0 END) as facturas_pendientes,
                SUM(CASE WHEN f.estado = 'vencida' THEN 1 ELSE 0 END) as facturas_vencidas,
                SUM(CASE WHEN f.estado = 'pagada' THEN 1 ELSE 0 END) as facturas_pagadas,
                COALESCE(SUM(f.total), 0) as total_facturado,
                COALESCE(SUM(f.saldo_pendiente), 0) as saldo_total_pendiente,
                COALESCE(SUM(CASE WHEN f.estado = 'vencida' THEN f.saldo_pendiente ELSE 0 END), 0) as saldo_vencido
            FROM clientes c
            LEFT JOIN facturas f ON c.id = f.cliente_id AND f.estado != 'cancelada'
            WHERE c.id = %s
            GROUP BY c.id
        """
        result = execute_query(query, (cliente_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_atraso_promedio_ponderado(cliente_id):
        """Calcula el atraso promedio ponderado por monto de factura"""
        query = """
            SELECT
                COALESCE(
                    SUM(GREATEST(DATEDIFF(CURDATE(), f.fecha_vencimiento), 0) * f.saldo_pendiente) /
                    NULLIF(SUM(f.saldo_pendiente), 0),
                    0
                ) as atraso_promedio_ponderado,
                SUM(f.saldo_pendiente) as saldo_total,
                COUNT(*) as num_facturas
            FROM facturas f
            WHERE f.cliente_id = %s
            AND f.estado IN ('pendiente', 'parcial', 'vencida')
            AND f.saldo_pendiente > 0
        """
        result = execute_query(query, (cliente_id,), fetch=True)
        return result[0] if result else None


class Factura:
    @staticmethod
    def get_all():
        """Obtiene todas las facturas"""
        query = """
            SELECT f.*, c.razon_social as cliente_nombre, c.codigo as cliente_codigo
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            ORDER BY f.fecha_emision DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_cliente(cliente_id):
        """Obtiene facturas de un cliente"""
        query = """
            SELECT f.*,
                DATEDIFF(CURDATE(), f.fecha_vencimiento) as dias_vencido
            FROM facturas f
            WHERE f.cliente_id = %s AND f.estado != 'cancelada'
            ORDER BY f.fecha_vencimiento ASC
        """
        return execute_query(query, (cliente_id,), fetch=True)

    @staticmethod
    def get_pendientes_by_cliente(cliente_id):
        """Obtiene facturas pendientes de un cliente"""
        query = """
            SELECT f.*,
                DATEDIFF(CURDATE(), f.fecha_vencimiento) as dias_vencido
            FROM facturas f
            WHERE f.cliente_id = %s
            AND f.estado IN ('pendiente', 'parcial', 'vencida')
            ORDER BY f.fecha_vencimiento ASC
        """
        return execute_query(query, (cliente_id,), fetch=True)

    @staticmethod
    def get_vencidas():
        """Obtiene todas las facturas vencidas"""
        query = """
            SELECT f.*, c.razon_social as cliente_nombre, c.codigo as cliente_codigo,
                DATEDIFF(CURDATE(), f.fecha_vencimiento) as dias_vencido
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.estado = 'vencida' OR (f.estado IN ('pendiente', 'parcial') AND f.fecha_vencimiento < CURDATE())
            ORDER BY dias_vencido DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_antiguedad_saldos(cliente_id=None):
        """Obtiene reporte de antigüedad de saldos"""
        base_query = """
            SELECT
                c.id as cliente_id, c.codigo, c.razon_social,
                SUM(CASE WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) <= 0 THEN f.saldo_pendiente ELSE 0 END) as vigente,
                SUM(CASE WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 1 AND 30 THEN f.saldo_pendiente ELSE 0 END) as dias_1_30,
                SUM(CASE WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 31 AND 60 THEN f.saldo_pendiente ELSE 0 END) as dias_31_60,
                SUM(CASE WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 61 AND 90 THEN f.saldo_pendiente ELSE 0 END) as dias_61_90,
                SUM(CASE WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) > 90 THEN f.saldo_pendiente ELSE 0 END) as dias_mas_90,
                SUM(f.saldo_pendiente) as total_pendiente
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.estado IN ('pendiente', 'parcial', 'vencida')
        """
        if cliente_id:
            query = base_query + " AND c.id = %s GROUP BY c.id, c.codigo, c.razon_social"
            return execute_query(query, (cliente_id,), fetch=True)
        else:
            query = base_query + " GROUP BY c.id, c.codigo, c.razon_social ORDER BY total_pendiente DESC"
            return execute_query(query, fetch=True)


class Pago:
    @staticmethod
    def get_by_cliente(cliente_id):
        """Obtiene pagos de un cliente"""
        query = """
            SELECT p.*, u.nombre_completo as registrado_por_nombre
            FROM pagos p
            LEFT JOIN usuarios u ON p.registrado_por = u.id
            WHERE p.cliente_id = %s
            ORDER BY p.fecha_pago DESC
        """
        return execute_query(query, (cliente_id,), fetch=True)

    @staticmethod
    def get_historial_pagos(cliente_id, limit=10):
        """Obtiene historial de pagos recientes de un cliente"""
        query = """
            SELECT p.*, u.nombre_completo as registrado_por_nombre
            FROM pagos p
            LEFT JOIN usuarios u ON p.registrado_por = u.id
            WHERE p.cliente_id = %s
            ORDER BY p.fecha_pago DESC
            LIMIT %s
        """
        return execute_query(query, (cliente_id, limit), fetch=True)


class CobranzaSeguimiento:
    @staticmethod
    def get_by_cliente(cliente_id, limit=20):
        """Obtiene seguimientos de cobranza de un cliente"""
        query = """
            SELECT s.*, u.nombre_completo as realizado_por_nombre,
                f.numero_factura
            FROM cobranza_seguimientos s
            LEFT JOIN usuarios u ON s.realizado_por = u.id
            LEFT JOIN facturas f ON s.factura_id = f.id
            WHERE s.cliente_id = %s
            ORDER BY s.fecha_contacto DESC
            LIMIT %s
        """
        return execute_query(query, (cliente_id, limit), fetch=True)

    @staticmethod
    def get_promesas_pendientes(cliente_id=None):
        """Obtiene promesas de pago pendientes"""
        base_query = """
            SELECT s.*, c.razon_social as cliente_nombre, c.codigo as cliente_codigo,
                u.nombre_completo as realizado_por_nombre
            FROM cobranza_seguimientos s
            JOIN clientes c ON s.cliente_id = c.id
            LEFT JOIN usuarios u ON s.realizado_por = u.id
            WHERE s.resultado = 'promesa_pago'
            AND s.fecha_promesa_pago IS NOT NULL
            AND s.fecha_promesa_pago <= CURDATE()
        """
        if cliente_id:
            query = base_query + " AND s.cliente_id = %s ORDER BY s.fecha_promesa_pago"
            return execute_query(query, (cliente_id,), fetch=True)
        else:
            query = base_query + " ORDER BY s.fecha_promesa_pago"
            return execute_query(query, fetch=True)


class Cobranza:
    """Clase con métodos de análisis avanzado para cobranzas"""

    @staticmethod
    def get_resumen_cliente_completo(cliente_id):
        """Genera un resumen completo de la situación de un cliente"""
        cliente = Cliente.get_by_id(cliente_id)
        if not cliente:
            return None

        resumen_cartera = Cliente.get_resumen_cartera(cliente_id)
        atraso_ponderado = Cliente.get_atraso_promedio_ponderado(cliente_id)
        antiguedad = Factura.get_antiguedad_saldos(cliente_id)
        facturas_pendientes = Factura.get_pendientes_by_cliente(cliente_id)
        ultimos_pagos = Pago.get_historial_pagos(cliente_id, 5)
        ultimos_seguimientos = CobranzaSeguimiento.get_by_cliente(cliente_id, 5)
        promesas_pendientes = CobranzaSeguimiento.get_promesas_pendientes(cliente_id)

        return {
            'cliente': cliente,
            'cartera': resumen_cartera,
            'atraso_promedio_ponderado': atraso_ponderado,
            'antiguedad_saldos': antiguedad[0] if antiguedad else None,
            'facturas_pendientes': facturas_pendientes or [],
            'ultimos_pagos': ultimos_pagos or [],
            'ultimos_seguimientos': ultimos_seguimientos or [],
            'promesas_incumplidas': promesas_pendientes or []
        }

    @staticmethod
    def get_dashboard_cobranzas():
        """Obtiene métricas generales del dashboard de cobranzas"""
        query = """
            SELECT
                COALESCE(COUNT(DISTINCT c.id), 0) as total_clientes_con_saldo,
                COALESCE(COUNT(f.id), 0) as total_facturas_pendientes,
                COALESCE(SUM(CASE WHEN f.estado = 'vencida' OR (f.estado IN ('pendiente', 'parcial') AND f.fecha_vencimiento < CURDATE()) THEN 1 ELSE 0 END), 0) as facturas_vencidas,
                COALESCE(SUM(f.saldo_pendiente), 0) as cartera_total,
                COALESCE(SUM(CASE WHEN f.fecha_vencimiento < CURDATE() THEN f.saldo_pendiente ELSE 0 END), 0) as cartera_vencida
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.estado IN ('pendiente', 'parcial', 'vencida')
        """
        result = execute_query(query, fetch=True)

        # Si no hay datos, retornar valores por defecto en 0
        if not result or not result[0]:
            return {
                'total_clientes_con_saldo': 0,
                'total_facturas_pendientes': 0,
                'facturas_vencidas': 0,
                'cartera_total': 0,
                'cartera_vencida': 0
            }

        return result[0]


# ==================== MÓDULO DE KPIs (POWER BI) ====================

class PowerBIReport:
    @staticmethod
    def get_all():
        """Obtiene todos los reportes activos"""
        query = """
            SELECT r.*, u.nombre_completo as creador_nombre
            FROM powerbi_reports r
            LEFT JOIN usuarios u ON r.creado_por = u.id
            WHERE r.activo = TRUE
            ORDER BY r.fecha_creacion DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(report_id):
        """Obtiene un reporte por ID con todos sus datos incluyendo filtros"""
        query = """
            SELECT r.*, u.nombre_completo as creador_nombre
            FROM powerbi_reports r
            LEFT JOIN usuarios u ON r.creado_por = u.id
            WHERE r.id = %s
        """
        result = execute_query(query, (report_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(titulo, descripcion, embed_url, categoria, creado_por, available_filters=None, embed_type='public'):
        """Crea un nuevo reporte con soporte para filtros"""
        import json

        # Convertir filtros a JSON si es dict
        filters_json = json.dumps(available_filters) if available_filters else None

        query = """
            INSERT INTO powerbi_reports (titulo, descripcion, embed_url, categoria, creado_por, available_filters, embed_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (titulo, descripcion, embed_url, categoria, creado_por, filters_json, embed_type))

    @staticmethod
    def update(report_id, titulo, descripcion, embed_url, categoria, activo, available_filters=None, embed_type='public'):
        """Actualiza un reporte incluyendo filtros y tipo de embedding"""
        import json

        # Convertir filtros a JSON si es dict
        filters_json = json.dumps(available_filters) if available_filters else None

        query = """
            UPDATE powerbi_reports
            SET titulo = %s, descripcion = %s, embed_url = %s, categoria = %s, activo = %s,
                available_filters = %s, embed_type = %s
            WHERE id = %s
        """
        return execute_query(query, (titulo, descripcion, embed_url, categoria, activo, filters_json, embed_type, report_id))

    @staticmethod
    def update_filters(report_id, available_filters):
        """Actualiza solo los filtros disponibles de un reporte"""
        import json

        filters_json = json.dumps(available_filters) if available_filters else None

        query = """
            UPDATE powerbi_reports
            SET available_filters = %s
            WHERE id = %s
        """
        return execute_query(query, (filters_json, report_id))

    @staticmethod
    def get_filters(report_id):
        """Obtiene solo los filtros disponibles de un reporte"""
        import json

        query = """
            SELECT available_filters
            FROM powerbi_reports
            WHERE id = %s
        """
        result = execute_query(query, (report_id,), fetch=True)

        if not result or not result[0]:
            return None

        filters = result[0].get('available_filters')

        # Si es string JSON, parsearlo
        if isinstance(filters, str):
            try:
                return json.loads(filters)
            except:
                return None

        return filters

    @staticmethod
    def delete(report_id):
        """Elimina un reporte (soft delete)"""
        query = "UPDATE powerbi_reports SET activo = FALSE WHERE id = %s"
        return execute_query(query, (report_id,))

# ============================================
# Modelos para Machine Learning - Metodología KDD
# ============================================

class MLModelo:
    """Gestión de modelos de Machine Learning"""

    @staticmethod
    def get_all_activos():
        """Obtiene todos los modelos activos"""
        query = """
            SELECT id, nombre, descripcion, tipo_modelo, algoritmo, version,
                   objetivo, activo, fecha_creacion
            FROM ml_modelos
            WHERE activo = 1
            ORDER BY fecha_creacion DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(modelo_id):
        """Obtiene un modelo por ID"""
        query = "SELECT * FROM ml_modelos WHERE id = %s"
        result = execute_query(query, (modelo_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_nombre(nombre):
        """Obtiene un modelo por nombre"""
        query = "SELECT * FROM ml_modelos WHERE nombre = %s"
        result = execute_query(query, (nombre,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(nombre, descripcion, tipo_modelo, algoritmo, version, objetivo,
               variables_entrada=None):
        """Crea un nuevo modelo ML"""
        query = """
            INSERT INTO ml_modelos
            (nombre, descripcion, tipo_modelo, algoritmo, version, objetivo, variables_entrada)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (nombre, descripcion, tipo_modelo, algoritmo,
                                    version, objetivo, variables_entrada))

    @staticmethod
    def update_estado(modelo_id, activo):
        """Actualiza el estado activo/inactivo de un modelo"""
        query = """
            UPDATE ml_modelos
            SET activo = %s, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return execute_query(query, (activo, modelo_id))


class MLEjecucion:
    """Gestión de ejecuciones de modelos ML"""

    @staticmethod
    def get_by_modelo(modelo_id, limit=10):
        """Obtiene las últimas ejecuciones de un modelo"""
        query = """
            SELECT e.*, m.nombre as modelo_nombre, m.tipo_modelo
            FROM ml_ejecuciones e
            JOIN ml_modelos m ON e.modelo_id = m.id
            WHERE e.modelo_id = %s
            ORDER BY e.fecha_ejecucion DESC
            LIMIT %s
        """
        return execute_query(query, (modelo_id, limit), fetch=True)

    @staticmethod
    def get_ultima_por_modelo(modelo_id):
        """Obtiene la última ejecución completada de un modelo"""
        query = """
            SELECT * FROM ml_ejecuciones
            WHERE modelo_id = %s AND estado = 'completado'
            ORDER BY fecha_ejecucion DESC
            LIMIT 1
        """
        result = execute_query(query, (modelo_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def get_by_id(ejecucion_id):
        """Obtiene una ejecución por ID"""
        query = """
            SELECT e.*, m.nombre as modelo_nombre, m.tipo_modelo, m.algoritmo
            FROM ml_ejecuciones e
            JOIN ml_modelos m ON e.modelo_id = m.id
            WHERE e.id = %s
        """
        result = execute_query(query, (ejecucion_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(modelo_id, fecha_datos_desde=None, fecha_datos_hasta=None,
               num_registros=None, duracion=None, parametros=None,
               usuario_ejecutor=None, estado='completado'):
        """Crea un registro de ejecución"""
        query = """
            INSERT INTO ml_ejecuciones
            (modelo_id, fecha_datos_desde, fecha_datos_hasta, num_registros_procesados,
             duracion_segundos, estado, parametros, usuario_ejecutor)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (modelo_id, fecha_datos_desde, fecha_datos_hasta,
                                    num_registros, duracion, parametros,
                                    usuario_ejecutor, estado))

    @staticmethod
    def get_ultimas_ejecuciones(limit=20):
        """Obtiene las últimas ejecuciones de todos los modelos"""
        query = """
            SELECT e.id, e.fecha_ejecucion, e.num_registros_procesados,
                   e.duracion_segundos, e.estado,
                   m.nombre as modelo_nombre, m.tipo_modelo, m.algoritmo
            FROM ml_ejecuciones e
            JOIN ml_modelos m ON e.modelo_id = m.id
            WHERE e.estado = 'completado'
            ORDER BY e.fecha_ejecucion DESC
            LIMIT %s
        """
        return execute_query(query, (limit,), fetch=True)


class MLKDDProceso:
    """Gestión del proceso KDD por ejecución"""

    @staticmethod
    def get_by_ejecucion(ejecucion_id):
        """Obtiene todas las etapas KDD de una ejecución"""
        query = """
            SELECT * FROM ml_kdd_proceso
            WHERE ejecucion_id = %s
            ORDER BY
                CASE etapa
                    WHEN 'selection' THEN 1
                    WHEN 'preprocessing' THEN 2
                    WHEN 'transformation' THEN 3
                    WHEN 'data_mining' THEN 4
                    WHEN 'interpretation' THEN 5
                END
        """
        return execute_query(query, (ejecucion_id,), fetch=True)

    @staticmethod
    def create(ejecucion_id, etapa, fecha_inicio=None, fecha_fin=None,
               duracion=None, descripcion=None, metricas_etapa=None,
               estado='completado', detalles=None):
        """Registra una etapa del proceso KDD"""
        query = """
            INSERT INTO ml_kdd_proceso
            (ejecucion_id, etapa, fecha_inicio, fecha_fin, duracion_segundos,
             descripcion, metricas_etapa, estado, detalles)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (ejecucion_id, etapa, fecha_inicio, fecha_fin,
                                    duracion, descripcion, metricas_etapa,
                                    estado, detalles))

    @staticmethod
    def get_resumen_por_ejecucion(ejecucion_id):
        """Obtiene resumen del proceso KDD de una ejecución"""
        query = """
            SELECT
                etapa,
                estado,
                duracion_segundos,
                descripcion,
                fecha_inicio,
                fecha_fin
            FROM ml_kdd_proceso
            WHERE ejecucion_id = %s
            ORDER BY
                CASE etapa
                    WHEN 'selection' THEN 1
                    WHEN 'preprocessing' THEN 2
                    WHEN 'transformation' THEN 3
                    WHEN 'data_mining' THEN 4
                    WHEN 'interpretation' THEN 5
                END
        """
        return execute_query(query, (ejecucion_id,), fetch=True)


class MLResultadoCliente:
    """Gestión de resultados ML por cliente"""

    @staticmethod
    def get_by_cliente(cliente_codigo):
        """Obtiene todos los resultados ML de un cliente"""
        query = """
            SELECT
                rc.*,
                m.nombre as modelo_nombre,
                m.tipo_modelo,
                m.algoritmo,
                m.descripcion as modelo_descripcion,
                e.fecha_ejecucion,
                e.fecha_datos_desde,
                e.fecha_datos_hasta
            FROM ml_resultados_cliente rc
            JOIN ml_ejecuciones e ON rc.ejecucion_id = e.id
            JOIN ml_modelos m ON e.modelo_id = m.id
            WHERE rc.cliente_codigo = %s
            AND e.estado = 'completado'
            AND m.activo = 1
            ORDER BY e.fecha_ejecucion DESC
        """
        return execute_query(query, (cliente_codigo,), fetch=True)

    @staticmethod
    def get_ultimos_por_cliente(cliente_codigo, limit=5):
        """Obtiene los últimos N resultados de un cliente"""
        query = """
            SELECT * FROM v_ml_ultimos_resultados_cliente
            WHERE cliente_codigo = %s
            ORDER BY fecha_ejecucion DESC
            LIMIT %s
        """
        return execute_query(query, (cliente_codigo, limit), fetch=True)

    @staticmethod
    def get_by_ejecucion(ejecucion_id):
        """Obtiene todos los resultados de una ejecución"""
        query = """
            SELECT rc.*, c.razon_social
            FROM ml_resultados_cliente rc
            JOIN clientes c ON rc.cliente_codigo = c.codigo
            WHERE rc.ejecucion_id = %s
            ORDER BY rc.score_prediccion DESC
        """
        return execute_query(query, (ejecucion_id,), fetch=True)

    @staticmethod
    def create(ejecucion_id, cliente_codigo, score_prediccion=None,
               clasificacion=None, probabilidad_pago=None, dias_pago_predicho=None,
               monto_recuperable_predicho=None, factores_principales=None,
               confianza_prediccion=None, segmento_cliente=None, cluster_id=None,
               accion_recomendada=None, prioridad_cobranza=None,
               datos_entrada=None, explicacion=None):
        """Crea un resultado ML para un cliente"""
        query = """
            INSERT INTO ml_resultados_cliente
            (ejecucion_id, cliente_codigo, score_prediccion, clasificacion,
             probabilidad_pago, dias_pago_predicho, monto_recuperable_predicho,
             factores_principales, confianza_prediccion, segmento_cliente,
             cluster_id, accion_recomendada, prioridad_cobranza,
             datos_entrada, explicacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (ejecucion_id, cliente_codigo, score_prediccion,
                                    clasificacion, probabilidad_pago, dias_pago_predicho,
                                    monto_recuperable_predicho, factores_principales,
                                    confianza_prediccion, segmento_cliente, cluster_id,
                                    accion_recomendada, prioridad_cobranza,
                                    datos_entrada, explicacion))

    @staticmethod
    def get_clientes_con_resultados():
        """Obtiene lista de clientes que tienen resultados ML"""
        query = """
            SELECT DISTINCT c.codigo, c.razon_social
            FROM clientes c
            JOIN ml_resultados_cliente rc ON c.codigo = rc.cliente_codigo
            JOIN ml_ejecuciones e ON rc.ejecucion_id = e.id
            WHERE e.estado = 'completado'
            ORDER BY c.razon_social
        """
        return execute_query(query, fetch=True)


class MLMetricasModelo:
    """Gestión de métricas de rendimiento de modelos"""

    @staticmethod
    def get_by_ejecucion(ejecucion_id):
        """Obtiene las métricas de una ejecución"""
        query = "SELECT * FROM ml_metricas_modelo WHERE ejecucion_id = %s"
        result = execute_query(query, (ejecucion_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(ejecucion_id, accuracy=None, precision_score=None, recall=None,
               f1_score=None, auc_roc=None, mae=None, mse=None, rmse=None,
               r2_score=None, silhouette_score=None, davies_bouldin_score=None,
               calinski_harabasz_score=None, tasa_recuperacion_predicha=None,
               matriz_confusion=None, metricas_custom=None):
        """Crea registro de métricas para una ejecución"""
        query = """
            INSERT INTO ml_metricas_modelo
            (ejecucion_id, accuracy, precision_score, recall, f1_score, auc_roc,
             mae, mse, rmse, r2_score, silhouette_score, davies_bouldin_score,
             calinski_harabasz_score, tasa_recuperacion_predicha,
             matriz_confusion, metricas_custom)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (ejecucion_id, accuracy, precision_score, recall,
                                    f1_score, auc_roc, mae, mse, rmse, r2_score,
                                    silhouette_score, davies_bouldin_score,
                                    calinski_harabasz_score, tasa_recuperacion_predicha,
                                    matriz_confusion, metricas_custom))

    @staticmethod
    def comparar_modelos(modelo_ids):
        """Compara métricas de múltiples modelos"""
        placeholders = ','.join(['%s'] * len(modelo_ids))
        query = f"""
            SELECT * FROM v_ml_comparacion_modelos
            WHERE modelo_id IN ({placeholders})
            ORDER BY fecha_ejecucion DESC
        """
        return execute_query(query, tuple(modelo_ids), fetch=True)


class MLComparacion:
    """Gestión de comparaciones entre modelos"""

    @staticmethod
    def get_all(limit=20):
        """Obtiene todas las comparaciones"""
        query = """
            SELECT c.*, m.nombre as modelo_ganador_nombre
            FROM ml_comparaciones c
            LEFT JOIN ml_modelos m ON c.modelo_ganador_id = m.id
            ORDER BY c.fecha_comparacion DESC
            LIMIT %s
        """
        return execute_query(query, (limit,), fetch=True)

    @staticmethod
    def get_by_id(comparacion_id):
        """Obtiene una comparación por ID"""
        query = """
            SELECT c.*, m.nombre as modelo_ganador_nombre
            FROM ml_comparaciones c
            LEFT JOIN ml_modelos m ON c.modelo_ganador_id = m.id
            WHERE c.id = %s
        """
        result = execute_query(query, (comparacion_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(nombre_comparacion, descripcion, ejecuciones_comparadas,
               criterio_comparacion, modelo_ganador_id=None,
               resultados_comparacion=None, conclusiones=None, usuario=None):
        """Crea una nueva comparación"""
        query = """
            INSERT INTO ml_comparaciones
            (nombre_comparacion, descripcion, ejecuciones_comparadas,
             criterio_comparacion, modelo_ganador_id, resultados_comparacion,
             conclusiones, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (nombre_comparacion, descripcion,
                                    ejecuciones_comparadas, criterio_comparacion,
                                    modelo_ganador_id, resultados_comparacion,
                                    conclusiones, usuario))


class MLFeature:
    """Gestión de features/variables de modelos"""

    @staticmethod
    def get_by_modelo(modelo_id):
        """Obtiene todas las features de un modelo"""
        query = """
            SELECT * FROM ml_features
            WHERE modelo_id = %s
            ORDER BY importancia DESC NULLS LAST, nombre_feature
        """
        return execute_query(query, (modelo_id,), fetch=True)

    @staticmethod
    def create(modelo_id, nombre_feature, descripcion=None, tipo_dato=None,
               fuente_dato=None, transformacion=None, importancia=None,
               estadisticas=None):
        """Crea una nueva feature"""
        query = """
            INSERT INTO ml_features
            (modelo_id, nombre_feature, descripcion, tipo_dato, fuente_dato,
             transformacion, importancia, estadisticas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(query, (modelo_id, nombre_feature, descripcion,
                                    tipo_dato, fuente_dato, transformacion,
                                    importancia, estadisticas))
