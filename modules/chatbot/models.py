"""
Modelos para el sistema de chatbot con IA
"""
import json
from datetime import datetime, date
from database import execute_query
import uuid


def convert_datetime_to_str(obj):
    """
    Convierte recursivamente objetos datetime y date a strings en diccionarios y listas
    para que sean serializables a JSON

    Args:
        obj: Objeto a convertir (puede ser dict, list, datetime, date, u otro)

    Returns:
        Objeto convertido con datetime/date como strings
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_datetime_to_str(item) for item in obj)
    else:
        return obj


class ChatbotSession:
    """Modelo para gestionar sesiones de chatbot"""

    @staticmethod
    def create(usuario_id, metadata=None):
        """
        Crea una nueva sesión de chatbot para un usuario

        Args:
            usuario_id: ID del usuario
            metadata: Diccionario con metadata adicional

        Returns:
            dict: Datos de la sesión creada
        """
        session_key = str(uuid.uuid4())
        metadata_json = json.dumps(convert_datetime_to_str(metadata)) if metadata else None

        query = """
            INSERT INTO chatbot_sessions (usuario_id, session_key, metadata)
            VALUES (%s, %s, %s)
        """
        session_id = execute_query(query, (usuario_id, session_key, metadata_json), fetch=False)

        return {
            'id': session_id,
            'usuario_id': usuario_id,
            'session_key': session_key,
            'activa': True
        }

    @staticmethod
    def get_active_session(usuario_id):
        """
        Obtiene la sesión activa de un usuario

        Args:
            usuario_id: ID del usuario

        Returns:
            dict: Sesión activa o None si no existe
        """
        query = """
            SELECT * FROM chatbot_sessions
            WHERE usuario_id = %s AND activa = TRUE
            ORDER BY fecha_ultimo_mensaje DESC
            LIMIT 1
        """
        sessions = execute_query(query, (usuario_id,))
        # Manejar el caso donde sessions es None
        if sessions is None or len(sessions) == 0:
            return None
        return sessions[0]

    @staticmethod
    def get_or_create_session(usuario_id):
        """
        Obtiene la sesión activa o crea una nueva si no existe

        Args:
            usuario_id: ID del usuario

        Returns:
            dict: Sesión activa o creada
        """
        session = ChatbotSession.get_active_session(usuario_id)
        if not session:
            session = ChatbotSession.create(usuario_id)
        return session

    @staticmethod
    def deactivate_session(session_id):
        """
        Desactiva una sesión (finaliza la conversación)

        Args:
            session_id: ID de la sesión
        """
        query = "UPDATE chatbot_sessions SET activa = FALSE WHERE id = %s"
        execute_query(query, (session_id,), fetch=False)

    @staticmethod
    def update_metadata(session_id, metadata):
        """
        Actualiza la metadata de una sesión

        Args:
            session_id: ID de la sesión
            metadata: Diccionario con metadata
        """
        metadata_json = json.dumps(convert_datetime_to_str(metadata))
        query = "UPDATE chatbot_sessions SET metadata = %s WHERE id = %s"
        execute_query(query, (metadata_json, session_id), fetch=False)


class ChatbotMessage:
    """Modelo para gestionar mensajes del chatbot"""

    @staticmethod
    def create(session_id, role, content, tool_calls=None, metadata=None):
        """
        Crea un nuevo mensaje en la conversación

        Args:
            session_id: ID de la sesión
            role: Rol del mensaje ('user', 'assistant', 'system', 'tool')
            content: Contenido del mensaje
            tool_calls: Llamadas a herramientas ejecutadas (dict)
            metadata: Metadata adicional (dict)

        Returns:
            int: ID del mensaje creado
        """
        # ✅ Validar que role sea un valor permitido
        valid_roles = ['user', 'assistant', 'system', 'tool']
        if role not in valid_roles:
            raise ValueError(f"Role inválido: '{role}'. Debe ser uno de: {valid_roles}")

        # ✅ Asegurar que content sea string (no None, no array, no dict)
        if content is None:
            content = ''
        elif isinstance(content, (list, dict)):
            # Si content es un array o dict (ej: mensaje de visión), convertir a JSON string
            content = json.dumps(content, ensure_ascii=False)
        elif not isinstance(content, str):
            # Si es otro tipo, convertir a string
            content = str(content)

        # ✅ Truncar content si es demasiado largo (TEXT = 65,535 bytes)
        # Dejamos margen de seguridad para caracteres multibyte
        max_content_length = 60000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[... contenido truncado por longitud ...]"

        tool_calls_json = json.dumps(convert_datetime_to_str(tool_calls)) if tool_calls else None
        metadata_json = json.dumps(convert_datetime_to_str(metadata)) if metadata else None

        query = """
            INSERT INTO chatbot_messages (session_id, role, content, tool_calls, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            message_id = execute_query(
                query,
                (session_id, role, content, tool_calls_json, metadata_json),
                fetch=False
            )
            return message_id
        except Exception as e:
            # ✅ Logging detallado del error para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al guardar mensaje en BD:")
            logger.error(f"  - session_id: {session_id}")
            logger.error(f"  - role: {role}")
            logger.error(f"  - content length: {len(content)}")
            logger.error(f"  - content preview: {content[:200]}...")
            logger.error(f"  - error: {str(e)}")
            raise

    @staticmethod
    def get_conversation_history(session_id, limit=50):
        """
        Obtiene el historial de conversación de una sesión
        Retorna los ÚLTIMOS N mensajes ordenados cronológicamente

        Args:
            session_id: ID de la sesión
            limit: Número máximo de mensajes a retornar

        Returns:
            list: Lista de mensajes ordenados cronológicamente
        """
        # Subconsulta para obtener los ÚLTIMOS N mensajes y luego ordenarlos cronológicamente
        query = """
            SELECT id, role, content, tool_calls, metadata, timestamp
            FROM (
                SELECT id, role, content, tool_calls, metadata, timestamp
                FROM chatbot_messages
                WHERE session_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            ) AS recent_messages
            ORDER BY timestamp ASC
        """
        messages = execute_query(query, (session_id, limit))

        # Manejar el caso donde messages es None
        if messages is None:
            return []

        # Convertir JSON strings a objetos Python
        for msg in messages:
            if msg.get('tool_calls'):
                msg['tool_calls'] = json.loads(msg['tool_calls'])
            if msg.get('metadata'):
                msg['metadata'] = json.loads(msg['metadata'])

        return messages

    @staticmethod
    def format_for_llm(messages, include_system=False, system_message=None):
        """
        Formatea mensajes para el formato esperado por el LLM

        Args:
            messages: Lista de mensajes de la BD
            include_system: Si debe incluir mensaje del sistema al inicio
            system_message: Contenido del mensaje del sistema (dict con role y content)

        Returns:
            list: Mensajes formateados para el LLM
        """
        # Manejar el caso donde messages es None
        if messages is None:
            return []

        formatted = []

        # Agregar mensaje del sistema al inicio si se solicita
        if include_system and system_message:
            formatted.append(system_message)

        # Filtrar mensajes del sistema existentes para evitar duplicados
        for msg in messages:
            # Saltar mensajes del sistema existentes si vamos a agregar uno nuevo
            if include_system and msg['role'] == 'system':
                continue

            formatted_msg = {
                'role': msg['role'],
                'content': msg['content']
            }

            # Agregar tool_calls si existen (para mensajes de assistant)
            if msg.get('tool_calls'):
                formatted_msg['tool_calls'] = msg['tool_calls']

            # Agregar tool_call_id si es un mensaje de tipo 'tool'
            if msg['role'] == 'tool' and msg.get('metadata'):
                metadata = msg['metadata']
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                if metadata.get('tool_call_id'):
                    formatted_msg['tool_call_id'] = metadata['tool_call_id']

            formatted.append(formatted_msg)
        return formatted

    @staticmethod
    def estimate_tokens(messages):
        """
        Estima el número de tokens en una lista de mensajes

        Args:
            messages: Lista de mensajes formateados

        Returns:
            int: Estimación de tokens (4 chars ≈ 1 token)
        """
        if not messages:
            return 0

        total_chars = 0
        for msg in messages:
            content = msg.get('content', '')
            total_chars += len(str(content))

            # Agregar tool calls si existen
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    total_chars += len(tool_call.get('function', {}).get('name', ''))
                    total_chars += len(tool_call.get('function', {}).get('arguments', ''))

        # Estimación: ~4 caracteres por token
        return total_chars // 4

    @staticmethod
    def clean_incomplete_tool_calls(messages):
        """
        Limpia mensajes assistant con tool_calls que no tienen sus correspondientes
        mensajes tool. Esto previene el error de OpenAI cuando una sesión es interrumpida.

        Args:
            messages: Lista de mensajes formateados para el LLM

        Returns:
            list: Mensajes limpiados (sin tool_calls incompletos)
        """
        if not messages:
            return messages

        cleaned_messages = []
        i = 0

        while i < len(messages):
            msg = messages[i]

            # Si es un mensaje assistant con tool_calls
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                tool_calls = msg['tool_calls']
                expected_tool_call_ids = {tc['id'] for tc in tool_calls}

                # Buscar mensajes tool consecutivos que respondan a estos tool_calls
                found_tool_call_ids = set()
                j = i + 1

                while j < len(messages) and messages[j].get('role') == 'tool':
                    tool_msg = messages[j]
                    if tool_msg.get('tool_call_id') in expected_tool_call_ids:
                        found_tool_call_ids.add(tool_msg['tool_call_id'])
                    j += 1

                # Verificar si TODOS los tool_call_ids tienen respuesta
                if expected_tool_call_ids == found_tool_call_ids:
                    # ✅ Completo: agregar el mensaje assistant y sus tool messages
                    cleaned_messages.append(msg)
                    # Agregar los mensajes tool
                    for k in range(i + 1, j):
                        cleaned_messages.append(messages[k])
                    i = j  # Saltar al siguiente mensaje después de los tool messages
                else:
                    # ❌ Incompleto: omitir este mensaje assistant y sus tool messages parciales
                    missing_ids = expected_tool_call_ids - found_tool_call_ids
                    print(f"[WARNING] Mensaje assistant con tool_calls incompletos detectado.")
                    print(f"          Expected IDs: {expected_tool_call_ids}")
                    print(f"          Found IDs: {found_tool_call_ids}")
                    print(f"          Missing IDs: {missing_ids}")
                    print(f"          Este mensaje será omitido del historial enviado al LLM.")
                    i = j  # Saltar este bloque completo
            else:
                # Mensaje normal (user, system, assistant sin tool_calls)
                cleaned_messages.append(msg)
                i += 1

        return cleaned_messages

    @staticmethod
    def trim_history(messages, max_tokens=12000, keep_recent=10):
        """
        Recorta el historial de mensajes para no exceder límites de tokens

        Args:
            messages: Lista de mensajes formateados
            max_tokens: Límite máximo de tokens
            keep_recent: Número mínimo de mensajes recientes a mantener

        Returns:
            list: Mensajes recortados
        """
        if not messages:
            return messages

        # Siempre mantener el mensaje del sistema si existe
        system_msg = None
        other_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                system_msg = msg
            else:
                other_messages.append(msg)

        # Si no excede el límite, retornar todo
        estimated = ChatbotMessage.estimate_tokens(messages)
        if estimated <= max_tokens:
            return messages

        # Mantener los mensajes más recientes
        trimmed = other_messages[-keep_recent:] if len(other_messages) > keep_recent else other_messages

        # Re-agregar mensaje del sistema al inicio
        if system_msg:
            trimmed.insert(0, system_msg)

        # Verificar si aún excede el límite
        while len(trimmed) > 3 and ChatbotMessage.estimate_tokens(trimmed) > max_tokens:
            # Remover el mensaje más antiguo (después del sistema)
            if trimmed[0]['role'] == 'system':
                trimmed.pop(1)  # Remover el segundo mensaje
            else:
                trimmed.pop(0)  # Remover el primero

        return trimmed

    @staticmethod
    def cleanup_incomplete_tool_calls_from_db(session_id):
        """
        Limpia físicamente de la base de datos mensajes assistant con tool_calls
        que no tienen sus correspondientes mensajes tool.

        Esta función se llama para mantener la base de datos limpia cuando se detectan
        mensajes incompletos (por ejemplo, después de que el usuario cambia de página).

        Args:
            session_id: ID de la sesión a limpiar

        Returns:
            int: Número de mensajes eliminados
        """
        # Obtener todos los mensajes de la sesión
        query = """
            SELECT id, role, content, tool_calls, metadata, timestamp
            FROM chatbot_messages
            WHERE session_id = %s
            ORDER BY timestamp ASC
        """
        messages = execute_query(query, (session_id,))

        if not messages:
            return 0

        # Convertir JSON strings a objetos Python
        for msg in messages:
            if msg.get('tool_calls'):
                msg['tool_calls'] = json.loads(msg['tool_calls'])
            if msg.get('metadata'):
                msg['metadata'] = json.loads(msg['metadata'])

        # Encontrar mensajes incompletos
        messages_to_delete = []
        i = 0

        while i < len(messages):
            msg = messages[i]

            # Si es un mensaje assistant con tool_calls
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                tool_calls = msg['tool_calls']
                expected_tool_call_ids = {tc['id'] for tc in tool_calls}

                # Buscar mensajes tool consecutivos
                found_tool_call_ids = set()
                j = i + 1

                while j < len(messages) and messages[j].get('role') == 'tool':
                    tool_msg = messages[j]
                    metadata = tool_msg.get('metadata', {})
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)

                    if metadata.get('tool_call_id') in expected_tool_call_ids:
                        found_tool_call_ids.add(metadata['tool_call_id'])
                    j += 1

                # Si están incompletos, marcar para eliminar
                if expected_tool_call_ids != found_tool_call_ids:
                    messages_to_delete.append(msg['id'])
                    # También eliminar los mensajes tool parciales
                    for k in range(i + 1, j):
                        messages_to_delete.append(messages[k]['id'])

                i = j
            else:
                i += 1

        # Eliminar mensajes identificados
        if messages_to_delete:
            placeholders = ', '.join(['%s'] * len(messages_to_delete))
            delete_query = f"""
                DELETE FROM chatbot_messages
                WHERE id IN ({placeholders})
            """
            execute_query(delete_query, tuple(messages_to_delete), fetch=False)

            print(f"[INFO] Limpiados {len(messages_to_delete)} mensajes incompletos de la sesión {session_id}")

        return len(messages_to_delete)


