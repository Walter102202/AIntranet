"""
Herramientas y acciones disponibles para el chatbot
Define las funciones que el LLM puede llamar para ejecutar acciones
"""
import json
from datetime import datetime, timedelta, date
from models import User, Employee, Department, Vacation, Document, Announcement, Ticket


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


class ChatbotTools:
    """Gestor de herramientas del chatbot"""

    def __init__(self, user_info):
        """
        Inicializa las herramientas con información del usuario

        Args:
            user_info: Diccionario con información del usuario actual
        """
        self.user_info = user_info
        self.user_id = user_info['id']
        self.user_role = user_info['rol']

    def get_available_tools(self):
        """
        Retorna las herramientas disponibles según el rol del usuario
        en formato de OpenAI function calling

        Returns:
            list: Lista de herramientas disponibles
        """
        tools = []

        # Herramientas de consulta (disponibles para todos)
        tools.extend([
            self._get_employees_info_tool(),
            self._get_departments_info_tool(),
            self._get_documents_info_tool(),
            self._get_my_vacations_tool(),
            self._get_my_tickets_tool(),
            self._get_announcements_tool(),
        ])

        # Herramientas de acción para empleados
        tools.extend([
            self._request_vacation_tool(),
            self._create_ticket_tool(),
        ])

        # Herramientas adicionales para RRHH
        if self.user_role in ['admin', 'rrhh']:
            tools.extend([
                self._get_all_vacations_tool(),
                self._approve_vacation_tool(),
                self._reject_vacation_tool(),
            ])

        # Herramientas adicionales para Soporte
        if self.user_role in ['admin', 'soporte']:
            tools.extend([
                self._get_all_tickets_tool(),
                self._update_ticket_status_tool(),
                self._assign_ticket_tool(),
            ])

        # Herramientas adicionales para Admin
        if self.user_role == 'admin':
            tools.extend([
                self._create_user_tool(),
                self._create_announcement_tool(),
                self._get_system_stats_tool(),
            ])

        return tools

    def execute_tool(self, tool_name, arguments):
        """
        Ejecuta una herramienta por su nombre

        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta (dict)

        Returns:
            dict: Resultado de la ejecución
        """
        # Mapeo de nombres de herramientas a métodos
        tool_map = {
            'get_employees_info': self._execute_get_employees_info,
            'get_departments_info': self._execute_get_departments_info,
            'get_documents_info': self._execute_get_documents_info,
            'get_my_vacations': self._execute_get_my_vacations,
            'get_my_tickets': self._execute_get_my_tickets,
            'get_announcements': self._execute_get_announcements,
            'request_vacation': self._execute_request_vacation,
            'create_ticket': self._execute_create_ticket,
            'get_all_vacations': self._execute_get_all_vacations,
            'approve_vacation': self._execute_approve_vacation,
            'reject_vacation': self._execute_reject_vacation,
            'get_all_tickets': self._execute_get_all_tickets,
            'update_ticket_status': self._execute_update_ticket_status,
            'assign_ticket': self._execute_assign_ticket,
            'create_user': self._execute_create_user,
            'create_announcement': self._execute_create_announcement,
            'get_system_stats': self._execute_get_system_stats,
        }

        if tool_name not in tool_map:
            return {'success': False, 'error': f'Herramienta "{tool_name}" no encontrada'}

        try:
            result = tool_map[tool_name](arguments)
            # Convertir datetime a strings para que sea serializable a JSON
            result_serializable = convert_datetime_to_str(result)
            return {'success': True, 'data': result_serializable}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== DEFINICIONES DE HERRAMIENTAS (OpenAI Format) ==========

    def _get_employees_info_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_employees_info",
                "description": "Obtiene información sobre empleados. Puede buscar por nombre o listar todos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Término de búsqueda (nombre, cargo, email). Opcional."
                        }
                    }
                }
            }
        }

    def _get_departments_info_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_departments_info",
                "description": "Obtiene información sobre los departamentos de la empresa.",
                "parameters": {"type": "object", "properties": {}}
            }
        }

    def _get_documents_info_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_documents_info",
                "description": "Consulta documentos corporativos disponibles. Puede filtrar por categoría.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "categoria": {
                            "type": "string",
                            "description": "Categoría de documentos",
                            "enum": ["politicas", "procedimientos", "manuales", "formularios", "otros"]
                        }
                    }
                }
            }
        }

    def _get_my_vacations_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_my_vacations",
                "description": "Obtiene las solicitudes de vacaciones del usuario actual.",
                "parameters": {"type": "object", "properties": {}}
            }
        }

    def _get_my_tickets_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_my_tickets",
                "description": "Obtiene los tickets de soporte creados por el usuario actual.",
                "parameters": {"type": "object", "properties": {}}
            }
        }

    def _get_announcements_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_announcements",
                "description": "Obtiene los anuncios activos de la intranet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Número máximo de anuncios a retornar (default: 5)"
                        }
                    }
                }
            }
        }

    def _request_vacation_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "request_vacation",
                "description": "Solicita vacaciones o permisos para el usuario actual.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_inicio": {
                            "type": "string",
                            "description": "Fecha de inicio en formato YYYY-MM-DD"
                        },
                        "fecha_fin": {
                            "type": "string",
                            "description": "Fecha de fin en formato YYYY-MM-DD"
                        },
                        "tipo": {
                            "type": "string",
                            "description": "Tipo de solicitud",
                            "enum": ["vacaciones", "permiso", "licencia_medica", "otro"]
                        },
                        "motivo": {
                            "type": "string",
                            "description": "Motivo de la solicitud"
                        }
                    },
                    "required": ["fecha_inicio", "fecha_fin", "tipo"]
                }
            }
        }

    def _create_ticket_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_ticket",
                "description": "Crea un nuevo ticket de soporte.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {
                            "type": "string",
                            "description": "Título del ticket"
                        },
                        "descripcion": {
                            "type": "string",
                            "description": "Descripción detallada del problema"
                        },
                        "categoria": {
                            "type": "string",
                            "description": "Categoría del ticket",
                            "enum": ["ti", "rrhh", "mantenimiento", "administrativo", "otro"]
                        },
                        "prioridad": {
                            "type": "string",
                            "description": "Prioridad del ticket",
                            "enum": ["baja", "media", "alta", "urgente"]
                        }
                    },
                    "required": ["titulo", "descripcion", "categoria"]
                }
            }
        }

    def _get_all_vacations_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_all_vacations",
                "description": "Obtiene todas las solicitudes de vacaciones (solo RRHH/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {
                            "type": "string",
                            "description": "Filtrar por estado",
                            "enum": ["pendiente", "aprobada", "rechazada", "cancelada"]
                        }
                    }
                }
            }
        }

    def _approve_vacation_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "approve_vacation",
                "description": "Aprueba una solicitud de vacaciones (solo RRHH/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vacation_id": {
                            "type": "integer",
                            "description": "ID de la solicitud de vacaciones"
                        },
                        "comentarios": {
                            "type": "string",
                            "description": "Comentarios del aprobador (opcional)"
                        }
                    },
                    "required": ["vacation_id"]
                }
            }
        }

    def _reject_vacation_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "reject_vacation",
                "description": "Rechaza una solicitud de vacaciones (solo RRHH/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vacation_id": {
                            "type": "integer",
                            "description": "ID de la solicitud de vacaciones"
                        },
                        "comentarios": {
                            "type": "string",
                            "description": "Motivo del rechazo"
                        }
                    },
                    "required": ["vacation_id", "comentarios"]
                }
            }
        }

    def _get_all_tickets_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_all_tickets",
                "description": "Obtiene todos los tickets de soporte (solo Soporte/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {
                            "type": "string",
                            "description": "Filtrar por estado",
                            "enum": ["abierto", "en_proceso", "resuelto", "cerrado"]
                        }
                    }
                }
            }
        }

    def _update_ticket_status_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "update_ticket_status",
                "description": "Actualiza el estado de un ticket (solo Soporte/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "ID del ticket"
                        },
                        "estado": {
                            "type": "string",
                            "description": "Nuevo estado",
                            "enum": ["abierto", "en_proceso", "resuelto", "cerrado"]
                        }
                    },
                    "required": ["ticket_id", "estado"]
                }
            }
        }

    def _assign_ticket_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "assign_ticket",
                "description": "Asigna un ticket a un usuario (solo Soporte/Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "ID del ticket"
                        },
                        "assigned_to": {
                            "type": "integer",
                            "description": "ID del usuario al que se asigna"
                        }
                    },
                    "required": ["ticket_id", "assigned_to"]
                }
            }
        }

    def _create_user_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_user",
                "description": "Crea un nuevo usuario en el sistema (solo Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Nombre de usuario"},
                        "password": {"type": "string", "description": "Contraseña"},
                        "email": {"type": "string", "description": "Email"},
                        "nombre_completo": {"type": "string", "description": "Nombre completo"},
                        "rol": {
                            "type": "string",
                            "description": "Rol del usuario",
                            "enum": ["admin", "empleado", "rrhh", "soporte"]
                        }
                    },
                    "required": ["username", "password", "email", "nombre_completo", "rol"]
                }
            }
        }

    def _create_announcement_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "create_announcement",
                "description": "Crea un nuevo anuncio en la intranet (solo Admin).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string", "description": "Título del anuncio"},
                        "contenido": {"type": "string", "description": "Contenido del anuncio"},
                        "tipo": {
                            "type": "string",
                            "description": "Tipo de anuncio",
                            "enum": ["general", "urgente", "evento", "comunicado"]
                        },
                        "prioridad": {
                            "type": "string",
                            "description": "Prioridad",
                            "enum": ["baja", "media", "alta"]
                        }
                    },
                    "required": ["titulo", "contenido", "tipo"]
                }
            }
        }

    def _get_system_stats_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "get_system_stats",
                "description": "Obtiene estadísticas generales del sistema (solo Admin).",
                "parameters": {"type": "object", "properties": {}}
            }
        }

    # ========== IMPLEMENTACIONES DE HERRAMIENTAS ==========

    def _execute_get_employees_info(self, args):
        """Obtiene información de empleados"""
        search_term = args.get('search_term', '')

        if search_term:
            employees = Employee.search(search_term)
        else:
            employees = Employee.get_all()

        # Manejar el caso donde employees puede ser None
        if employees is None:
            employees = []

        return {
            'total': len(employees),
            'empleados': employees[:20]  # Limitar a 20 resultados
        }

    def _execute_get_departments_info(self, args):
        """Obtiene información de departamentos"""
        departments = Department.get_all()
        # Manejar el caso donde departments puede ser None
        if departments is None:
            departments = []
        return {'departamentos': departments}

    def _execute_get_documents_info(self, args):
        """Consulta documentos"""
        categoria = args.get('categoria')

        if categoria:
            documents = Document.get_by_category(categoria)
        else:
            documents = Document.get_all()

        # Manejar el caso donde documents puede ser None
        if documents is None:
            documents = []

        return {
            'total': len(documents),
            'documentos': documents
        }

    def _execute_get_my_vacations(self, args):
        """Obtiene vacaciones del usuario actual"""
        # Obtener empleado asociado al usuario
        employee = Employee.get_by_user_id(self.user_id)
        if not employee:
            return {'error': 'No tienes un perfil de empleado asociado', 'vacaciones': []}

        vacations = Vacation.get_by_employee(employee['id'])
        if vacations is None:
            vacations = []
        return {'vacaciones': vacations}

    def _execute_get_my_tickets(self, args):
        """Obtiene tickets del usuario actual"""
        tickets = Ticket.get_by_user(self.user_id)
        if tickets is None:
            tickets = []
        return {'tickets': tickets}

    def _execute_get_announcements(self, args):
        """Obtiene anuncios activos"""
        limit = args.get('limit', 5)
        announcements = Announcement.get_active()
        if announcements is None:
            announcements = []
        return {'anuncios': announcements[:limit]}

    def _execute_request_vacation(self, args):
        """Solicita vacaciones"""
        try:
            # Obtener empleado asociado
            employee = Employee.get_by_user_id(self.user_id)
            if not employee:
                return {
                    'success': False,
                    'error': 'No tienes un perfil de empleado asociado. Contacta a RRHH para crear tu perfil.'
                }

            # Calcular días solicitados
            fecha_inicio = datetime.strptime(args['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(args['fecha_fin'], '%Y-%m-%d').date()
            dias = (fecha_fin - fecha_inicio).days + 1

            # Validar fechas
            if dias <= 0:
                return {
                    'success': False,
                    'error': 'La fecha de fin debe ser posterior a la fecha de inicio'
                }

            # Crear solicitud de vacaciones (parámetro correcto: 'dias', no 'dias_solicitados')
            vacation_id = Vacation.create(
                employee_id=employee['id'],
                fecha_inicio=args['fecha_inicio'],
                fecha_fin=args['fecha_fin'],
                dias=dias,  # ✅ CORREGIDO: era 'dias_solicitados'
                tipo=args['tipo'],
                motivo=args.get('motivo', '')
            )

            if not vacation_id:
                return {
                    'success': False,
                    'error': 'No se pudo crear la solicitud de vacaciones. Intenta de nuevo o contacta a soporte.'
                }

            return {
                'success': True,
                'vacation_id': vacation_id,
                'mensaje': f'✅ Solicitud de {args["tipo"]} creada exitosamente para {dias} días (del {args["fecha_inicio"]} al {args["fecha_fin"]}). Estado: Pendiente de aprobación.',
                'datos': {
                    'id': vacation_id,
                    'empleado': employee['nombre'] + ' ' + employee['apellido'],
                    'fecha_inicio': args['fecha_inicio'],
                    'fecha_fin': args['fecha_fin'],
                    'dias': dias,
                    'tipo': args['tipo'],
                    'estado': 'pendiente'
                }
            }
        except ValueError as e:
            return {
                'success': False,
                'error': f'Formato de fecha inválido. Usa el formato YYYY-MM-DD (ej: 2026-02-23). Error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al crear la solicitud: {str(e)}'
            }

    def _execute_create_ticket(self, args):
        """Crea un ticket de soporte"""
        try:
            # Validar campos requeridos
            if not args.get('titulo') or not args.get('titulo').strip():
                return {
                    'success': False,
                    'error': 'El título del ticket es requerido y no puede estar vacío'
                }

            if not args.get('descripcion') or not args.get('descripcion').strip():
                return {
                    'success': False,
                    'error': 'La descripción del ticket es requerida y no puede estar vacía'
                }

            # Crear ticket
            ticket_id = Ticket.create(
                titulo=args['titulo'],
                descripcion=args['descripcion'],
                categoria=args['categoria'],
                prioridad=args.get('prioridad', 'media'),
                solicitante_id=self.user_id
            )

            if not ticket_id:
                return {
                    'success': False,
                    'error': 'No se pudo crear el ticket. Intenta de nuevo o contacta a soporte.'
                }

            return {
                'success': True,
                'ticket_id': ticket_id,
                'mensaje': f'✅ Ticket #{ticket_id} creado exitosamente. Estado: Abierto. Un miembro del equipo de soporte lo atenderá pronto.',
                'datos': {
                    'id': ticket_id,
                    'titulo': args['titulo'],
                    'categoria': args['categoria'],
                    'prioridad': args.get('prioridad', 'media'),
                    'estado': 'abierto',
                    'solicitante': self.user_info.get('nombre_completo', 'Usuario')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al crear el ticket: {str(e)}'
            }

    def _execute_get_all_vacations(self, args):
        """Obtiene todas las solicitudes de vacaciones (RRHH/Admin)"""
        if self.user_role not in ['admin', 'rrhh']:
            raise Exception('No tienes permisos para esta acción')

        vacations = Vacation.get_all()
        if vacations is None:
            vacations = []

        # Filtrar por estado si se especifica
        estado = args.get('estado')
        if estado and vacations:
            vacations = [v for v in vacations if v['estado'] == estado]

        return {'vacaciones': vacations}

    def _execute_approve_vacation(self, args):
        """Aprueba una solicitud de vacaciones (RRHH/Admin)"""
        try:
            # Verificar permisos
            if self.user_role not in ['admin', 'rrhh']:
                return {
                    'success': False,
                    'error': 'No tienes permisos para aprobar vacaciones. Esta acción está reservada para RRHH y Administradores.'
                }

            # Validar vacation_id
            if not args.get('vacation_id'):
                return {
                    'success': False,
                    'error': 'Se requiere el ID de la solicitud de vacaciones'
                }

            # Actualizar estado
            result = Vacation.update_status(
                vacation_id=args['vacation_id'],
                estado='aprobada',
                aprobador_id=self.user_id,
                comentarios=args.get('comentarios', '')
            )

            # Verificar resultado
            if result is False or result == 0:
                return {
                    'success': False,
                    'error': f'No se pudo aprobar la solicitud #{args["vacation_id"]}. Verifica que el ID sea correcto y que la solicitud exista.'
                }

            return {
                'success': True,
                'mensaje': f'✅ Solicitud de vacaciones #{args["vacation_id"]} aprobada exitosamente.',
                'datos': {
                    'vacation_id': args["vacation_id"],
                    'estado': 'aprobada',
                    'aprobador': self.user_info.get('nombre_completo', 'Usuario'),
                    'comentarios': args.get('comentarios', '')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al aprobar la solicitud: {str(e)}'
            }

    def _execute_reject_vacation(self, args):
        """Rechaza una solicitud de vacaciones (RRHH/Admin)"""
        try:
            # Verificar permisos
            if self.user_role not in ['admin', 'rrhh']:
                return {
                    'success': False,
                    'error': 'No tienes permisos para rechazar vacaciones. Esta acción está reservada para RRHH y Administradores.'
                }

            # Validar vacation_id
            if not args.get('vacation_id'):
                return {
                    'success': False,
                    'error': 'Se requiere el ID de la solicitud de vacaciones'
                }

            # Validar comentarios (requeridos para rechazo)
            if not args.get('comentarios') or not args.get('comentarios').strip():
                return {
                    'success': False,
                    'error': 'Se requiere un motivo/comentario para rechazar la solicitud de vacaciones'
                }

            # Actualizar estado
            result = Vacation.update_status(
                vacation_id=args['vacation_id'],
                estado='rechazada',
                aprobador_id=self.user_id,
                comentarios=args['comentarios']
            )

            # Verificar resultado
            if result is False or result == 0:
                return {
                    'success': False,
                    'error': f'No se pudo rechazar la solicitud #{args["vacation_id"]}. Verifica que el ID sea correcto y que la solicitud exista.'
                }

            return {
                'success': True,
                'mensaje': f'✅ Solicitud de vacaciones #{args["vacation_id"]} rechazada.',
                'datos': {
                    'vacation_id': args["vacation_id"],
                    'estado': 'rechazada',
                    'aprobador': self.user_info.get('nombre_completo', 'Usuario'),
                    'comentarios': args['comentarios']
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al rechazar la solicitud: {str(e)}'
            }

    def _execute_get_all_tickets(self, args):
        """Obtiene todos los tickets (Soporte/Admin)"""
        if self.user_role not in ['admin', 'soporte']:
            raise Exception('No tienes permisos para ver todos los tickets')

        tickets = Ticket.get_all()
        if tickets is None:
            tickets = []

        # Filtrar por estado si se especifica
        estado = args.get('estado')
        if estado and tickets:
            tickets = [t for t in tickets if t['estado'] == estado]

        return {'tickets': tickets}

    def _execute_update_ticket_status(self, args):
        """Actualiza estado de un ticket (Soporte/Admin)"""
        try:
            # Verificar permisos
            if self.user_role not in ['admin', 'soporte']:
                return {
                    'success': False,
                    'error': 'No tienes permisos para actualizar tickets. Esta acción está reservada para Soporte y Administradores.'
                }

            # Validar ticket_id
            if not args.get('ticket_id'):
                return {
                    'success': False,
                    'error': 'Se requiere el ID del ticket'
                }

            # Validar estado
            estados_validos = ['abierto', 'en_proceso', 'resuelto', 'cerrado']
            if not args.get('estado') or args['estado'] not in estados_validos:
                return {
                    'success': False,
                    'error': f'Estado inválido. Estados permitidos: {", ".join(estados_validos)}'
                }

            # Actualizar estado
            result = Ticket.update_status(
                ticket_id=args['ticket_id'],
                estado=args['estado'],
                asignado_a=None
            )

            # Verificar resultado
            if result is False or result == 0:
                return {
                    'success': False,
                    'error': f'No se pudo actualizar el ticket #{args["ticket_id"]}. Verifica que el ID sea correcto y que el ticket exista.'
                }

            return {
                'success': True,
                'mensaje': f'✅ Ticket #{args["ticket_id"]} actualizado exitosamente.',
                'datos': {
                    'ticket_id': args["ticket_id"],
                    'estado': args['estado'],
                    'actualizado_por': self.user_info.get('nombre_completo', 'Usuario')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al actualizar el ticket: {str(e)}'
            }

    def _execute_assign_ticket(self, args):
        """Asigna un ticket a un usuario (Soporte/Admin)"""
        try:
            # Verificar permisos
            if self.user_role not in ['admin', 'soporte']:
                return {
                    'success': False,
                    'error': 'No tienes permisos para asignar tickets. Esta acción está reservada para Soporte y Administradores.'
                }

            # Validar ticket_id
            if not args.get('ticket_id'):
                return {
                    'success': False,
                    'error': 'Se requiere el ID del ticket'
                }

            # Validar assigned_to
            if not args.get('assigned_to'):
                return {
                    'success': False,
                    'error': 'Se requiere el ID del usuario al que se asignará el ticket'
                }

            # Verificar que el usuario asignado existe
            assigned_user = User.get_by_id(args['assigned_to'])
            if not assigned_user:
                return {
                    'success': False,
                    'error': f'El usuario con ID {args["assigned_to"]} no existe'
                }

            # Asignar ticket
            result = Ticket.update_status(
                ticket_id=args['ticket_id'],
                estado='en_proceso',
                asignado_a=args['assigned_to']
            )

            # Verificar resultado
            if result is False or result == 0:
                return {
                    'success': False,
                    'error': f'No se pudo asignar el ticket #{args["ticket_id"]}. Verifica que el ID sea correcto y que el ticket exista.'
                }

            return {
                'success': True,
                'mensaje': f'✅ Ticket #{args["ticket_id"]} asignado exitosamente a {assigned_user.get("nombre_completo", "usuario")}.',
                'datos': {
                    'ticket_id': args["ticket_id"],
                    'estado': 'en_proceso',
                    'asignado_a': assigned_user.get('nombre_completo', 'Usuario'),
                    'asignado_por': self.user_info.get('nombre_completo', 'Usuario')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al asignar el ticket: {str(e)}'
            }

    def _execute_create_user(self, args):
        """Crea un nuevo usuario (Admin)"""
        try:
            import re

            # Verificar permisos
            if self.user_role != 'admin':
                return {
                    'success': False,
                    'error': 'Solo los administradores pueden crear usuarios'
                }

            # Validar campos requeridos
            required_fields = ['username', 'password', 'email', 'nombre_completo', 'rol']
            for field in required_fields:
                if not args.get(field) or not str(args[field]).strip():
                    return {
                        'success': False,
                        'error': f'El campo "{field}" es requerido y no puede estar vacío'
                    }

            # Validar formato de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, args['email']):
                return {
                    'success': False,
                    'error': 'El formato del email es inválido. Usa el formato: usuario@dominio.com'
                }

            # Validar longitud de username
            if len(args['username']) < 3:
                return {
                    'success': False,
                    'error': 'El username debe tener al menos 3 caracteres'
                }

            # Validar longitud de password
            if len(args['password']) < 6:
                return {
                    'success': False,
                    'error': 'La contraseña debe tener al menos 6 caracteres'
                }

            # Validar rol
            roles_validos = ['admin', 'empleado', 'rrhh', 'soporte']
            if args['rol'] not in roles_validos:
                return {
                    'success': False,
                    'error': f'Rol inválido. Roles permitidos: {", ".join(roles_validos)}'
                }

            # Crear usuario
            user_id = User.create(
                username=args['username'],
                password=args['password'],
                email=args['email'],
                nombre_completo=args['nombre_completo'],
                rol=args['rol']
            )

            if not user_id:
                return {
                    'success': False,
                    'error': 'No se pudo crear el usuario. Es posible que el username o email ya existan.'
                }

            return {
                'success': True,
                'user_id': user_id,
                'mensaje': f'✅ Usuario "{args["username"]}" creado exitosamente con rol {args["rol"]}.',
                'datos': {
                    'id': user_id,
                    'username': args['username'],
                    'email': args['email'],
                    'nombre_completo': args['nombre_completo'],
                    'rol': args['rol']
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al crear el usuario: {str(e)}'
            }

    def _execute_create_announcement(self, args):
        """Crea un anuncio (Admin)"""
        try:
            # Verificar permisos
            if self.user_role != 'admin':
                return {
                    'success': False,
                    'error': 'Solo los administradores pueden crear anuncios'
                }

            # Validar campos requeridos
            if not args.get('titulo') or not args.get('titulo').strip():
                return {
                    'success': False,
                    'error': 'El título del anuncio es requerido y no puede estar vacío'
                }

            if not args.get('contenido') or not args.get('contenido').strip():
                return {
                    'success': False,
                    'error': 'El contenido del anuncio es requerido y no puede estar vacío'
                }

            # Validar tipo
            tipos_validos = ['general', 'urgente', 'evento', 'comunicado']
            if not args.get('tipo') or args['tipo'] not in tipos_validos:
                return {
                    'success': False,
                    'error': f'Tipo inválido. Tipos permitidos: {", ".join(tipos_validos)}'
                }

            # Validar prioridad (opcional)
            prioridades_validas = ['baja', 'media', 'alta']
            prioridad = args.get('prioridad', 'media')
            if prioridad not in prioridades_validas:
                return {
                    'success': False,
                    'error': f'Prioridad inválida. Prioridades permitidas: {", ".join(prioridades_validas)}'
                }

            # Crear anuncio
            announcement_id = Announcement.create(
                titulo=args['titulo'],
                contenido=args['contenido'],
                tipo=args['tipo'],
                prioridad=prioridad,
                autor_id=self.user_id
            )

            if not announcement_id:
                return {
                    'success': False,
                    'error': 'No se pudo crear el anuncio. Intenta de nuevo o contacta a soporte.'
                }

            return {
                'success': True,
                'announcement_id': announcement_id,
                'mensaje': f'✅ Anuncio "{args["titulo"]}" creado exitosamente con tipo {args["tipo"]} y prioridad {prioridad}.',
                'datos': {
                    'id': announcement_id,
                    'titulo': args['titulo'],
                    'tipo': args['tipo'],
                    'prioridad': prioridad,
                    'autor': self.user_info.get('nombre_completo', 'Usuario')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al crear el anuncio: {str(e)}'
            }

    def _execute_get_system_stats(self, args):
        """Obtiene estadísticas del sistema (Admin)"""
        if self.user_role != 'admin':
            raise Exception('Solo los administradores pueden ver estadísticas del sistema')

        from database import execute_query

        # Obtener estadísticas
        stats = {
            'total_usuarios': execute_query("SELECT COUNT(*) as total FROM usuarios WHERE activo = TRUE", fetch=True)[0]['total'],
            'total_empleados': execute_query("SELECT COUNT(*) as total FROM empleados WHERE activo = TRUE", fetch=True)[0]['total'],
            'total_documentos': execute_query("SELECT COUNT(*) as total FROM documentos WHERE activo = TRUE", fetch=True)[0]['total'],
            'tickets_abiertos': execute_query("SELECT COUNT(*) as total FROM tickets WHERE estado IN ('abierto', 'en_proceso')", fetch=True)[0]['total'],
            'vacaciones_pendientes': execute_query("SELECT COUNT(*) as total FROM vacaciones WHERE estado = 'pendiente'", fetch=True)[0]['total'],
            'anuncios_activos': execute_query("SELECT COUNT(*) as total FROM anuncios WHERE activo = TRUE", fetch=True)[0]['total'],
        }

        return stats
