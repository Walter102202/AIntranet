# AIntranet - Roadmap de Mejoras para Intranet Profesional

> Análisis completo del repositorio realizado el 2026-02-20.
> Calificación general actual: **4/10** — Funcionalidad rica, pero requiere maduración significativa para producción.

---

## Resumen Ejecutivo

AIntranet es un portal de intranet corporativo con buena cobertura funcional (8 módulos, chatbot con IA, integración Power BI, módulo de cobranzas con ML). Sin embargo, presenta deficiencias críticas en seguridad, infraestructura de despliegue, testing y rendimiento que impiden su uso en producción empresarial.

### Calificación por Área

| Área | Puntuación | Estado |
|------|-----------|--------|
| Funcionalidad | 8/10 | Cobertura completa de módulos |
| Calidad de Código | 5/10 | Necesita refactorización |
| Seguridad | 4/10 | Vulnerabilidades múltiples |
| Testing | 2/10 | Cobertura mínima (<5%) |
| Documentación | 7/10 | Buena, en español |
| Rendimiento | 3/10 | Queries sin optimizar |
| Despliegue | 2/10 | No listo para producción |
| Accesibilidad | 1/10 | No abordada |
| Frontend/UX | 6.5/10 | Funcional, mejoras necesarias |

---

## FASE 1: Seguridad Crítica (Prioridad Máxima)

### 1.1 Protección CSRF en formularios
- **Severidad**: CRITICA
- **Impacto**: Todas las rutas POST (15+ endpoints) carecen de tokens CSRF
- **Archivos afectados**: Todos los templates con formularios POST
- **Acción**: Implementar Flask-WTF con middleware CSRF global
- **Detalle**: Un atacante puede forzar a usuarios autenticados a ejecutar acciones no deseadas (aprobar vacaciones, crear tickets, crear usuarios)

### 1.2 Eliminar modo debug en producción
- **Severidad**: CRITICA
- **Ubicación**: `app.py:157` — `app.run(debug=True, host='0.0.0.0', port=5000)`
- **Riesgo**: Expone debugger interactivo, código fuente y permite ejecución arbitraria de código
- **Acción**: Configurar `debug=False` para producción, usar variable de entorno

### 1.3 Eliminar SECRET_KEY hardcodeada
- **Severidad**: CRITICA
- **Ubicación**: `config.py:6` — fallback a `'dev-secret-key-change-in-production'`
- **Riesgo**: Si .env no está configurado, tokens de sesión son predecibles
- **Acción**: Remover fallback, requerir configuración explícita en .env, lanzar excepción si falta

### 1.4 Configuración segura de sesiones
- **Severidad**: CRITICA
- **Ubicación**: `config.py:17-21`
- **Problemas**:
  - `SESSION_COOKIE_SECURE = False` — cookies transmitidas en texto plano
  - `SESSION_TYPE = 'filesystem'` — datos de sesión sin cifrar en disco
  - `PERMANENT_SESSION_LIFETIME = 30 días` — ventana muy amplia para secuestro de sesión
- **Acción**: `SESSION_COOKIE_SECURE = True`, usar Redis para sesiones, reducir lifetime a 8 horas

### 1.5 Vulnerabilidad XSS en chatbot
- **Severidad**: CRITICA
- **Ubicación**: `static/js/chatbot.js:239-242` — mensajes renderizados con `innerHTML` sin sanitización
- **Riesgo**: Ejecución arbitraria de JavaScript a través de mensajes maliciosos
- **Acción**: Usar `textContent` o implementar DOMPurify

### 1.6 Política de contraseñas débil
- **Severidad**: CRITICA
- **Ubicación**: `modules/auth/routes.py:121, 185` — mínimo 6 caracteres sin complejidad
- **Acción**: Implementar mínimo 12 caracteres con requisitos de complejidad (mayúsculas, minúsculas, números, símbolos)

### 1.7 Headers de seguridad faltantes
- **Severidad**: ALTA
- **Faltantes**: `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy`
- **Acción**: Agregar middleware Flask para inyectar headers de seguridad

### 1.8 Rate limiting inexistente
- **Severidad**: ALTA
- **Riesgo**: Login vulnerable a fuerza bruta, endpoint de chatbot vulnerable a DoS
- **Acción**: Implementar Flask-Limiter (ej. 5 intentos fallidos = bloqueo 15 min)

