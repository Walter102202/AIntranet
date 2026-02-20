-- Migración: Agregar soporte para filtros en reportes PowerBI
-- Fecha: 2025-11-23
-- Descripción: Agrega columna para almacenar metadatos de filtros disponibles

-- Agregar columna para metadatos de filtros (JSON)
ALTER TABLE powerbi_reports
ADD COLUMN IF NOT EXISTS available_filters JSON DEFAULT NULL
COMMENT 'Metadatos de filtros disponibles en formato JSON. Ejemplo: {"Mes": {"table": "Calendario", "column": "NombreMes", "values": ["Enero", "Febrero", "Marzo"]}}';

-- Agregar columna para tipo de embedding
ALTER TABLE powerbi_reports
ADD COLUMN IF NOT EXISTS embed_type ENUM('public', 'embedded') DEFAULT 'public'
COMMENT 'Tipo de URL de PowerBI: public (URL pública) o embedded (con token)';

-- Agregar índice para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_powerbi_embed_type ON powerbi_reports(embed_type);

-- Comentario de ayuda
-- Ejemplo de uso de available_filters:
-- {
--   "Mes": {
--     "table": "Calendario",
--     "column": "NombreMes",
--     "values": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
--     "type": "string"
--   },
--   "Región": {
--     "table": "Geografía",
--     "column": "Región",
--     "values": ["Norte", "Sur", "Este", "Oeste", "Centro"],
--     "type": "string"
--   },
--   "Año": {
--     "table": "Calendario",
--     "column": "Año",
--     "values": [2022, 2023, 2024, 2025],
--     "type": "number"
--   }
-- }
