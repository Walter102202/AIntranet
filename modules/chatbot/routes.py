"""
Rutas y controladores del chatbot
"""
import os
import json
from datetime import datetime, date
from flask import Blueprint, request, jsonify, session
from functools import wraps
from modules.chatbot.models import ChatbotSession, ChatbotMessage, ChatbotAction
from modules.chatbot.llm_client import LLMClient, MockLLMClient
from modules.chatbot.tools import ChatbotTools
from models import User


class DateTimeEncoder(json.JSONEncoder):
    """Encoder personalizado para serializar datetime y date a JSON"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function


@chatbot_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Endpoint principal del chatbot
    Recibe un mensaje del usuario y retorna la respuesta del asistente
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400

        # Obtener información del usuario actual
        user_id = session['user_id']
        user_info = User.get_by_id(user_id)

        if not user_info:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Obtener o crear sesión de chatbot
        chat_session = ChatbotSession.get_or_create_session(user_id)

        # Guardar mensaje del usuario
        ChatbotMessage.create(
            session_id=chat_session['id'],
            role='user',
            content=user_message
        )

        # Obtener historial de conversación (últimos 100 mensajes)
        history = ChatbotMessage.get_conversation_history(chat_session['id'], limit=100)

        # 🧹 Limpiar mensajes incompletos de la base de datos (si existen)
        # Esto mantiene la BD limpia automáticamente
        deleted_count = ChatbotMessage.cleanup_incomplete_tool_calls_from_db(chat_session['id'])
        if deleted_count > 0:
            # Recargar historial después de la limpieza
            history = ChatbotMessage.get_conversation_history(chat_session['id'], limit=100)

        # Inicializar cliente LLM
        try:
            llm_client = LLMClient()
        except ValueError:
            # Si no hay API key, usar cliente mock para desarrollo
            llm_client = MockLLMClient()

        # Inicializar herramientas del chatbot
        tools_manager = ChatbotTools(user_info)
        available_tools = tools_manager.get_available_tools()

        # Validar que available_tools no sea None
        if available_tools is None:
            available_tools = []

        # Construir mensaje del sistema (SIEMPRE incluirlo para mantener contexto)
        tool_names = [tool['function']['name'] for tool in available_tools]
        system_message_content = llm_client.build_system_message(user_info, tool_names)
        system_message = {
            'role': 'system',
            'content': system_message_content
        }

        # Formatear historial con el mensaje del sistema
        formatted_history = ChatbotMessage.format_for_llm(
            history,
            include_system=True,
            system_message=system_message
        )

        # 🔧 LIMPIAR mensajes assistant con tool_calls incompletos
        # Esto previene errores cuando el usuario cambia de página durante una ejecución de herramientas
        cleaned_history = ChatbotMessage.clean_incomplete_tool_calls(formatted_history)

        # Aplicar trimming si el historial es muy largo (límite de ~12K tokens)
        messages = ChatbotMessage.trim_history(
            cleaned_history,
            max_tokens=12000,  # Límite conservador para gpt-4o-mini
            keep_recent=20     # Mantener al menos 20 mensajes recientes
        )

        # Validación final: asegurar que messages no esté vacío
        if not messages:
            messages = [
                system_message,
                {
                    'role': 'user',
                    'content': user_message
                }
            ]

        # Debug: verificar el contenido de messages
        estimated_tokens = ChatbotMessage.estimate_tokens(messages)
        print(f"[DEBUG] Mensajes a enviar al LLM: {len(messages)} mensajes (~{estimated_tokens} tokens)")
        for i, msg in enumerate(messages):
            role = msg.get('role')
            content_length = len(msg.get('content', ''))
            has_tools = 'tool_calls' in msg
            print(f"[DEBUG] Mensaje {i+1}: role={role}, content_length={content_length}, has_tool_calls={has_tools}")

        # Llamar al LLM
        max_iterations = 5  # Límite de iteraciones para evitar loops infinitos
        iteration = 0
        assistant_response = None

        while iteration < max_iterations:
            iteration += 1

            print(f"[DEBUG] Iteración {iteration}: Llamando al LLM...")

            llm_response = llm_client.chat_completion(
                messages=messages,
                tools=available_tools,
                tool_choice="auto"
            )

            content, tool_calls = llm_client.extract_response(llm_response)

            # Si no hay llamadas a herramientas, terminamos
            if not tool_calls:
                assistant_response = content
                break

            # Agregar respuesta del asistente a los mensajes EN MEMORIA
            messages.append({
                'role': 'assistant',
                'content': content or '',
                'tool_calls': tool_calls
            })

            # Guardar mensaje del asistente EN BASE DE DATOS (UNA SOLA VEZ)
            assistant_message_id = ChatbotMessage.create(
                session_id=chat_session['id'],
                role='assistant',
                content=content or '',
                tool_calls=tool_calls
            )

            # Ejecutar herramientas llamadas
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])

                # Ejecutar la herramienta
                result = tools_manager.execute_tool(tool_name, tool_args)

                # Registrar la acción en la tabla de acciones
                ChatbotAction.create(
                    session_id=chat_session['id'],
                    message_id=assistant_message_id,
                    action_type=tool_name,
                    action_params=tool_args,
                    action_result=result.get('data') if result.get('success') else None,
                    success=result.get('success', False),
                    error_message=result.get('error')
                )

                # Preparar resultado de la herramienta
                tool_result_content = json.dumps(result, ensure_ascii=False, cls=DateTimeEncoder)

                # Agregar resultado EN MEMORIA
                tool_results.append({
                    'role': 'tool',
                    'tool_call_id': tool_call['id'],
                    'content': tool_result_content
                })

                # ✅ GUARDAR mensaje de tipo 'tool' EN BASE DE DATOS
                ChatbotMessage.create(
                    session_id=chat_session['id'],
                    role='tool',
                    content=tool_result_content,
                    metadata={'tool_call_id': tool_call['id'], 'tool_name': tool_name}
                )

            # Agregar resultados de herramientas a los mensajes EN MEMORIA
            messages.extend(tool_results)

        # Si llegamos al límite de iteraciones sin respuesta
        if assistant_response is None:
            assistant_response = "Lo siento, he tenido problemas para procesar tu solicitud. ¿Podrías reformular tu pregunta?"

        # Guardar respuesta del asistente
        ChatbotMessage.create(
            session_id=chat_session['id'],
            role='assistant',
            content=assistant_response
        )

        return jsonify({
            'success': True,
            'response': assistant_response,
            'session_id': chat_session['session_key']
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error en chatbot: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """
    Obtiene el historial de conversación del usuario actual
    """
    try:
        user_id = session['user_id']
        chat_session = ChatbotSession.get_active_session(user_id)

        if not chat_session:
            return jsonify({
                'success': True,
                'messages': []
            })

        # 🧹 Limpiar mensajes incompletos de la base de datos (si existen)
        deleted_count = ChatbotMessage.cleanup_incomplete_tool_calls_from_db(chat_session['id'])

        # Obtener historial (recargar si se eliminaron mensajes)
        history = ChatbotMessage.get_conversation_history(chat_session['id'])

        # Filtrar solo mensajes de usuario y asistente
        messages = [
            {
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat() if msg.get('timestamp') else None
            }
            for msg in history
            if msg['role'] in ['user', 'assistant']
        ]

        return jsonify({
            'success': True,
            'messages': messages,
            'session_id': chat_session['session_key']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/new-session', methods=['POST'])
@login_required
def new_session():
    """
    Crea una nueva sesión de chatbot (resetea la conversación)
    """
    try:
        user_id = session['user_id']

        # Desactivar sesión actual si existe
        current_session = ChatbotSession.get_active_session(user_id)
        if current_session:
            ChatbotSession.deactivate_session(current_session['id'])

        # Crear nueva sesión
        new_chat_session = ChatbotSession.create(user_id)

        return jsonify({
            'success': True,
            'message': 'Nueva sesión creada',
            'session_id': new_chat_session['session_key']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/status', methods=['GET'])
@login_required
def status():
    """
    Verifica el estado del chatbot y la configuración del LLM
    """
    try:
        # Verificar si hay API key configurada
        has_api_key = bool(os.environ.get('LLM_API_KEY'))

        llm_config = {
            'api_configured': has_api_key,
            'model': os.environ.get('LLM_MODEL', 'gpt-4o-mini'),
            'api_base': os.environ.get('LLM_API_BASE', 'https://api.openai.com/v1'),
            'mode': 'production' if has_api_key else 'development'
        }

        # Obtener información de sesión actual
        user_id = session['user_id']
        chat_session = ChatbotSession.get_active_session(user_id)

        session_info = None
        if chat_session:
            message_count = len(ChatbotMessage.get_conversation_history(chat_session['id']))
            session_info = {
                'session_id': chat_session['session_key'],
                'message_count': message_count,
                'active': chat_session['activa']
            }

        return jsonify({
            'success': True,
            'llm_config': llm_config,
            'session': session_info,
            'user': {
                'nombre': session.get('nombre_completo'),
                'rol': session.get('rol')
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/session-summary', methods=['GET'])
@login_required
def session_summary():
    """
    Obtiene un resumen detallado de la sesión actual
    """
    try:
        user_id = session['user_id']
        chat_session = ChatbotSession.get_active_session(user_id)

        if not chat_session:
            return jsonify({
                'success': True,
                'summary': {
                    'active': False,
                    'message': 'No hay sesión activa'
                }
            })

        # Obtener historial completo
        history = ChatbotMessage.get_conversation_history(chat_session['id'], limit=200)

        # Contar tipos de mensajes
        user_messages = sum(1 for msg in history if msg['role'] == 'user')
        assistant_messages = sum(1 for msg in history if msg['role'] == 'assistant')
        system_messages = sum(1 for msg in history if msg['role'] == 'system')

        # Estimar tokens
        formatted = ChatbotMessage.format_for_llm(history)
        estimated_tokens = ChatbotMessage.estimate_tokens(formatted)

        # Obtener acciones ejecutadas
        from database import execute_query
        actions_query = """
            SELECT action_type, COUNT(*) as count, SUM(success) as successful
            FROM chatbot_actions
            WHERE session_id = %s
            GROUP BY action_type
        """
        actions_stats = execute_query(actions_query, (chat_session['id'],)) or []

        return jsonify({
            'success': True,
            'summary': {
                'active': True,
                'session_id': chat_session['session_key'],
                'started': chat_session['fecha_inicio'].isoformat() if chat_session.get('fecha_inicio') else None,
                'last_message': chat_session['fecha_ultimo_mensaje'].isoformat() if chat_session.get('fecha_ultimo_mensaje') else None,
                'total_messages': len(history),
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'system_messages': system_messages,
                'estimated_tokens': estimated_tokens,
                'actions_executed': [
                    {
                        'type': action['action_type'],
                        'count': action['count'],
                        'successful': action['successful']
                    }
                    for action in actions_stats
                ] if actions_stats else []
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """
    Limpia el historial de mensajes de la sesión actual (mantiene la sesión activa)
    """
    try:
        user_id = session['user_id']
        chat_session = ChatbotSession.get_active_session(user_id)

        if not chat_session:
            return jsonify({
                'success': False,
                'error': 'No hay sesión activa'
            }), 404

        # Eliminar todos los mensajes de la sesión
        from database import execute_query
        delete_messages = "DELETE FROM chatbot_messages WHERE session_id = %s"
        execute_query(delete_messages, (chat_session['id'],), fetch=False)

        delete_actions = "DELETE FROM chatbot_actions WHERE session_id = %s"
        execute_query(delete_actions, (chat_session['id'],), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Historial de conversación limpiado exitosamente',
            'session_id': chat_session['session_key']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/session-stats', methods=['GET'])
@login_required
def session_stats():
    """
    Obtiene estadísticas de todas las sesiones del usuario
    """
    try:
        user_id = session['user_id']

        from database import execute_query

        # Obtener todas las sesiones del usuario
        sessions_query = """
            SELECT
                s.id,
                s.session_key,
                s.fecha_inicio,
                s.fecha_ultimo_mensaje,
                s.activa,
                COUNT(DISTINCT m.id) as message_count
            FROM chatbot_sessions s
            LEFT JOIN chatbot_messages m ON m.session_id = s.id
            WHERE s.usuario_id = %s
            GROUP BY s.id, s.session_key, s.fecha_inicio, s.fecha_ultimo_mensaje, s.activa
            ORDER BY s.fecha_inicio DESC
            LIMIT 10
        """
        sessions = execute_query(sessions_query, (user_id,)) or []

        sessions_data = []
        for sess in sessions:
            sessions_data.append({
                'session_id': sess['session_key'],
                'started': sess['fecha_inicio'].isoformat() if sess.get('fecha_inicio') else None,
                'last_message': sess['fecha_ultimo_mensaje'].isoformat() if sess.get('fecha_ultimo_mensaje') else None,
                'active': bool(sess['activa']),
                'message_count': sess['message_count']
            })

        return jsonify({
            'success': True,
            'total_sessions': len(sessions),
            'sessions': sessions_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