### 1.9 Validación de archivos subidos incompleta
- **Severidad**: ALTA
- **Ubicación**: `modules/documents/routes.py:48-50`
- **Problema**: Solo verifica extensión, no tipo MIME real; sin antivirus
- **Acción**: Validar tipo MIME, generar nombres únicos con UUID, escanear archivos

### 1.10 Verificación de email OAuth incompleta
- **Severidad**: ALTA
- **Ubicación**: `modules/auth/routes.py:320-350` — Microsoft OAuth no verifica campo `email_verified`
- **Acción**: Agregar verificación de email como la implementación de Google (línea 471)

---

## FASE 2: Infraestructura y Backend (Prioridad Alta)

### 2.1 Connection pooling de base de datos
- **Severidad**: CRITICA para escalabilidad
- **Ubicación**: `database.py` — crea conexión nueva por CADA query
- **Impacto**: Agotamiento de recursos con 50+ usuarios
- **Acción**: Implementar SQLAlchemy con connection pooling o configurar pool en mysql-connector

### 2.2 Configuración de despliegue
- **Estado actual**: INEXISTENTE
- **Faltantes**:
  - [ ] Dockerfile y docker-compose.yml
  - [ ] Configuración nginx como reverse proxy
  - [ ] Configuración gunicorn/uWSGI como servidor WSGI
  - [ ] Archivos de servicio systemd
  - [ ] Endpoint de health check (`/health`)
  - [ ] Configuraciones por ambiente (dev/staging/prod)
- **Acción**: Crear infraestructura completa de despliegue

### 2.3 Sistema de migraciones de base de datos
- **Estado actual**: 7+ scripts manuales sin versionado
- **Problema**: No hay tracking de versiones, no hay rollback, esquema disperso en múltiples .sql
- **Scripts duplicados**: `init_chatbot_db.py` y `create_chatbot_tables.py` parecen duplicados
- **Acción**: Implementar Alembic para migraciones versionadas y controladas

### 2.4 Logging centralizado
- **Estado actual**: Inconsistente — 6/30+ archivos usan logging, el resto usa `print()`
- **Problemas**:
  - Código debug en producción: `database.py:58-68` imprime queries y parámetros
  - `chatbot/models.py:152-229` tiene logs `[ROLE_DEBUG]`
  - Información sensible potencialmente expuesta en logs
- **Acción**: Configurar logging centralizado con niveles apropiados, eliminar código debug

### 2.5 Sistema de caché
- **Estado actual**: INEXISTENTE
- **Oportunidades**:
  - Dashboard hace 5+ queries por carga de página para datos estáticos
  - Directorio de empleados se consulta completo en cada request
  - Screenshots de Power BI nunca se cachean
- **Acción**: Implementar Redis con Flask-Caching (TTL 5 min para datos semi-estáticos)

### 2.6 Cola de tareas en background
- **Estado actual**: INEXISTENTE
- **Operaciones bloqueantes identificadas**:
  - Screenshots PowerBI: 8 segundos de `page.wait_for_timeout()` bloqueando HTTP
  - Ejecución de modelos ML: tablas existen pero no hay scheduler
  - Sincronización de datos: script manual sin automatización
- **Acción**: Implementar Celery o APScheduler para jobs asíncronos

### 2.7 Sistema de notificaciones por email
- **Estado actual**: INEXISTENTE
- **Notificaciones faltantes**:
  - [ ] Aprobación/rechazo de vacaciones
  - [ ] Confirmación de creación de tickets
  - [ ] Broadcast de anuncios
  - [ ] Resultados de acciones del chatbot
  - [ ] Alertas de administrador
- **Acción**: Implementar Flask-Mail con templates de email

### 2.8 Validación de inputs en servidor
- **Estado actual**: Mínima — solo verificaciones básicas
- **Problemas**:
  - Sin validación de formato de email
  - Sin límites de longitud de campos
  - Parámetros del chatbot sin validar antes de ejecución
- **Acción**: Implementar Marshmallow o Pydantic para validación de esquemas

