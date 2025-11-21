-- Tabla para reportes de Power BI
CREATE TABLE IF NOT EXISTS powerbi_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    embed_url TEXT NOT NULL,
    categoria ENUM('general', 'ventas', 'finanzas', 'operaciones', 'rrhh', 'marketing') DEFAULT 'general',
    creado_por INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Indice para busquedas por categoria
CREATE INDEX idx_powerbi_categoria ON powerbi_reports(categoria);
CREATE INDEX idx_powerbi_activo ON powerbi_reports(activo);
