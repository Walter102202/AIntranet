-- Script para crear las tablas del módulo de cobranzas
-- Base de datos: mi_database

USE mi_database;

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    razon_social VARCHAR(200) NOT NULL,
    rfc VARCHAR(20),
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(20),
    limite_credito DECIMAL(12,2) DEFAULT 0,
    dias_credito INT DEFAULT 30,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_codigo (codigo),
    INDEX idx_razon_social (razon_social)
);

-- Tabla de facturas
CREATE TABLE IF NOT EXISTS facturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    cliente_id INT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    iva DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    saldo_pendiente DECIMAL(12,2) NOT NULL,
    moneda ENUM('MXN', 'USD') DEFAULT 'MXN',
    estado ENUM('pendiente', 'parcial', 'pagada', 'vencida', 'cancelada') DEFAULT 'pendiente',
    notas TEXT,
    creado_por INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_cliente (cliente_id),
    INDEX idx_estado (estado),
    INDEX idx_vencimiento (fecha_vencimiento),
    INDEX idx_numero (numero_factura)
);

-- Tabla de pagos recibidos
CREATE TABLE IF NOT EXISTS pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_pago VARCHAR(50) UNIQUE NOT NULL,
    cliente_id INT NOT NULL,
    fecha_pago DATE NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    metodo_pago ENUM('efectivo', 'transferencia', 'cheque', 'tarjeta', 'otro') DEFAULT 'transferencia',
    referencia VARCHAR(100),
    banco VARCHAR(100),
    notas TEXT,
    registrado_por INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_cliente (cliente_id),
    INDEX idx_fecha (fecha_pago)
);

-- Tabla de aplicacion de pagos a facturas (relacion N:M)
CREATE TABLE IF NOT EXISTS pago_facturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pago_id INT NOT NULL,
    factura_id INT NOT NULL,
    monto_aplicado DECIMAL(12,2) NOT NULL,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON DELETE CASCADE,
    FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE RESTRICT,
    INDEX idx_pago (pago_id),
    INDEX idx_factura (factura_id)
);

-- Tabla de seguimientos de cobranza
CREATE TABLE IF NOT EXISTS cobranza_seguimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    factura_id INT,
    tipo_contacto ENUM('llamada', 'email', 'visita', 'whatsapp', 'carta', 'otro') DEFAULT 'llamada',
    fecha_contacto TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resultado ENUM('contactado', 'no_contesta', 'promesa_pago', 'rechaza_pago', 'pago_realizado', 'otro') DEFAULT 'contactado',
    fecha_promesa_pago DATE,
    monto_prometido DECIMAL(12,2),
    notas TEXT,
    proximo_seguimiento DATE,
    realizado_por INT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE SET NULL,
    FOREIGN KEY (realizado_por) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_cliente (cliente_id),
    INDEX idx_factura (factura_id),
    INDEX idx_fecha (fecha_contacto),
    INDEX idx_proximo (proximo_seguimiento)
);

-- Tabla de alertas de cobranza
CREATE TABLE IF NOT EXISTS cobranza_alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    factura_id INT,
    tipo_alerta ENUM('vencimiento_proximo', 'vencida', 'promesa_incumplida', 'limite_credito', 'otro') NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_lectura TIMESTAMP NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE SET NULL,
    INDEX idx_cliente (cliente_id),
    INDEX idx_activa (activa),
    INDEX idx_leida (leida)
);

-- Vista para resumen de cartera por cliente
CREATE OR REPLACE VIEW v_cartera_cliente AS
SELECT
    c.id as cliente_id,
    c.codigo,
    c.razon_social,
    COUNT(f.id) as total_facturas,
    SUM(CASE WHEN f.estado IN ('pendiente', 'parcial', 'vencida') THEN 1 ELSE 0 END) as facturas_pendientes,
    SUM(CASE WHEN f.estado = 'vencida' THEN 1 ELSE 0 END) as facturas_vencidas,
    COALESCE(SUM(f.saldo_pendiente), 0) as saldo_total,
    COALESCE(SUM(CASE WHEN f.estado = 'vencida' THEN f.saldo_pendiente ELSE 0 END), 0) as saldo_vencido
FROM clientes c
LEFT JOIN facturas f ON c.id = f.cliente_id AND f.estado != 'cancelada'
WHERE c.activo = TRUE
GROUP BY c.id, c.codigo, c.razon_social;

-- Vista para antigüedad de saldos
CREATE OR REPLACE VIEW v_antiguedad_saldos AS
SELECT
    f.id as factura_id,
    f.numero_factura,
    c.id as cliente_id,
    c.razon_social,
    f.fecha_vencimiento,
    f.saldo_pendiente,
    DATEDIFF(CURDATE(), f.fecha_vencimiento) as dias_vencido,
    CASE
        WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) <= 0 THEN 'vigente'
        WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 1 AND 30 THEN '1-30 dias'
        WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 31 AND 60 THEN '31-60 dias'
        WHEN DATEDIFF(CURDATE(), f.fecha_vencimiento) BETWEEN 61 AND 90 THEN '61-90 dias'
        ELSE 'mas de 90 dias'
    END as rango_antiguedad
FROM facturas f
JOIN clientes c ON f.cliente_id = c.id
WHERE f.estado IN ('pendiente', 'parcial', 'vencida')
ORDER BY dias_vencido DESC;

-- Datos iniciales de ejemplo
INSERT INTO clientes (codigo, razon_social, rfc, email, telefono, limite_credito, dias_credito) VALUES
('CLI001', 'Empresa Ejemplo S.A. de C.V.', 'EEJ123456ABC', 'contacto@ejemplo.com', '555-123-4567', 50000.00, 30),
('CLI002', 'Comercializadora Norte S.A.', 'CNO789012DEF', 'pagos@comnorte.com', '555-987-6543', 100000.00, 45);