### 2.9 Audit logging
- **Estado actual**: INEXISTENTE
- **Requerimiento**: Registro de todas las acciones sensibles con timestamp, usuario y detalle
- **Acciones a auditar**: Login/logout, creación/modificación de usuarios, aprobación de vacaciones, acciones del chatbot, cambios de estado de tickets
- **Acción**: Crear tabla `audit_log` e implementar decorador de auditoría

### 2.10 Mecanismo de reset de contraseña
- **Estado actual**: INEXISTENTE — requiere intervención del admin
- **Riesgo**: Bloqueo de usuarios, mala experiencia
- **Acción**: Implementar flujo self-service con verificación por email

---

## FASE 3: Calidad de Código y Testing (Prioridad Media-Alta)

### 3.1 Tests automatizados
- **Estado actual**: 2 archivos de test (~60 líneas), cobertura <5%
- **Objetivo**: 70%+ de cobertura
- **Acciones**:
  - [ ] Configurar pytest con fixtures para Flask app y BD
  - [ ] Tests unitarios para todos los modelos (models.py — 1,243 líneas)
  - [ ] Tests de integración para todas las rutas
  - [ ] Tests de API para endpoints del chatbot
  - [ ] Tests de seguridad (CSRF, autenticación, autorización)
  - [ ] Tests de rendimiento básicos
  - [ ] Configurar CI/CD pipeline

### 3.2 Refactorización de modelos
- **Problema**: `models.py` tiene 1,243 líneas en un solo archivo
- **Acción**: Separar en módulos por dominio:
  - `models/auth.py` — User, Department
  - `models/tickets.py` — Ticket, TicketComment
  - `models/vacations.py` — Vacation
  - `models/documents.py` — Document
  - `models/announcements.py` — Announcement
  - `models/cobranzas.py` — Cliente, Factura, Pago
  - `models/chatbot.py` — ChatbotSession, ChatbotMessage
  - `models/powerbi.py` — PowerBIReport

### 3.3 Eliminación de duplicación de código
- **Estimación**: 15-20% del código está duplicado
- **Hotspots**:
  - Verificaciones de permisos: `if session.get('rol') not in [...]` aparece 50+ veces
  - Callbacks OAuth: implementaciones Microsoft/Google 70% idénticas
  - Patrones de modelo: lógica query-execute-fetch repetida
  - Mensajes flash: templates repetidos verbatim
- **Acción**: Crear decorador `@requires_role()`, abstraer patrones comunes

### 3.4 Type hints
- **Estado actual**: Ausentes en todo el código
- **Acción**: Agregar anotaciones de tipo a todas las funciones (Python 3.8+ lo soporta)

### 3.5 Consistencia en respuestas API
- **Estado actual**: Chatbot usa formato estructurado, resto inconsistente
- **Acción**: Estandarizar formato de respuesta JSON para todos los endpoints API

### 3.6 Paginación de datos
- **Estado actual**: Métodos `get_all()` cargan todos los registros sin límite
- **Riesgo**: Degradación de rendimiento con datos crecientes
- **Acción**: Implementar paginación en modelos y rutas (LIMIT/OFFSET o cursor-based)

### 3.7 Linting y formateo
- **Estado actual**: Sin configuración de linting
- **Acción**: Configurar flake8/ruff + black/isort, agregar pre-commit hooks

---

## FASE 4: Frontend y UX (Prioridad Media)

### 4.1 Accesibilidad (WCAG 2.1 AA)
- **Estado actual**: Cumplimiento parcial — semántica HTML presente pero incompleta
- **Faltantes**:
  - [ ] Atributos `alt` en imágenes de empleados
  - [ ] Links "saltar al contenido" (skip-to-content)
  - [ ] Gestión de foco en modales
  - [ ] Navegación por teclado documentada
  - [ ] Descripciones ARIA en iconos
  - [ ] Títulos de página únicos
- **Acción**: Auditoría con axe DevTools/WAVE, corregir issues

### 4.2 Optimización de rendimiento frontend
- **Problemas identificados**:
  - CSS/JS custom servidos sin minificar (~43 KB total)
  - Sin estrategia de caché de assets (sin versioning)
  - Sin lazy loading de imágenes
  - Búsqueda en tablas sin debouncing
  - Sin preconnect/prefetch a CDNs
