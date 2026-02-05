# CLAUDE.md - Guía para Asistentes de IA

Este documento proporciona contexto y directrices para que los asistentes de IA trabajen de manera efectiva con este repositorio.

## Descripción del Proyecto

**AIntranet** es un portal de intranet corporativo desarrollado en Python con Flask. Incluye un chatbot inteligente con IA que puede ejecutar acciones (vacaciones, tickets, anuncios) y analizar reportes de Power BI usando capacidades de visión.

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3.8+, Flask 3.0 |
| Base de datos | MySQL 5.7+ |
| Templates | Jinja2 |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Chatbot LLM | OpenAI API (compatible con GPT-4o, GPT-5.1) |
| Autenticación | Sesiones Flask + OAuth (Microsoft, Google) |
| Screenshots | Playwright |

## Estructura del Proyecto

```
AIntranet/
├── app.py                      # Aplicación principal Flask
├── config.py                   # Configuración (env vars)
├── database.py                 # Conexión MySQL y helpers
├── models.py                   # Modelos de datos (Active Record pattern)
├── requirements.txt            # Dependencias Python
├── .env.example                # Plantilla de variables de entorno
│
├── modules/                    # Módulos (Flask Blueprints)
│   ├── auth/                   # Autenticación y usuarios
│   │   ├── __init__.py         # Blueprint: auth_bp, prefix=/auth
│   │   └── routes.py           # Login, logout, OAuth, CRUD usuarios
│   │
│   ├── announcements/          # Anuncios corporativos
│   │   └── routes.py           # Blueprint: announcements_bp, prefix=/announcements
│   │
│   ├── chatbot/                # Chatbot con IA
│   │   ├── __init__.py         # Blueprint: chatbot_bp, prefix=/chatbot
│   │   ├── routes.py           # API endpoints del chat
│   │   ├── models.py           # ChatbotSession, ChatbotMessage, ChatbotAction
│   │   ├── llm_client.py       # Cliente LLM (OpenAI API)
│   │   ├── tools.py            # Herramientas/funciones del chatbot
│   │   └── screenshot_service.py  # Captura de screenshots Power BI
│   │
│   ├── cobranzas/              # Gestión de cobranzas
│   │   └── routes.py           # Blueprint: cobranzas_bp, prefix=/cobranzas
│   │
│   ├── documents/              # Documentos corporativos
│   │   └── routes.py           # Blueprint: documents_bp, prefix=/documents
│   │
│   ├── employees/              # Directorio de empleados
│   │   └── routes.py           # Blueprint: employees_bp, prefix=/employees
│   │
│   ├── kpis/                   # KPIs y reportes Power BI
│   │   └── routes.py           # Blueprint: kpis_bp, prefix=/kpis
│   │
│   ├── tickets/                # Sistema de tickets
│   │   └── routes.py           # Blueprint: tickets_bp, prefix=/tickets
│   │
│   └── vacations/              # Gestión de vacaciones
│       └── routes.py           # Blueprint: vacations_bp, prefix=/vacations
│
├── templates/                  # Plantillas Jinja2
│   ├── base.html               # Template base con navbar y layout
│   ├── login.html              # Página de login
│   ├── dashboard.html          # Dashboard principal
│   ├── 404.html, 500.html      # Páginas de error
│   └── [módulo]/               # Templates por módulo
│
├── static/                     # Archivos estáticos
│   ├── css/
│   │   ├── style.css           # Estilos principales
│   │   └── chatbot.css         # Estilos del chatbot
│   ├── js/
│   │   ├── main.js             # JavaScript principal
│   │   └── chatbot.js          # JavaScript del chatbot
│   └── uploads/                # Archivos subidos por usuarios
│
├── sql/                        # Scripts SQL adicionales
│   ├── migrations/             # Migraciones de BD
│   └── powerbi_reports.sql     # Esquema de reportes Power BI
│
└── screenshots/                # Capturas de pantalla (documentación)
```

## Esquemas de Base de Datos

### Tablas Principales (`schema.sql`)
- `usuarios` - Usuarios del sistema con roles
- `departamentos` - Departamentos de la empresa
- `empleados` - Directorio de empleados
- `vacaciones` - Solicitudes de vacaciones
- `documentos` - Documentos corporativos
- `anuncios` - Anuncios y noticias
- `tickets` - Tickets de soporte
- `ticket_comentarios` - Comentarios en tickets

### Tablas del Chatbot (`chatbot_schema.sql`)
- `chatbot_sessions` - Sesiones de conversación
- `chatbot_messages` - Mensajes (user, assistant, system, tool)
- `chatbot_actions` - Acciones ejecutadas por el chatbot

