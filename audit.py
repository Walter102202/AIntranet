"""
Sistema de auditoría para registrar acciones de usuarios y del sistema.
"""
import json
import logging
from flask import request, session
from database import execute_query

logger = logging.getLogger(__name__)


def log_action(accion, recurso=None, recurso_id=None, detalles=None, resultado='exito'):
    """
    Registra una acción en la tabla de auditoría.

    Args:
        accion: Tipo de acción (login, create_user, approve_vacation, etc.)
        recurso: Tipo de recurso afectado (usuario, vacacion, ticket, etc.)
        recurso_id: ID del recurso afectado
        detalles: Dict con detalles adicionales
        resultado: 'exito', 'error', o 'denegado'
    """
    try:
        usuario_id = session.get('user_id')
        usuario_nombre = session.get('nombre_completo') or session.get('username')

        ip_address = request.remote_addr if request else None
        user_agent = str(request.user_agent)[:500] if request else None

        detalles_json = json.dumps(detalles, ensure_ascii=False) if detalles else None

        query = """
            INSERT INTO audit_log
                (usuario_id, usuario_nombre, accion, recurso, recurso_id,
                 detalles, ip_address, user_agent, resultado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (
            usuario_id, usuario_nombre, accion, recurso, recurso_id,
            detalles_json, ip_address, user_agent, resultado
        ), fetch=False)

    except Exception as e:
        # Nunca dejar que un error de auditoría rompa la operación principal
        logger.error(f"Error al registrar auditoría: {e}")