- **Acciones**:
  - [ ] Minificar CSS/JS
  - [ ] Agregar versionamiento de assets (`?v=hash`)
  - [ ] Implementar compresión gzip
  - [ ] Agregar debouncing a eventos de búsqueda/scroll
  - [ ] Implementar lazy loading para imágenes

### 4.3 Soporte para modo oscuro (dark mode)
- **Estado actual**: No implementado
- **Acción**: Implementar con CSS custom properties y `prefers-color-scheme` media query, toggle manual con persistencia en localStorage

### 4.4 Mejoras de navegación
- **Faltantes**:
  - [ ] Breadcrumbs en páginas de detalle
  - [ ] Indicador de estado "activo" en página actual
  - [ ] Búsqueda global
  - [ ] Navegación consistente con botón "atrás"
- **Acción**: Implementar componentes de navegación reutilizables

### 4.5 Mejoras responsive para tablet
- **Estado actual**: Solo 1 breakpoint (768px), sin optimizaciones tablet
- **Acción**: Agregar breakpoints intermedios, optimizar layouts de tabla para tablet

### 4.6 Estados de carga y feedback
- **Faltantes**:
  - [ ] Manejo de timeout para respuestas lentas de API
  - [ ] Mecanismo de reintento para requests fallidos
  - [ ] Detección de modo offline
  - [ ] Degradación graceful si JavaScript está deshabilitado
- **Acción**: Implementar patrones de loading/error/retry consistentes

### 4.7 Funcionalidad de descarga de documentos
- **Severidad**: MEDIA — Feature core incompleta
- **Ubicación**: `modules/documents/routes.py` — endpoint `/documents/download/<id>` solo incrementa contador, no descarga
- **Acción**: Completar implementación con serving de archivos y control de acceso

---

## FASE 5: Funcionalidades Profesionales (Prioridad Media-Baja)

### 5.1 Internacionalización (i18n)
- **Estado actual**: Todo hardcodeado en español, `lang="es"` fijo
- **Acción**: Extraer strings, implementar i18next o Flask-Babel, crear estructura de archivos de traducción

### 5.2 Versionado de documentos
- **Estado actual**: Sin historial de versiones
- **Acción**: Implementar sistema de versionado para documentos subidos

### 5.3 Exportación de reportes
- **Estado actual**: Sin capacidad de exportación
- **Acción**: Agregar exportación a CSV/Excel/PDF para tickets, vacaciones, cobranzas

### 5.4 Integración con Slack/Teams
- **Estado actual**: Sin integraciones externas de comunicación
- **Acción**: Webhooks para notificaciones en canales de equipo

### 5.5 Sincronización de calendario
- **Estado actual**: Sin integración con calendarios
- **Acción**: Exportar vacaciones/eventos como .ics, integración con Google Calendar/Outlook

### 5.6 Importación masiva de usuarios
- **Estado actual**: Creación individual únicamente
- **Acción**: Implementar importación desde CSV/Excel con validación

### 5.7 Dashboard de métricas de uso
- **Estado actual**: Estadísticas básicas solo para admin
- **Acción**: Dashboard con analytics de uso por módulo, actividad de usuarios, métricas del chatbot

### 5.8 Sistema de workflows avanzados
- **Estado actual**: Flujos básicos (solicitar → aprobar/rechazar)
- **Acción**: Motor de workflows configurable con múltiples aprobadores, escalaciones, SLAs

### 5.9 Exportación de datos GDPR
- **Estado actual**: Sin soporte
- **Acción**: Endpoint para que usuarios exporten todos sus datos personales

### 5.10 Tracking de costos del chatbot
- **Estado actual**: Sin tracking de consumo de API LLM
- **Acción**: Registrar tokens consumidos por sesión/usuario, dashboard de costos

---

## FASE 6: DevOps y Operaciones (Prioridad Baja)

### 6.1 CI/CD Pipeline
- **Estado actual**: Sin pipeline visible
- **Acción**: Configurar GitHub Actions con lint, test, build, deploy

### 6.2 Monitoreo y alertas
- **Estado actual**: Sin monitoreo
- **Acción**: Integrar Sentry para errores, métricas de aplicación (Prometheus/Grafana)

### 6.3 Backup y restauración de BD
- **Estado actual**: Sin estrategia
- **Acción**: Configurar backups automáticos con mysqldump, UI de restauración para admin