class ChatbotAction:
    """Modelo para gestionar acciones ejecutadas por el chatbot"""

    @staticmethod
    def create(session_id, message_id, action_type, action_params, action_result=None,
               success=False, error_message=None):
        """
        Registra una acción ejecutada por el chatbot

        Args:
            session_id: ID de la sesión
            message_id: ID del mensaje que generó la acción
            action_type: Tipo de acción ejecutada
            action_params: Parámetros de la acción (dict)
            action_result: Resultado de la acción (dict)
            success: Si la acción fue exitosa
            error_message: Mensaje de error si la acción falló

        Returns:
            int: ID de la acción registrada
        """
        params_json = json.dumps(convert_datetime_to_str(action_params)) if action_params else None
        result_json = json.dumps(convert_datetime_to_str(action_result)) if action_result else None

        query = """
            INSERT INTO chatbot_actions
            (session_id, message_id, action_type, action_params, action_result, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        action_id = execute_query(
            query,
            (session_id, message_id, action_type, params_json, result_json, success, error_message),
            fetch=False
        )
        return action_id

    @staticmethod
    def get_by_session(session_id):
        """
        Obtiene todas las acciones de una sesión

        Args:
            session_id: ID de la sesión

        Returns:
            list: Lista de acciones ejecutadas
        """
        query = """
            SELECT * FROM chatbot_actions
            WHERE session_id = %s
            ORDER BY timestamp ASC
        """
        actions = execute_query(query, (session_id,))

        # Manejar el caso donde actions es None
        if actions is None:
            return []

        # Convertir JSON strings a objetos Python
        for action in actions:
            if action.get('action_params'):
                action['action_params'] = json.loads(action['action_params'])
            if action.get('action_result'):
                action['action_result'] = json.loads(action['action_result'])

        return actions