### Tablas de Cobranzas (`cobranzas_schema.sql`)
- `clientes` - Clientes con datos de crédito
- `facturas` - Facturas y saldos
- `pagos` - Historial de pagos
- `cobranza_seguimientos` - Seguimiento de cobranza

### Tablas ML/KDD (`ml_results_schema.sql`)
- `ml_modelos` - Modelos de machine learning
- `ml_ejecuciones` - Ejecuciones de modelos
- `ml_kdd_proceso` - Etapas del proceso KDD
- `ml_resultados_cliente` - Resultados por cliente
- `ml_metricas_modelo` - Métricas de rendimiento

### Tablas Power BI
- `powerbi_reports` - Reportes embebidos con filtros

## Roles de Usuario

| Rol | Permisos |
|-----|----------|
| `admin` | Acceso completo, CRUD usuarios, anuncios, estadísticas |
| `rrhh` | Gestión de vacaciones y empleados |
| `soporte` | Gestión de tickets |
| `empleado` | Acceso básico, solicitudes propias |

## Arquitectura del Chatbot

### Flujo de Conversación
1. Usuario envía mensaje → `/chatbot/chat` POST
2. Se obtiene/crea sesión de chatbot
3. Se carga historial de conversación
4. Se construye mensaje del sistema con contexto del usuario
5. Se envía al LLM con herramientas disponibles
6. Si hay `tool_calls`, se ejecutan y se continúa iterando
7. Se guarda respuesta y se retorna al usuario

### Herramientas del Chatbot (Function Calling)

Definidas en `modules/chatbot/tools.py`:

**Para todos los usuarios:**
- `get_employees_info` - Buscar empleados
- `get_departments_info` - Listar departamentos
- `get_documents_info` - Consultar documentos
- `get_my_vacations` - Ver mis vacaciones
- `get_my_tickets` - Ver mis tickets
- `get_announcements` - Ver anuncios
- `request_vacation` - Solicitar vacaciones
- `create_ticket` - Crear ticket de soporte
- `list_powerbi_reports` - Listar reportes Power BI
- `analyze_powerbi_report` - Analizar reporte con visión
- `get_powerbi_report_filters` - Obtener filtros de reporte

**Solo RRHH/Admin:**
- `get_all_vacations` - Ver todas las vacaciones
- `approve_vacation` - Aprobar vacaciones
- `reject_vacation` - Rechazar vacaciones

**Solo Soporte/Admin:**
- `get_all_tickets` - Ver todos los tickets
- `update_ticket_status` - Actualizar estado de ticket
- `assign_ticket` - Asignar ticket

**Solo Admin:**
- `create_user` - Crear usuario
- `create_announcement` - Crear anuncio
- `get_system_stats` - Estadísticas del sistema

**Cobranzas (admin, rrhh, soporte):**
- `buscar_cliente` - Buscar clientes
- `get_deuda_cliente` - Ver deuda de cliente
- `get_atraso_promedio_ponderado` - Calcular atraso ponderado
- `get_facturas_cliente` - Ver facturas
- `get_resumen_cliente` - Resumen completo
- `get_antiguedad_saldos` - Antigüedad de saldos
- `get_dashboard_cobranzas` - Métricas de cobranzas

### Configuración del LLM

Variables de entorno:
```env
LLM_API_KEY=<api_key>
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-5.1
LLM_MAX_TOKENS=4000
LLM_TEMPERATURE=0.3
LLM_VERBOSITY=medium          # Solo GPT-5.1
LLM_REASONING_EFFORT=medium   # Solo GPT-5.1
LLM_VISION_REASONING_EFFORT=low  # Para análisis de imágenes
```

## Convenciones de Código

### Python

- **Idioma**: Código y comentarios principalmente en español
- **Docstrings**: En español, formato simple
- **Imports**: stdlib → third-party → local
- **Nombres**:
  - Variables/funciones: `snake_case`
  - Clases: `PascalCase`
  - Constantes: `UPPER_SNAKE_CASE`

### Patrón de Modelos

Los modelos en `models.py` usan un patrón Active Record simplificado con métodos estáticos:

```python
class Entity:
    @staticmethod
    def get_all():
        query = "SELECT * FROM tabla WHERE activo = TRUE"
        return execute_query(query, fetch=True)

    @staticmethod
    def get_by_id(entity_id):
        query = "SELECT * FROM tabla WHERE id = %s"
        result = execute_query(query, (entity_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(campo1, campo2):
        query = "INSERT INTO tabla (campo1, campo2) VALUES (%s, %s)"
        return execute_query(query, (campo1, campo2))
```

