-- Script para crear las tablas del portal de intranet
-- Base de datos: mi_database

USE mi_database;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    rol ENUM('admin', 'empleado', 'rrhh', 'soporte') DEFAULT 'empleado',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Tabla de departamentos
CREATE TABLE IF NOT EXISTS departamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de empleados (directorio)
CREATE TABLE IF NOT EXISTS empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    extension VARCHAR(10),
    departamento_id INT,
    cargo VARCHAR(100),
    fecha_ingreso DATE,
    foto_url VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (departamento_id) REFERENCES departamentos(id) ON DELETE SET NULL,
    INDEX idx_departamento (departamento_id),
    INDEX idx_nombre (nombre, apellido)
);

-- Tabla de solicitudes de vacaciones
CREATE TABLE IF NOT EXISTS vacaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    dias_solicitados INT NOT NULL,
    tipo ENUM('vacaciones', 'permiso', 'licencia_medica', 'otro') DEFAULT 'vacaciones',
    motivo TEXT,
    estado ENUM('pendiente', 'aprobada', 'rechazada', 'cancelada') DEFAULT 'pendiente',
    aprobador_id INT,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta TIMESTAMP NULL,
    comentarios_aprobador TEXT,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (aprobador_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_empleado (empleado_id),
    INDEX idx_estado (estado),
    INDEX idx_fechas (fecha_inicio, fecha_fin)
);

-- Tabla de documentos corporativos
CREATE TABLE IF NOT EXISTS documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria ENUM('politicas', 'procedimientos', 'manuales', 'formularios', 'otros') DEFAULT 'otros',
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tamanio INT,
    tipo_archivo VARCHAR(50),
    subido_por INT NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NULL,
    descargas INT DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (subido_por) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_categoria (categoria),
    INDEX idx_fecha (fecha_subida)
);

-- Tabla de anuncios/noticias
CREATE TABLE IF NOT EXISTS anuncios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    contenido TEXT NOT NULL,
    tipo ENUM('general', 'urgente', 'evento', 'comunicado') DEFAULT 'general',
    prioridad ENUM('baja', 'media', 'alta') DEFAULT 'media',
    autor_id INT NOT NULL,
    fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATE NULL,
    imagen_url VARCHAR(255),
    vistas INT DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_tipo (tipo),
    INDEX idx_fecha (fecha_publicacion),
    INDEX idx_activo (activo)
);

-- Tabla de tickets de soporte
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria ENUM('ti', 'rrhh', 'mantenimiento', 'administrativo', 'otro') DEFAULT 'otro',
    prioridad ENUM('baja', 'media', 'alta', 'urgente') DEFAULT 'media',
    estado ENUM('abierto', 'en_proceso', 'resuelto', 'cerrado') DEFAULT 'abierto',
    solicitante_id INT NOT NULL,
    asignado_a INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NULL,
    fecha_resolucion TIMESTAMP NULL,
    solucion TEXT,
    FOREIGN KEY (solicitante_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (asignado_a) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_estado (estado),
    INDEX idx_prioridad (prioridad),
    INDEX idx_categoria (categoria),
    INDEX idx_solicitante (solicitante_id)
);

-- Tabla de comentarios en tickets
CREATE TABLE IF NOT EXISTS ticket_comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    usuario_id INT NOT NULL,
    comentario TEXT NOT NULL,
    fecha_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_ticket (ticket_id)
);

-- Insertar datos iniciales

-- Departamentos por defecto
INSERT INTO departamentos (nombre, descripcion) VALUES
('Tecnología', 'Departamento de Tecnologías de la Información'),
('Recursos Humanos', 'Gestión de personal y talento'),
('Administración', 'Gestión administrativa y financiera'),
('Operaciones', 'Operaciones y logística'),
('Dirección', 'Dirección general y gerencia');

-- NOTA: El usuario inicial se crea con init_db.py usando las variables de entorno
-- Configura ADMIN_USERNAME, ADMIN_PASSWORD y ADMIN_EMAIL en tu archivo .env
-- Luego ejecuta: python init_db.py

-- Algunos anuncios de ejemplo
INSERT INTO anuncios (titulo, contenido, tipo, prioridad, autor_id, fecha_expiracion) VALUES
('Bienvenido al Portal de Intranet', 'Bienvenido al nuevo portal de intranet corporativo. Aquí encontrarás toda la información y herramientas necesarias para tu trabajo diario.', 'general', 'alta', 1, DATE_ADD(CURDATE(), INTERVAL 30 DAY)),
('Mantenimiento Programado', 'Se realizará mantenimiento del sistema el próximo fin de semana. El portal estará disponible el lunes por la mañana.', 'comunicado', 'media', 1, DATE_ADD(CURDATE(), INTERVAL 7 DAY));
