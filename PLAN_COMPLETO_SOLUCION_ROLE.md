# 🎯 PLAN COMPLETO DE SOLUCIÓN - Error Role 1265

## 📋 Diagnóstico del Problema

**Bug identificado:** La columna `role` en la tabla `chatbot_messages` tiene un ENUM que **NO incluye el valor `'tool'`**.

### Evidencia de los Logs:

```
[ROLE_DEBUG] Role VÁLIDO: 'tool' - Procediendo a insertar en BD
[DATABASE_DEBUG]   Param[1]: 'tool' (tipo: str, len: 4, repr: 'tool')
Error al ejecutar query: 1265 (01000): Data truncated for column 'role' at row 1
```

El código Python valida correctamente que `'tool'` es válido, pero **MySQL lo rechaza** porque el ENUM de la columna no lo incluye.

---

## 🔧 SOLUCIÓN PASO A PASO

### PASO 1: Verificar el Schema Actual ✅

**Opción A: Desde MySQL Workbench/phpMyAdmin/CLI**

```sql
USE mi_database;

SELECT COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'mi_database'
  AND TABLE_NAME = 'chatbot_messages'
  AND COLUMN_NAME = 'role';
```

**Resultado esperado (con el problema):**
```
enum('user','assistant','system')
```

**Resultado esperado (después de la solución):**
```
enum('user','assistant','system','tool')
```

**Opción B: Ejecutar script de verificación SQL**

```bash
mysql -u root -p mi_database < verificar_schema_chatbot.sql
```

---

### PASO 2: Ejecutar la Migración 🔄

**Opción A: Script Python Automático (RECOMENDADO)**

1. Abre una terminal en el directorio del proyecto

2. Ejecuta el script de migración:
   ```bash
   python migrate_role_enum.py
   ```

3. El script te mostrará:
   - ✅ Schema actual
   - ⚠️  Si requiere migración
   - 🔄 Ejecutará la migración
   - ✅ Verificará que fue exitosa

4. Cuando pregunte "¿Deseas continuar con la migración? (s/n):", escribe `s` y presiona Enter

**Opción B: SQL Manual**

1. Conéctate a MySQL:
   ```bash
   mysql -u root -p
   ```

2. Ejecuta:
   ```sql
   USE mi_database;

   ALTER TABLE chatbot_messages
   MODIFY COLUMN role ENUM('user', 'assistant', 'system', 'tool') NOT NULL;
   ```

3. Verifica que funcionó:
   ```sql
   SELECT COLUMN_TYPE
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = 'mi_database'
     AND TABLE_NAME = 'chatbot_messages'
     AND COLUMN_NAME = 'role';
   ```

**Opción C: Ejecutar script SQL**

```bash
mysql -u root -p mi_database < fix_role_enum_add_tool.sql
```

---

### PASO 3: Verificar la Migración ✅

Después de ejecutar la migración, verifica que fue exitosa:

```sql
-- Debería retornar: enum('user','assistant','system','tool')
SHOW COLUMNS FROM chatbot_messages LIKE 'role';

-- Probar insertar un mensaje con role='tool' (debería funcionar)
INSERT INTO chatbot_messages (session_id, role, content)
VALUES (1, 'tool', 'Test message with tool role')
ON DUPLICATE KEY UPDATE content = 'Test message with tool role';
```

Si NO hay errores, ✅ **la migración fue exitosa**.

---

### PASO 4: Probar el Flujo Completo 🧪

1. **Si el servidor Flask está corriendo, reinícialo:**
   - Presiona `Ctrl + C` en la terminal del servidor
   - Ejecuta: `python app.py`

2. **Prueba el análisis de Power BI:**
   - Ve al módulo KPIs
   - En el chatbot, escribe: `"Analiza el reporte Creando nuevos reportes"`

3. **Verifica que NO aparezca el error:**
   - ❌ Antes: `Error al ejecutar query: 1265`
   - ✅ Después: `[ROLE_DEBUG] ✅ Mensaje insertado exitosamente con ID: XXX`

