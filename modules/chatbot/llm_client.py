"""
Cliente para conectarse con LLM (Large Language Model)
Soporta OpenAI API y APIs compatibles
"""
import os
import json
import requests
from typing import List, Dict, Optional


class LLMClient:
    """Cliente para interactuar con APIs de LLM"""

    def __init__(self):
        """Inicializa el cliente LLM con la configuración del entorno"""
        self.api_key = os.environ.get('LLM_API_KEY', '')
        self.api_base = os.environ.get('LLM_API_BASE', 'https://api.openai.com/v1')
        self.model = os.environ.get('LLM_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.environ.get('LLM_MAX_TOKENS', '2000'))
        self.temperature = float(os.environ.get('LLM_TEMPERATURE', '0.7'))
        self.verbosity = os.environ.get('LLM_VERBOSITY', 'medium')
        self.reasoning_effort = os.environ.get('LLM_REASONING_EFFORT', 'medium')

        # Detectar si es un modelo GPT-5.1
        self.is_gpt51 = 'gpt-5.1' in self.model.lower() or 'gpt-5-1' in self.model.lower()

        if not self.api_key:
            raise ValueError("LLM_API_KEY no está configurada en las variables de entorno")

    def chat_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict:
        """
        Envía una solicitud de chat completion al LLM

        Args:
            messages: Lista de mensajes en formato OpenAI
            tools: Lista de herramientas disponibles para el LLM
            tool_choice: Cómo el LLM debe elegir herramientas ("auto", "none", o específica)

        Returns:
            dict: Respuesta del LLM
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'max_completion_tokens': self.max_tokens,  # Actualizado a max_completion_tokens
        }

        # GPT-5.1 usa 'verbosity' y 'reasoning_effort' en lugar de 'temperature'
        if self.is_gpt51:
            payload['verbosity'] = self.verbosity
            # Agregar reasoning_effort para habilitar razonamiento adaptativo
            if self.reasoning_effort and self.reasoning_effort != 'none':
                payload['reasoning_effort'] = self.reasoning_effort
            # GPT-5.1 solo acepta temperature=1 (valor por defecto, no es necesario enviarlo)
        else:
            # Modelos anteriores (GPT-4, GPT-4o, etc.) usan temperature
            payload['temperature'] = self.temperature

        # Agregar tools si están disponibles
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = tool_choice

        try:
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"Error al conectar con el LLM: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text}"
            raise Exception(error_msg)

    def extract_response(self, llm_response: Dict) -> tuple:
        """
        Extrae el contenido de la respuesta del LLM

        Args:
            llm_response: Respuesta completa del LLM

        Returns:
            tuple: (contenido_texto, tool_calls)
        """
        try:
            choice = llm_response['choices'][0]
            message = choice['message']

            content = message.get('content', '')
            tool_calls = message.get('tool_calls', None)

            return content, tool_calls

        except (KeyError, IndexError) as e:
            raise Exception(f"Formato de respuesta del LLM inválido: {str(e)}")

    def build_system_message(self, user_info: Dict, available_actions: List[str]) -> str:
        """
        Construye el mensaje del sistema con contexto del usuario

        Args:
            user_info: Información del usuario actual
            available_actions: Lista de acciones disponibles para el usuario

        Returns:
            str: Mensaje del sistema
        """
        actions_text = "\n".join([f"- {action}" for action in available_actions])

        system_message = f"""Eres un asistente virtual inteligente para el portal de intranet corporativo.

INFORMACIÓN DEL USUARIO:
- Nombre: {user_info.get('nombre_completo', 'Usuario')}
- Rol: {user_info.get('rol', 'empleado')}
- Username: {user_info.get('username', '')}

CAPACIDADES:
Puedes ayudar al usuario de dos formas principales:

1. EJECUTAR ACCIONES en la intranet (usando las herramientas disponibles):
{actions_text}

2. RESPONDER PREGUNTAS sobre información del sistema:
   - Consultar datos de empleados, departamentos, documentos
   - Consultar estado de vacaciones y tickets
   - Proporcionar estadísticas y resúmenes
   - Explicar políticas y procedimientos

INSTRUCCIONES IMPORTANTES:
- Sé conversacional, amable y profesional
- Recuerda el contexto de la conversación para no repetir preguntas
- Cuando ejecutes acciones, confirma los detalles antes de proceder
- Si necesitas información adicional para una acción, pregunta específicamente
- Proporciona respuestas claras y concisas
- Si no puedes realizar una acción debido a permisos, explícalo amablemente
- Usa las herramientas disponibles cuando sea apropiado
- Para consultas de información, usa las herramientas de consulta

FORMATO DE RESPUESTAS:
- Para acciones exitosas: Confirma lo realizado y proporciona detalles.
    - Si te piden por ejemplo "vacaciones", no pidas el tipo de solicitud y considera en el conteo de días solo días hábiles. Evita obviedades y redundancias.
- Para consultas: Presenta la información de forma clara y organizada
- Para errores: Explica el problema y sugiere alternativas si es posible

Mantén un tono profesional pero cercano, como un asistente administrativo experimentado."""

        return system_message


class MockLLMClient(LLMClient):
    """Cliente Mock para desarrollo y testing sin API key real"""

    def __init__(self):
        """Inicializa el cliente mock sin requerir API key"""
        self.api_key = "mock_key"
        self.api_base = "mock"
        self.model = "mock-model"
        self.max_tokens = 2000
        self.temperature = 0.7

    def chat_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict:
        """
        Simula una respuesta del LLM para desarrollo

        Returns:
            dict: Respuesta simulada
        """
        last_message = messages[-1]['content'] if messages else ""

        # Respuesta simulada básica
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': f'Respuesta simulada para: "{last_message}". '
                               f'Este es el modo de desarrollo. Configura LLM_API_KEY para usar un LLM real.'
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }
