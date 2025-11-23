-- ============================================================
-- SCRIPT 2: MIGRACIÓN - AGREGAR 'tool' AL ENUM DE role
-- ============================================================
-- Este script actualiza la columna role para incluir 'tool'
-- Es SEGURO ejecutarlo incluso si 'tool' ya existe
-- ============================================================

USE mi_database;

-- OPCIÓN A: ALTER TABLE (recomendado, más rápido)
-- Modifica el ENUM para incluir 'tool'
ALTER TABLE chatbot_messages
MODIFY COLUMN role ENUM('user', 'assistant', 'system', 'tool') NOT NULL;

-- Verificar que el cambio se aplicó correctamente
SELECT
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'mi_database'
  AND TABLE_NAME = 'chatbot_messages'
  AND COLUMN_NAME = 'role';

-- Resultado esperado después de la migración:
-- COLUMN_TYPE: enum('user','assistant','system','tool')

-- ============================================================
-- VERIFICACIÓN ADICIONAL
-- ============================================================

-- Contar mensajes actuales por role (antes de la migración no debería haber 'tool')
SELECT role, COUNT(*) as total
FROM chatbot_messages
GROUP BY role
ORDER BY role;

-- Esta query debería funcionar DESPUÉS de ejecutar el ALTER TABLE
-- INSERT INTO chatbot_messages (session_id, role, content)
-- VALUES (1, 'tool', 'Test message with tool role');
