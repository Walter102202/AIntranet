-- Migración: Crear tabla de auditoría
-- Fecha: 2026-02-20
-- Descripción: Registra acciones importantes de usuarios y del sistema

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    usuario_nombre VARCHAR(255) NULL,
    accion VARCHAR(100) NOT NULL COMMENT 'Tipo de acción: login, create_user, approve_vacation, etc.',
    recurso VARCHAR(100) NULL COMMENT 'Tipo de recurso afectado: usuario, vacacion, ticket, etc.',
    recurso_id INT NULL COMMENT 'ID del recurso afectado',
    detalles JSON NULL COMMENT 'Detalles adicionales de la acción',
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    resultado ENUM('exito', 'error', 'denegado') DEFAULT 'exito',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuario (usuario_id),
    INDEX idx_accion (accion),
    INDEX idx_recurso (recurso, recurso_id),
    INDEX idx_fecha (fecha_creacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
