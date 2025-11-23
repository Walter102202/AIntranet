-- ============================================================
-- SCRIPT 1: VERIFICAR EL SCHEMA ACTUAL DE chatbot_messages
-- ============================================================
-- Ejecuta este script primero para ver el problema
-- ============================================================

USE mi_database;

-- Ver la definición completa de la tabla
SHOW CREATE TABLE chatbot_messages;

-- Ver específicamente la columna role
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'mi_database'
  AND TABLE_NAME = 'chatbot_messages'
  AND COLUMN_NAME = 'role';

-- Resultado esperado si NO tiene 'tool':
-- COLUMN_TYPE: enum('user','assistant','system')
--
-- Resultado esperado si SÍ tiene 'tool':
-- COLUMN_TYPE: enum('user','assistant','system','tool')
