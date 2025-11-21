-- ============================================
-- Schema para Resultados de Machine Learning
-- Módulo de Cobranzas - Metodología KDD
-- ============================================

-- Tabla de modelos ML registrados en el sistema
CREATE TABLE ml_modelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    tipo_modelo VARCHAR(50) NOT NULL, -- 'clasificacion', 'regresion', 'clustering', 'prediccion'
    algoritmo VARCHAR(100) NOT NULL, -- 'random_forest', 'xgboost', 'neural_network', etc.
    version VARCHAR(20) NOT NULL,
    objetivo TEXT NOT NULL, -- Descripción del objetivo del modelo
    variables_entrada TEXT, -- JSON con lista de variables utilizadas
    activo BOOLEAN DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ejecuciones de modelos ML
CREATE TABLE ml_ejecuciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL,
    fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_datos_desde DATE,
    fecha_datos_hasta DATE,
    num_registros_procesados INTEGER,
    duracion_segundos REAL,
    estado VARCHAR(20) DEFAULT 'completado', -- 'completado', 'error', 'en_proceso'
    parametros TEXT, -- JSON con parámetros del modelo
    notas TEXT,
    usuario_ejecutor VARCHAR(100),
    FOREIGN KEY (modelo_id) REFERENCES ml_modelos(id)
);

-- Proceso KDD tracking por ejecución
CREATE TABLE ml_kdd_proceso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL,
    etapa VARCHAR(50) NOT NULL, -- 'selection', 'preprocessing', 'transformation', 'data_mining', 'interpretation'
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    duracion_segundos REAL,
    descripcion TEXT,
    metricas_etapa TEXT, -- JSON con métricas específicas de cada etapa
    estado VARCHAR(20) DEFAULT 'completado',
    detalles TEXT, -- Información adicional de la etapa
    FOREIGN KEY (ejecucion_id) REFERENCES ml_ejecuciones(id)
);

-- Resultados ML por cliente
CREATE TABLE ml_resultados_cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL,
    cliente_codigo VARCHAR(20) NOT NULL,

    -- Predicciones/Resultados principales
    score_prediccion REAL, -- Score general del modelo (0-1 o escala específica)
    clasificacion VARCHAR(50), -- Categoría asignada: 'alto_riesgo', 'medio_riesgo', 'bajo_riesgo', etc.
    probabilidad_pago REAL, -- Probabilidad de pago (0-1)
    dias_pago_predicho INTEGER, -- Días estimados para pago
    monto_recuperable_predicho REAL, -- Monto estimado a recuperar

    -- Factores de decisión
    factores_principales TEXT, -- JSON con top factores que influyeron en la predicción
    confianza_prediccion REAL, -- Nivel de confianza del modelo (0-1)

    -- Segmentación
    segmento_cliente VARCHAR(50), -- Segmento asignado por clustering
    cluster_id INTEGER, -- ID de cluster si aplica

    -- Recomendaciones
    accion_recomendada VARCHAR(100), -- Acción sugerida por el modelo
    prioridad_cobranza VARCHAR(20), -- 'alta', 'media', 'baja'

    -- Metadata
    datos_entrada TEXT, -- JSON con datos del cliente utilizados
    explicacion TEXT, -- Explicación human-readable del resultado

    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ejecucion_id) REFERENCES ml_ejecuciones(id),
    FOREIGN KEY (cliente_codigo) REFERENCES clientes(codigo)
);

-- Métricas de rendimiento de modelos
CREATE TABLE ml_metricas_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id INTEGER NOT NULL,

    -- Métricas de clasificación
    accuracy REAL,
    precision_score REAL,
    recall REAL,
    f1_score REAL,
    auc_roc REAL,

    -- Métricas de regresión
    mae REAL, -- Mean Absolute Error
    mse REAL, -- Mean Squared Error
    rmse REAL, -- Root Mean Squared Error
    r2_score REAL, -- R-squared

    -- Métricas de clustering
    silhouette_score REAL,
    davies_bouldin_score REAL,
    calinski_harabasz_score REAL,

    -- Métricas de negocio específicas
    tasa_recuperacion_predicha REAL,
    valor_recuperado_real REAL,
    efectividad_recomendaciones REAL,

    -- Matriz de confusión (para clasificación)
    matriz_confusion TEXT, -- JSON con la matriz

    -- Métricas adicionales
    metricas_custom TEXT, -- JSON con métricas personalizadas

    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ejecucion_id) REFERENCES ml_ejecuciones(id)
);

-- Comparaciones entre modelos
CREATE TABLE ml_comparaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_comparacion VARCHAR(200) NOT NULL,
    descripcion TEXT,
    fecha_comparacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ejecuciones_comparadas TEXT NOT NULL, -- JSON array con IDs de ejecuciones
    criterio_comparacion VARCHAR(100), -- 'accuracy', 'f1_score', 'recuperacion', etc.
    modelo_ganador_id INTEGER,
    resultados_comparacion TEXT, -- JSON con resultados detallados
    conclusiones TEXT,
    usuario VARCHAR(100),
    FOREIGN KEY (modelo_ganador_id) REFERENCES ml_modelos(id)
);

