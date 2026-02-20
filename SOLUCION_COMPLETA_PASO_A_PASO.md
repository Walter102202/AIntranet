# ✅ SOLUCIÓN COMPLETA - Error MySQL 1265 "Data truncated for column 'role'"

## 🎯 Problema Identificado

La columna `role` en la tabla `chatbot_messages` tiene un ENUM que **NO incluye el valor `'tool'`**, causando el error:

```
Error al ejecutar query: 1265 (01000): Data truncated for column 'role' at row 1
```

---

## 📋 PASOS PARA SOLUCIONAR

### PASO 1: Verificar Conexión a MySQL ✅

**Ejecuta este comando primero:**

```bash
python test_db_connection.py
```

**Resultado esperado (✅ ÉXITO):**

```
✅ ¡CONEXIÓN EXITOSA!
   Versión de MySQL Server: 8.x.x
   Conectado a la base de datos: mi_database
   ✅ Tabla 'chatbot_messages' encontrada
   📊 Schema de columna 'role': enum('user','assistant','system')
   ⚠️  La columna 'role' NO incluye 'tool'
```

**Si ves esto ✅**, continúa al PASO 2.

**Si hay error de conexión ❌:**

1. Verifica que MySQL esté corriendo
2. Verifica que el archivo `.env` tenga las credenciales correctas:
   ```
   DB_HOST=localhost
   DB_USER=walter_local
   DB_PASSWORD=Milton3007%
   DB_NAME=mi_database
   ```
3. Verifica que `python-dotenv` esté instalado:
   ```bash
   pip install python-dotenv
   ```

---

### PASO 2: Ejecutar Migración del Schema ⚡

**Ejecuta el script de migración:**

```bash
python migrate_role_enum.py
```

**El script te mostrará:**

```
PASO 1: Verificando schema actual de chatbot_messages.role
✅ Schema actual de la columna 'role':
   enum('user','assistant','system')

⚠️  El ENUM NO incluye 'tool'. Se requiere migración.

¿Deseas continuar con la migración? (s/n):
```

**Escribe `s` y presiona Enter.**

**Resultado esperado:**

```
PASO 2: Ejecutando migración - Agregando 'tool' al ENUM
✅ Migración ejecutada exitosamente!

PASO 3: Verificando que la migración fue exitosa
✅ MIGRACIÓN EXITOSA!
   La columna 'role' ahora incluye 'tool' en el ENUM
```

---

### PASO 3: Verificar que la Migración Funcionó ✅

**Ejecuta el script de prueba:**

```bash
python test_tool_role.py
```

**Resultado esperado (✅ ÉXITO):**

```
Creando sesión de prueba...
✅ Sesión creada/obtenida: ID 18

Intentando insertar mensaje con role='tool'...
✅ ¡ÉXITO! Mensaje con role='tool' insertado con ID: 144

============================================================
✅ LA MIGRACIÓN FUE EXITOSA
============================================================

El role='tool' ahora funciona correctamente en la BD.
Puedes proceder a probar el análisis de Power BI.
```

**Si ves este mensaje ✅**, la migración fue exitosa. Continúa al PASO 4.

---

### PASO 4: Reiniciar el Servidor Flask 🔄

**Si el servidor Flask está corriendo:**

1. Presiona `Ctrl + C` en la terminal del servidor
2. Reinicia el servidor:
   ```bash
   python app.py
   ```

---

### PASO 5: Probar el Análisis de Power BI 🧪

1. **Accede a la intranet** en tu navegador
2. **Ve al módulo de KPIs** con el chatbot
3. **Envía el mensaje:**
   ```
   Analiza el reporte "Creando nuevos reportes"
   ```

**Resultado esperado (✅ ÉXITO):**

En la consola del servidor Flask verás:

```
[ROLE_DEBUG] Role VÁLIDO: 'tool' - Procediendo a insertar en BD
[ROLE_DEBUG] ✅ Mensaje insertado exitosamente con ID: XXX
INFO:modules.chatbot.screenshot_service: Screenshot capturado exitosamente
INFO:modules.chatbot.tools: Análisis de visión completado exitosamente
```

**Y en el chatbot:**
- ✅ El screenshot se captura correctamente
- ✅ El análisis de visión se completa
- ✅ La respuesta del chatbot aparece correctamente
- ✅ **NO hay error MySQL 1265**

---

## 🔍 Verificación Final

**Consulta SQL para verificar el schema:**

```sql
USE mi_database;

SELECT COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'mi_database'
  AND TABLE_NAME = 'chatbot_messages'
  AND COLUMN_NAME = 'role';
```

**Resultado esperado:**
```
enum('user','assistant','system','tool')
```

---

## 📂 Scripts Creados y Corregidos

1. ✅ **test_db_connection.py** - Verifica conexión a MySQL con credenciales del .env
2. ✅ **migrate_role_enum.py** - Ejecuta la migración automáticamente (CORREGIDO)
3. ✅ **test_tool_role.py** - Verifica que role='tool' funciona (CORREGIDO)
4. ✅ **fix_role_enum_add_tool.sql** - Script SQL manual alternativo
5. ✅ **verificar_schema_chatbot.sql** - Verifica el schema actual

**Todos los scripts ahora cargan correctamente el `.env` con `load_dotenv()`**

---

## ⚠️ Solución al Problema de Credenciales

**Problema anterior:**
```
Error al conectar a MySQL: 1045 (28000): Access denied for user 'root'@'localhost'
```

**Causa:**
Los scripts NO estaban cargando el archivo `.env`, por lo que intentaban usar las credenciales por defecto (root sin password).

**Solución aplicada:**
Todos los scripts ahora incluyen al inicio:

```python
from dotenv import load_dotenv
load_dotenv()
```

Esto carga las credenciales del `.env` ANTES de importar `Config`.

---

## 🚀 Resumen de Ejecución Rápida

```bash
# 1. Verificar conexión
python test_db_connection.py

# 2. Ejecutar migración (escribe 's' cuando pregunte)
python migrate_role_enum.py

# 3. Verificar que funcionó
python test_tool_role.py

# 4. Reiniciar Flask y probar
python app.py
```

---

## ✅ Checklist de Verificación

- [ ] `python test_db_connection.py` - Conexión exitosa ✅
- [ ] `python migrate_role_enum.py` - Migración exitosa ✅
- [ ] `python test_tool_role.py` - Inserción de role='tool' exitosa ✅
- [ ] Servidor Flask reiniciado
- [ ] Análisis de Power BI funciona sin errores
- [ ] NO aparece el error MySQL 1265

---

## 📞 Si Algo Sale Mal

**Error de conexión a MySQL:**
- Verifica que MySQL esté corriendo
- Verifica las credenciales en el `.env`
- Verifica que `python-dotenv` esté instalado: `pip install python-dotenv`

**La migración falla:**
- Verifica que tienes permisos para modificar la tabla
- Ejecuta el SQL manual: `mysql -u walter_local -p mi_database < fix_role_enum_add_tool.sql`

**El error 1265 persiste después de la migración:**
- Verifica el schema: `SHOW COLUMNS FROM chatbot_messages LIKE 'role';`
- Verifica que reiniciaste el servidor Flask
- Envíame los logs completos de `[ROLE_DEBUG]`

---

**Fecha de corrección:** 2025-11-22
**Problema:** MySQL Error 1265 + Error de credenciales
**Causa:** ENUM sin 'tool' + Scripts sin cargar .env
**Solución:** Migración de schema + Corrección de carga de credenciales
**Estado:** ✅ Listo para ejecutar
