# Configuración de OAuth para Microsoft y Google

Este documento describe cómo configurar la autenticación OAuth con Microsoft (Azure AD) y Google para el portal de intranet.

## Requisitos previos

1. Ejecutar la migración de base de datos para añadir soporte OAuth:
```bash
mysql -u root -p mi_database < migration_oauth.sql
```

2. Instalar las dependencias necesarias:
```bash
pip install -r requirements.txt
```

## Configuración de Microsoft (Azure AD)

### 1. Crear una aplicación en Azure AD

1. Accede al [Portal de Azure](https://portal.azure.com)
2. Ve a **Azure Active Directory** > **App registrations** > **New registration**
3. Configura la aplicación:
   - **Name**: Portal Intranet
   - **Supported account types**: Selecciona según tu necesidad
     - "Accounts in this organizational directory only" - Solo tu organización
     - "Accounts in any organizational directory" - Cualquier organización
     - "Accounts in any organizational directory and personal Microsoft accounts" - Incluye cuentas personales
   - **Redirect URI**: Web - `http://localhost:5000/auth/microsoft/callback` (cambiar en producción)

### 2. Configurar permisos

1. Ve a **API permissions**
2. Añade los siguientes permisos de Microsoft Graph:
   - `User.Read` (tipo: Delegated)
   - `email` (tipo: Delegated)
   - `profile` (tipo: Delegated)
   - `openid` (tipo: Delegated)
3. Haz clic en **Grant admin consent** si es necesario

### 3. Crear Client Secret

1. Ve a **Certificates & secrets**
2. Haz clic en **New client secret**
3. Añade una descripción y selecciona la expiración
4. **IMPORTANTE**: Copia el valor del secreto inmediatamente (solo se muestra una vez)

### 4. Obtener IDs necesarios

En la página de **Overview** de tu aplicación, encontrarás:
- **Application (client) ID**: Tu Client ID
- **Directory (tenant) ID**: Tu Tenant ID

### 5. Configurar variables de entorno

Añade estas variables a tu archivo `.env`:

```bash
# Microsoft OAuth
MICROSOFT_CLIENT_ID=tu-client-id-aqui
MICROSOFT_CLIENT_SECRET=tu-client-secret-aqui
MICROSOFT_TENANT_ID=tu-tenant-id-aqui  # O "common" para multi-tenant
MICROSOFT_REDIRECT_URI=http://localhost:5000/auth/microsoft/callback
```

**Para producción**, cambia la REDIRECT_URI a tu dominio:
```bash
MICROSOFT_REDIRECT_URI=https://tudominio.com/auth/microsoft/callback
```

## Configuración de Google

### 1. Crear proyecto en Google Cloud Console

1. Accede a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google+ API** o **Google Identity API**

### 2. Crear credenciales OAuth 2.0

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **Create Credentials** > **OAuth client ID**
3. Si es necesario, configura la pantalla de consentimiento OAuth primero:
   - Ve a **OAuth consent screen**
   - Selecciona **Internal** (solo tu organización) o **External**
   - Completa la información requerida
   - Añade los scopes: `email`, `profile`, `openid`

4. Vuelve a **Credentials** y crea el OAuth client ID:
   - **Application type**: Web application
   - **Name**: Portal Intranet
   - **Authorized redirect URIs**: `http://localhost:5000/auth/google/callback`

5. Copia el **Client ID** y **Client Secret**

### 3. Configurar variables de entorno

Añade estas variables a tu archivo `.env`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id-aqui.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret-aqui
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

**Para producción**, cambia la REDIRECT_URI a tu dominio:
```bash
GOOGLE_REDIRECT_URI=https://tudominio.com/auth/google/callback
```

## Configuración de producción

### URLs de redirección

Cuando despliegues en producción, debes:

1. **Microsoft**: Añadir la URL de producción en Azure AD
   - Ve a tu app en Azure Portal
   - **Authentication** > **Platform configurations** > **Add URI**
   - Añade: `https://tudominio.com/auth/microsoft/callback`

2. **Google**: Añadir la URL de producción en Google Cloud Console
   - Ve a tus credenciales en Google Cloud Console
   - Edita el OAuth 2.0 Client ID
   - Añade a **Authorized redirect URIs**: `https://tudominio.com/auth/google/callback`

### HTTPS

En producción, **SIEMPRE** usa HTTPS. OAuth requiere conexiones seguras.

### Variables de entorno en producción

Actualiza tus variables de entorno en el servidor de producción:

```bash
MICROSOFT_REDIRECT_URI=https://tudominio.com/auth/microsoft/callback
GOOGLE_REDIRECT_URI=https://tudominio.com/auth/google/callback
```

## Uso

### Inicio de sesión

Los usuarios pueden iniciar sesión de tres formas:

1. **Usuario/Contraseña tradicional**: Para usuarios creados manualmente en el sistema
2. **Microsoft**: Haciendo clic en "Continuar con Microsoft"
3. **Google**: Haciendo clic en "Continuar con Google"

### Creación automática de usuarios

Cuando un usuario inicia sesión por primera vez con OAuth:
- Se crea automáticamente una cuenta en el sistema
- El rol por defecto es `empleado`
- El username se genera automáticamente desde el email
- No se requiere contraseña (solo para OAuth)

### Gestión de usuarios

Los administradores pueden:
- Ver todos los usuarios en `/auth/users`
- Activar/desactivar usuarios OAuth
- Los usuarios OAuth no pueden usar login tradicional
- Los usuarios tradicionales no pueden usar OAuth (a menos que se vincule manualmente)

## Seguridad

### CSRF Protection

El sistema incluye protección CSRF usando tokens de estado aleatorios (`state`) en cada flujo OAuth.

### Verificación de email

- **Microsoft**: Se confía en la verificación de Microsoft
- **Google**: Solo se aceptan emails verificados por Google

### Gestión de sesiones

Las sesiones OAuth funcionan igual que las sesiones tradicionales:
- Timeout de 1 hora
- Almacenamiento en filesystem
- Se puede ajustar en `config.py`

## Troubleshooting

### Error: "La autenticación con Microsoft/Google no está configurada"

**Solución**: Verifica que las variables de entorno estén correctamente configuradas en tu archivo `.env` y que la aplicación las esté cargando.

### Error: "redirect_uri_mismatch"

**Solución**: Asegúrate de que la URI de redirección en tu archivo `.env` coincida exactamente con la configurada en Azure/Google Cloud Console.

### Error: "Email no verificado" (Google)

**Solución**: El usuario debe verificar su email en Google antes de poder iniciar sesión.

### Usuario no puede iniciar sesión después de crear cuenta OAuth

**Solución**: Verifica que el usuario esté activo en la base de datos. Los administradores pueden activar usuarios desde `/auth/users`.

## Notas adicionales

### Dominios permitidos

Si quieres restringir qué dominios de email pueden registrarse:

1. Modifica `/modules/auth/routes.py`
2. En las funciones `microsoft_callback` y `google_callback`
3. Añade validación de dominio:

```python
allowed_domains = ['tuempresa.com', 'subsidiaria.com']
email_domain = email.split('@')[1]
if email_domain not in allowed_domains:
    flash('Tu dominio de email no está autorizado', 'danger')
    return redirect(url_for('auth.login'))
```

### Roles automáticos

Para asignar roles automáticamente basados en el dominio o grupo:

1. Modifica la función `create_oauth_user` en `models.py`
2. Añade lógica personalizada para determinar el rol

### Migración de usuarios existentes

Si tienes usuarios con email que quieres vincular a OAuth:

```sql
-- PRECAUCIÓN: Solo ejecutar después de confirmar que el email coincide
UPDATE usuarios
SET oauth_provider = 'microsoft',
    oauth_id = 'id-del-usuario-en-microsoft'
WHERE email = 'usuario@empresa.com';
```

## Soporte

Para más información:
- [Documentación de Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Documentación de Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