-- Features/Variables utilizadas en modelos
CREATE TABLE ml_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL,
    nombre_feature VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo_dato VARCHAR(50), -- 'numerico', 'categorico', 'booleano', 'fecha'
    fuente_dato VARCHAR(100), -- tabla o cálculo de origen
    transformacion TEXT, -- Descripción de transformación aplicada
    importancia REAL, -- Importancia de la feature (si está disponible)
    estadisticas TEXT, -- JSON con estadísticas de la variable
    FOREIGN KEY (modelo_id) REFERENCES ml_modelos(id)
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_ml_ejecuciones_modelo ON ml_ejecuciones(modelo_id);
CREATE INDEX idx_ml_ejecuciones_fecha ON ml_ejecuciones(fecha_ejecucion);
CREATE INDEX idx_ml_resultados_ejecucion ON ml_resultados_cliente(ejecucion_id);
CREATE INDEX idx_ml_resultados_cliente ON ml_resultados_cliente(cliente_codigo);
CREATE INDEX idx_ml_resultados_clasificacion ON ml_resultados_cliente(clasificacion);
CREATE INDEX idx_ml_kdd_ejecucion ON ml_kdd_proceso(ejecucion_id);
CREATE INDEX idx_ml_kdd_etapa ON ml_kdd_proceso(etapa);
CREATE INDEX idx_ml_metricas_ejecucion ON ml_metricas_modelo(ejecucion_id);
CREATE INDEX idx_ml_features_modelo ON ml_features(modelo_id);

-- Vista consolidada de últimos resultados por cliente
CREATE VIEW v_ml_ultimos_resultados_cliente AS
SELECT
    rc.cliente_codigo,
    c.razon_social,
    m.nombre as modelo_nombre,
    m.tipo_modelo,
    m.algoritmo,
    e.fecha_ejecucion,
    rc.score_prediccion,
    rc.clasificacion,
    rc.probabilidad_pago,
    rc.dias_pago_predicho,
    rc.monto_recuperable_predicho,
    rc.accion_recomendada,
    rc.prioridad_cobranza,
    rc.confianza_prediccion,
    rc.segmento_cliente,
    met.accuracy,
    met.f1_score,
    met.auc_roc
FROM ml_resultados_cliente rc
JOIN ml_ejecuciones e ON rc.ejecucion_id = e.id
JOIN ml_modelos m ON e.modelo_id = m.id
JOIN clientes c ON rc.cliente_codigo = c.codigo
WHERE e.estado = 'completado'
AND m.activo = 1;

-- Vista comparativa de modelos
CREATE VIEW v_ml_comparacion_modelos AS
SELECT
    m.id as modelo_id,
    m.nombre as modelo_nombre,
    m.algoritmo,
    m.tipo_modelo,
    e.id as ejecucion_id,
    e.fecha_ejecucion,
    COUNT(DISTINCT rc.cliente_codigo) as num_clientes_evaluados,
    AVG(rc.score_prediccion) as score_promedio,
    AVG(rc.probabilidad_pago) as prob_pago_promedio,
    AVG(rc.confianza_prediccion) as confianza_promedio,
    met.accuracy,
    met.precision_score,
    met.recall,
    met.f1_score,
    met.auc_roc,
    met.rmse,
    met.r2_score
FROM ml_modelos m
LEFT JOIN ml_ejecuciones e ON m.id = e.modelo_id
LEFT JOIN ml_resultados_cliente rc ON e.id = rc.ejecucion_id
LEFT JOIN ml_metricas_modelo met ON e.id = met.ejecucion_id
WHERE m.activo = 1
AND e.estado = 'completado'
GROUP BY m.id, e.id;

-- Vista del proceso KDD por ejecución
CREATE VIEW v_ml_kdd_resumen AS
SELECT
    e.id as ejecucion_id,
    m.nombre as modelo_nombre,
    e.fecha_ejecucion,
    kdd.etapa,
    kdd.duracion_segundos,
    kdd.estado as estado_etapa,
    kdd.descripcion,
    kdd.fecha_inicio,
    kdd.fecha_fin
FROM ml_kdd_proceso kdd
JOIN ml_ejecuciones e ON kdd.ejecucion_id = e.id
JOIN ml_modelos m ON e.modelo_id = m.id
ORDER BY e.fecha_ejecucion DESC,
    CASE kdd.etapa
        WHEN 'selection' THEN 1
        WHEN 'preprocessing' THEN 2
        WHEN 'transformation' THEN 3
        WHEN 'data_mining' THEN 4
        WHEN 'interpretation' THEN 5
    END;