### Patrón de Rutas (Blueprints)

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

modulo_bp = Blueprint('modulo', __name__, url_prefix='/modulo')

@modulo_bp.route('/')
@login_required
def index():
    """Descripción de la ruta"""
    # Lógica
    return render_template('modulo/index.html', datos=datos)
```

### Manejo de Errores

```python
try:
    # operación
    if not result:
        return {'success': False, 'error': 'Mensaje de error'}
    return {'success': True, 'data': result}
except Exception as e:
    return {'success': False, 'error': str(e)}
```

## Comandos de Desarrollo

### Setup Inicial

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Crear base de datos MySQL
mysql -u root -p
CREATE DATABASE intranet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Inicializar tablas y usuario admin
python init_db.py

# (Opcional) Inicializar chatbot
python create_chatbot_tables.py

# (Opcional) Datos de prueba de cobranzas
python seed_cobranzas_data.py
```

### Ejecutar la Aplicación

```bash
python app.py
# Servidor en http://127.0.0.1:5000
```

### Scripts de Utilidad

| Script | Descripción |
|--------|-------------|
| `init_db.py` | Crea tablas principales y usuario admin |
| `init_chatbot_db.py` | Inicializa tablas del chatbot |
| `create_chatbot_tables.py` | Crea tablas del chatbot |
| `seed_cobranzas_data.py` | Genera datos de prueba de cobranzas |
| `seed_ml_data.py` | Genera datos de prueba ML |
| `migrate_role_enum.py` | Migración del enum 'role' |
| `migrate_powerbi_filters.py` | Migración de filtros Power BI |
| `sincronizar_usuarios_empleados.py` | Sincroniza usuarios con empleados |

## Flujos de Trabajo Comunes

### Agregar un Nuevo Módulo

1. Crear directorio en `modules/nuevo_modulo/`
2. Crear `__init__.py` con Blueprint
3. Crear `routes.py` con rutas
4. Registrar Blueprint en `app.py`
5. Crear templates en `templates/nuevo_modulo/`
6. Agregar modelos en `models.py` si es necesario
7. Crear esquema SQL si hay nuevas tablas

### Agregar una Nueva Herramienta al Chatbot

1. En `modules/chatbot/tools.py`:
   - Crear método `_nueva_tool(self)` que retorna la definición OpenAI
   - Crear método `_execute_nueva_tool(self, args)` con la lógica
   - Agregar al mapeo en `execute_tool()`
   - Agregar a `get_available_tools()` según permisos

### Modificar Esquema de Base de Datos

1. Crear script de migración en `sql/migrations/`
2. Documentar cambios
3. Actualizar `models.py` si es necesario
4. Probar migración en desarrollo antes de producción

## Variables de Entorno Importantes

```env
# Base de datos (requerido)
DB_HOST=localhost
DB_USER=usuario
DB_PASSWORD=password
DB_NAME=intranet_db

# Admin inicial
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password_seguro
ADMIN_EMAIL=admin@empresa.com

# LLM/Chatbot (requerido para chatbot funcional)
LLM_API_KEY=sk-...
LLM_MODEL=gpt-5.1

# OAuth (opcional)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Seguridad
SECRET_KEY=clave-secreta-produccion
```

## Notas para AI Assistants

### Al Modificar Código

1. **Mantener el idioma**: Comentarios, mensajes de error y UI en español
2. **Seguir patrones existentes**: Revisar código similar antes de agregar nuevo
3. **Validar inputs**: Siempre validar datos de usuario antes de usar
4. **Manejar None**: Muchos métodos de modelos pueden retornar None
5. **Usar transacciones**: Para operaciones múltiples en BD

### Al Debuggear

- Los errores del chatbot se loguean en consola con `[DEBUG]`
- Errores de BD relacionados con 'role' tienen logging especial
- El chatbot tiene modo mock si no hay `LLM_API_KEY`

### Archivos Críticos No Modificar Sin Cuidado

- `database.py` - Afecta toda la aplicación
- `config.py` - Puede romper configuración
- `models.py` - Muchos módulos dependen de estos
- `modules/chatbot/tools.py` - Afecta capacidades del chatbot

### Testing

Actualmente no hay tests automatizados. Al agregar funcionalidad:
1. Probar manualmente el flujo completo
2. Verificar en diferentes roles de usuario
3. Probar con datos límite y errores

## Documentación Adicional

- `README.md` - Guía general del proyecto
- `OAUTH_SETUP.md` - Configuración de OAuth
- `POWERBI_VISION_README.md` - Integración de visión Power BI
- `docs/POWERBI_FILTERS_GUIDE.md` - Guía de filtros Power BI
