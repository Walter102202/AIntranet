-- Script para crear las tablas del chatbot con IA
-- Base de datos: mi_database

USE mi_database;

-- Tabla de sesiones de chatbot
-- Almacena las sesiones de conversación de cada usuario
CREATE TABLE IF NOT EXISTS chatbot_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    session_key VARCHAR(100) UNIQUE NOT NULL,
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultimo_mensaje TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    activa BOOLEAN DEFAULT TRUE,
    metadata JSON,  -- Para almacenar contexto adicional de la sesión
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id),
    INDEX idx_session_key (session_key),
    INDEX idx_activa (activa),
    INDEX idx_fecha_ultimo (fecha_ultimo_mensaje)
);

-- Tabla de mensajes del chatbot
-- Almacena el historial completo de conversaciones
CREATE TABLE IF NOT EXISTS chatbot_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant', 'system', 'tool') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tool_calls JSON,  -- Almacena las llamadas a herramientas/acciones ejecutadas
    metadata JSON,  -- Información adicional del mensaje
    FOREIGN KEY (session_id) REFERENCES chatbot_sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_role (role)
);

-- Tabla de acciones ejecutadas por el chatbot
-- Registra todas las acciones que el chatbot ha ejecutado
CREATE TABLE IF NOT EXISTS chatbot_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    message_id INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,  -- Ej: 'create_vacation', 'upload_document', etc.
    action_params JSON,  -- Parámetros de la acción
    action_result JSON,  -- Resultado de la acción
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chatbot_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES chatbot_messages(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp)
);