4. **Verifica que el análisis funcione completamente:**
   - ✅ Screenshot capturado
   - ✅ Análisis de visión completado
   - ✅ Respuesta del chatbot entregada

---

### PASO 5: Limpiar Logging de Debug (OPCIONAL) 🧹

Una vez que verifiques que todo funciona, puedes limpiar el logging temporal:

**Archivos a editar:**

1. **modules/chatbot/models.py** - Eliminar logs `[ROLE_DEBUG]`:
   - Líneas 147-179: Eliminar los `logger.info()` de debug
   - Líneas 205-211: Eliminar los logs de parámetros
   - Líneas 219, 223-228: Eliminar logs de éxito/error (o dejarlos si son útiles)

2. **database.py** - Eliminar logs `[DATABASE_DEBUG]`:
   - Líneas 57-68: Eliminar el bloque de logging de debug

**O mantén los logs si quieres monitorear el sistema.**

---

## 📊 Antes vs Después

### ANTES (Con Error):

```
Schema BD:  role ENUM('user', 'assistant', 'system')
             ↓
Código Python intenta insertar: role='tool'
             ↓
❌ MySQL rechaza: "Data truncated for column 'role'"
```

### DESPUÉS (Corregido):

```
Schema BD:  role ENUM('user', 'assistant', 'system', 'tool')
             ↓
Código Python inserta: role='tool'
             ↓
✅ MySQL acepta: Mensaje insertado exitosamente
```

---

## 🗂️ Archivos Creados

1. ✅ **verificar_schema_chatbot.sql** - Script para verificar schema actual
2. ✅ **fix_role_enum_add_tool.sql** - Script SQL para ejecutar migración
3. ✅ **migrate_role_enum.py** - Script Python automático para migración
4. ✅ **PLAN_COMPLETO_SOLUCION_ROLE.md** - Este documento

---

## ⚠️ IMPORTANTE - Ejecución de la Migración

### Método Recomendado: Script Python

```bash
python migrate_role_enum.py
```

**Ventajas:**
- ✅ Verifica automáticamente el schema actual
- ✅ Detecta si la migración es necesaria
- ✅ Pide confirmación antes de ejecutar
- ✅ Verifica que la migración fue exitosa
- ✅ Maneja errores automáticamente

### Método Alternativo: SQL Manual

```sql
ALTER TABLE chatbot_messages
MODIFY COLUMN role ENUM('user', 'assistant', 'system', 'tool') NOT NULL;
```

---

## ✅ Checklist de Verificación

Después de ejecutar la migración, verifica:

- [ ] El schema de la columna `role` incluye `'tool'`
- [ ] Puedes insertar un registro con `role='tool'` manualmente
- [ ] El servidor Flask se reinició (si estaba corriendo)
- [ ] El análisis de Power BI funciona sin errores
- [ ] Los mensajes se insertan correctamente en BD
- [ ] No hay errores MySQL 1265 en la consola

---

## 🚀 Resultado Esperado

Después de completar todos los pasos:

1. ✅ La columna `role` acepta los valores: `'user'`, `'assistant'`, `'system'`, `'tool'`
2. ✅ El análisis de visión de Power BI funciona completamente
3. ✅ No hay errores MySQL 1265
4. ✅ Los mensajes del chatbot se guardan correctamente en BD

---

## 📞 Si el Problema Persiste

Si después de ejecutar la migración el error continúa:

1. **Verifica que el schema se actualizó:**
   ```sql
   SHOW COLUMNS FROM chatbot_messages LIKE 'role';
   ```

2. **Verifica que reiniciaste el servidor Flask**

3. **Revisa los logs `[ROLE_DEBUG]` para ver qué role está fallando**

4. **Envíame los logs completos** para investigar más

---

**Fecha:** 2025-11-22
**Problema:** MySQL Error 1265 - "Data truncated for column 'role'"
**Causa:** ENUM de la columna `role` no incluía `'tool'`
**Solución:** Migración del schema de BD para agregar `'tool'` al ENUM