### 6.4 Documentación de API
- **Estado actual**: Sin documentación de endpoints
- **Acción**: Implementar Swagger/OpenAPI para todos los endpoints

### 6.5 Load testing
- **Estado actual**: Sin pruebas de carga
- **Acción**: Configurar Locust o similar para probar con 100+ usuarios concurrentes

---

## Matriz de Riesgo Actual

| Riesgo | Severidad | Probabilidad | Estado |
|--------|----------|-------------|--------|
| CSRF en formularios | CRITICA | ALTA | Sin mitigar |
| Debug mode en producción | CRITICA | MEDIA | Sin mitigar |
| SECRET_KEY predecible | CRITICA | MEDIA | Sin mitigar |
| XSS en chatbot | CRITICA | MEDIA | Sin mitigar |
| Sin connection pooling | ALTA | ALTA | Sin mitigar |
| Sin rate limiting | ALTA | MEDIA | Sin mitigar |
| Contraseñas débiles | ALTA | ALTA | Sin mitigar |
| Upload sin validación MIME | ALTA | MEDIA | Sin mitigar |
| Sin audit logging | MEDIA | ALTA | Sin mitigar |
| Sin paginación | MEDIA | MEDIA | Sin mitigar |
| Sin caché | MEDIA | MEDIA | Sin mitigar |
| Sin notificaciones email | BAJA | BAJA | Sin implementar |

---

## Aspectos Positivos Existentes

Estos elementos ya están bien implementados y deben mantenerse:

1. **Protección contra SQL injection**: Queries parametrizadas en toda la aplicación
2. **Hashing de contraseñas**: Werkzeug PBKDF2 con salt
3. **Organización modular**: Blueprints Flask bien separados
4. **Arquitectura del chatbot**: Ejecución iterativa de herramientas, gestión de sesiones, permisos por rol
5. **Integración Power BI**: Servicio de screenshots con filtros y optimización de imágenes
6. **Esquema de BD**: Bien diseñado con vistas, índices apropiados y dominio financiero complejo
7. **OAuth 2.0**: Implementado con parámetro state para CSRF
8. **Cookies HttpOnly**: `SESSION_COOKIE_HTTPONLY = True` previene robo via XSS
9. **Documentación**: README, CLAUDE.md, guías de OAuth y Power BI

---

## Dependencias Recomendadas a Agregar

| Paquete | Propósito | Fase |
|---------|-----------|------|
| `Flask-WTF` | Protección CSRF | 1 |
| `Flask-Limiter` | Rate limiting | 1 |
| `DOMPurify` (JS CDN) | Sanitización XSS | 1 |
| `SQLAlchemy` | ORM + connection pooling | 2 |
| `Alembic` | Migraciones de BD | 2 |
| `Flask-Caching` + `Redis` | Caché | 2 |
| `Celery` | Cola de tareas | 2 |
| `Flask-Mail` | Notificaciones email | 2 |
| `Marshmallow` o `Pydantic` | Validación de inputs | 2 |
| `gunicorn` | Servidor WSGI producción | 2 |
| `pytest` + `pytest-flask` | Testing | 3 |
| `ruff` o `flake8` | Linting | 3 |
| `Sentry SDK` | Monitoreo de errores | 6 |

---

## Archivos Críticos de Referencia

| Archivo | Líneas | Issues | Prioridad |
|---------|--------|--------|-----------|
| `config.py` | 45 | SECRET_KEY insegura, sesión insegura | CRITICA |
| `app.py` | 157 | Debug mode, host 0.0.0.0 | CRITICA |
| `database.py` | 94 | Sin pooling, debug code, logging sensible | CRITICA |
| `modules/auth/routes.py` | 450+ | Contraseñas débiles, sin rate limit, OAuth incompleto | ALTA |
| `modules/documents/routes.py` | ~100 | Sin validación MIME, descarga no implementada | ALTA |
| `models.py` | 1,243 | Archivo monolítico, sin validación, sin paginación | MEDIA |
| `static/js/chatbot.js` | 435 | Vulnerabilidad XSS via innerHTML | CRITICA |
| Todos los templates HTML | ~26 | Sin tokens CSRF | CRITICA |

---

*Este documento debe revisarse y actualizarse conforme se completen las mejoras.*
