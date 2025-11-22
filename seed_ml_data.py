#!/usr/bin/env python3
"""
Script para poblar datos de ejemplo de ML en la base de datos
Incluye modelos, ejecuciones, resultados por cliente y proceso KDD
"""
import json
from datetime import datetime, timedelta
import random
from database import execute_query

def clean_ml_tables():
    """Limpia todas las tablas ML antes de insertar datos nuevos"""
    print("Limpiando tablas ML existentes...")

    # Orden de eliminación respetando foreign keys
    tables = [
        'ml_resultados_cliente',
        'ml_metricas_modelo',
        'ml_kdd_proceso',
        'ml_ejecuciones',
        'ml_comparaciones',
        'ml_features',
        'ml_modelos'
    ]

    for table in tables:
        query = f"DELETE FROM {table}"
        execute_query(query)
        print(f"  ✓ Tabla {table} limpiada")

    print()

def seed_ml_models():
    """Crea modelos de ML de ejemplo"""
    print("Creando modelos de ML...")

    modelos = [
        {
            'nombre': 'Clasificador de Riesgo de Pago',
            'descripcion': 'Modelo de clasificación que predice el riesgo de impago basado en histórico de pagos, antigüedad de saldos y comportamiento del cliente',
            'tipo_modelo': 'clasificacion',
            'algoritmo': 'Random Forest',
            'version': '1.0',
            'objetivo': 'Clasificar clientes en categorías de riesgo (alto, medio, bajo) para priorizar gestiones de cobranza',
            'variables_entrada': json.dumps([
                'dias_promedio_pago',
                'facturas_vencidas',
                'saldo_pendiente',
                'limite_credito',
                'antiguedad_cliente',
                'tasa_incumplimiento',
                'numero_promesas_incumplidas'
            ])
        },
        {
            'nombre': 'Predictor de Probabilidad de Pago',
            'descripcion': 'Modelo de regresión que estima la probabilidad de que un cliente realice el pago en los próximos 30 días',
            'tipo_modelo': 'regresion',
            'algoritmo': 'XGBoost',
            'version': '1.2',
            'objetivo': 'Predecir probabilidad de pago para optimizar recursos de cobranza',
            'variables_entrada': json.dumps([
                'historial_pagos',
                'promesas_cumplidas',
                'dias_atraso',
                'monto_pendiente',
                'contactos_realizados',
                'estacionalidad'
            ])
        },
        {
            'nombre': 'Segmentador de Clientes',
            'descripcion': 'Modelo de clustering que agrupa clientes por patrones de comportamiento de pago',
            'tipo_modelo': 'clustering',
            'algoritmo': 'K-Means',
            'version': '1.0',
            'objetivo': 'Segmentar clientes para estrategias de cobranza personalizadas',
            'variables_entrada': json.dumps([
                'frecuencia_pago',
                'puntualidad',
                'volumen_compra',
                'respuesta_contactos',
                'antiguedad'
            ])
        },
        {
            'nombre': 'Estimador de Días hasta Pago',
            'descripcion': 'Modelo predictivo que estima cuántos días tomará al cliente realizar el pago',
            'tipo_modelo': 'prediccion',
            'algoritmo': 'Gradient Boosting',
            'version': '1.1',
            'objetivo': 'Estimar tiempo de recuperación para proyecciones de flujo de caja',
            'variables_entrada': json.dumps([
                'dias_credito',
                'historial_atrasos',
                'monto_factura',
                'industria_cliente',
                'temporada'
            ])
        }
    ]

    modelo_ids = []
    for modelo in modelos:
        query = """
            INSERT INTO ml_modelos
            (nombre, descripcion, tipo_modelo, algoritmo, version, objetivo, variables_entrada, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """
        lastrowid = execute_query(query, (
            modelo['nombre'],
            modelo['descripcion'],
            modelo['tipo_modelo'],
            modelo['algoritmo'],
            modelo['version'],
            modelo['objetivo'],
            modelo['variables_entrada']
        ))

        # execute_query devuelve el lastrowid directamente para INSERT
        if lastrowid:
            modelo_ids.append(lastrowid)
            print(f"  ✓ Creado: {modelo['nombre']} (ID: {lastrowid})")

    return modelo_ids


def seed_ml_executions(modelo_ids):
    """Crea ejecuciones de modelos"""
    print("\nCreando ejecuciones de modelos...")

    ejecucion_ids = []

    for modelo_id in modelo_ids:
        # Crear 2-3 ejecuciones por modelo
        num_ejecuciones = random.randint(2, 3)

        for i in range(num_ejecuciones):
            fecha_ejecucion = datetime.now() - timedelta(days=random.randint(1, 60))
            fecha_desde = fecha_ejecucion - timedelta(days=180)
            fecha_hasta = fecha_ejecucion - timedelta(days=1)

            query = """
                INSERT INTO ml_ejecuciones
                (modelo_id, fecha_ejecucion, fecha_datos_desde, fecha_datos_hasta,
                 num_registros_procesados, duracion_segundos, estado, parametros, usuario_ejecutor)
                VALUES (%s, %s, %s, %s, %s, %s, 'completado', %s, 'admin')
            """

            parametros = json.dumps({
                'train_test_split': 0.8,
                'cross_validation_folds': 5,
                'random_state': 42
            })

            lastrowid = execute_query(query, (
                modelo_id,
                fecha_ejecucion,
                fecha_desde,
                fecha_hasta,
                random.randint(100, 500),
                round(random.uniform(10, 120), 2),
                parametros
            ))

            # execute_query devuelve el lastrowid directamente para INSERT
            if lastrowid:
                ejecucion_ids.append(lastrowid)
                print(f"  ✓ Ejecución creada para modelo {modelo_id} (ID: {lastrowid})")

    return ejecucion_ids


def seed_kdd_process(ejecucion_ids):
    """Crea datos del proceso KDD para cada ejecución"""
    print("\nCreando proceso KDD...")

    etapas_kdd = [
        {
            'etapa': 'selection',
            'descripcion': 'Selección de datos de clientes, facturas y pagos de los últimos 12 meses',
            'detalles': 'Se seleccionaron registros con facturas pendientes y al menos 3 transacciones'
        },
        {
            'etapa': 'preprocessing',
            'descripcion': 'Limpieza de datos: eliminación de outliers, manejo de valores faltantes',
            'detalles': 'Se imputaron valores faltantes y se eliminaron 3% de registros con anomalías'
        },
        {
            'etapa': 'transformation',
            'descripcion': 'Normalización de variables numéricas y encoding de variables categóricas',
            'detalles': 'Se aplicó StandardScaler y OneHotEncoding según el tipo de variable'
        },
        {
            'etapa': 'data_mining',
            'descripcion': 'Entrenamiento del modelo con validación cruzada',
            'detalles': 'Se optimizaron hiperparámetros mediante GridSearchCV'
        },
        {
            'etapa': 'interpretation',
            'descripcion': 'Evaluación de métricas y generación de predicciones',
            'detalles': 'Se calcularon métricas de rendimiento y se interpretaron resultados'
        }
    ]

    for ejecucion_id in ejecucion_ids:
        fecha_base = datetime.now() - timedelta(days=random.randint(1, 60))

        for idx, etapa in enumerate(etapas_kdd):
            fecha_inicio = fecha_base + timedelta(seconds=sum([random.uniform(5, 30) for _ in range(idx)]))
            duracion = random.uniform(5, 30)
            fecha_fin = fecha_inicio + timedelta(seconds=duracion)

            metricas_etapa = json.dumps({
                'registros_procesados': random.randint(100, 500),
                'registros_validos': random.randint(95, 100),
                'tiempo_cpu': round(duracion * 0.8, 2)
            })

            query = """
                INSERT INTO ml_kdd_proceso
                (ejecucion_id, etapa, fecha_inicio, fecha_fin, duracion_segundos,
                 descripcion, metricas_etapa, estado, detalles)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'completado', %s)
            """

            execute_query(query, (
                ejecucion_id,
                etapa['etapa'],
                fecha_inicio,
                fecha_fin,
                round(duracion, 2),
                etapa['descripcion'],
                metricas_etapa,
                etapa['detalles']
            ))

        print(f"  ✓ Proceso KDD creado para ejecución {ejecucion_id}")


def seed_ml_metrics(ejecucion_ids):
    """Crea métricas de rendimiento para cada ejecución"""
    print("\nCreando métricas de modelos...")

    for ejecucion_id in ejecucion_ids:
        # Obtener info de la ejecución para determinar tipo de modelo
        query = """
            SELECT m.tipo_modelo
            FROM ml_ejecuciones e
            JOIN ml_modelos m ON e.modelo_id = m.id
            WHERE e.id = %s
        """
        result = execute_query(query, (ejecucion_id,), fetch=True)

        if not result:
            continue

        tipo_modelo = result[0]['tipo_modelo']

        # Generar métricas según el tipo de modelo
        accuracy = round(random.uniform(0.75, 0.95), 4) if tipo_modelo == 'clasificacion' else None
        precision = round(random.uniform(0.70, 0.90), 4) if tipo_modelo == 'clasificacion' else None
        recall = round(random.uniform(0.72, 0.92), 4) if tipo_modelo == 'clasificacion' else None
        f1 = round(random.uniform(0.73, 0.91), 4) if tipo_modelo == 'clasificacion' else None
        auc_roc = round(random.uniform(0.80, 0.96), 4) if tipo_modelo == 'clasificacion' else None

        mae = round(random.uniform(0.05, 0.15), 4) if tipo_modelo == 'regresion' else None
        rmse = round(random.uniform(0.10, 0.25), 4) if tipo_modelo == 'regresion' else None
        r2 = round(random.uniform(0.75, 0.95), 4) if tipo_modelo == 'regresion' else None

        silhouette = round(random.uniform(0.40, 0.70), 4) if tipo_modelo == 'clustering' else None

        matriz_confusion = json.dumps([
            [45, 5],
            [3, 47]
        ]) if tipo_modelo == 'clasificacion' else None

        query = """
            INSERT INTO ml_metricas_modelo
            (ejecucion_id, accuracy, precision_score, recall, f1_score, auc_roc,
             mae, rmse, r2_score, silhouette_score, tasa_recuperacion_predicha, matriz_confusion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        execute_query(query, (
            ejecucion_id,
            accuracy,
            precision,
            recall,
            f1,
            auc_roc,
            mae,
            rmse,
            r2,
            silhouette,
            round(random.uniform(0.60, 0.85), 4),
            matriz_confusion
        ))

        print(f"  ✓ Métricas creadas para ejecución {ejecucion_id}")


def seed_ml_results_cliente(ejecucion_ids):
    """Crea resultados ML para clientes"""
    print("\nCreando resultados ML por cliente...")

    # Obtener clientes existentes
    query = "SELECT codigo FROM clientes LIMIT 10"
    clientes = execute_query(query, fetch=True)

    if not clientes:
        print("  ⚠ No hay clientes en la base de datos. Omitiendo resultados por cliente.")
        return

    clasificaciones = ['alto_riesgo', 'medio_riesgo', 'bajo_riesgo']
    acciones = [
        'Contactar inmediatamente por teléfono',
        'Enviar recordatorio por email',
        'Programar visita presencial',
        'Aplicar descuento por pronto pago',
        'Negociar plan de pagos',
        'Mantener monitoreo regular'
    ]
    prioridades = ['alta', 'media', 'baja']
    segmentos = ['Pagador puntual', 'Pagador ocasional', 'Moroso frecuente', 'Nuevo cliente']

    for ejecucion_id in ejecucion_ids:
        # Crear resultados para 5-8 clientes aleatorios
        clientes_muestra = random.sample(clientes, min(random.randint(5, 8), len(clientes)))

        for cliente in clientes_muestra:
            clasificacion = random.choice(clasificaciones)

            # Ajustar probabilidades según clasificación
            if clasificacion == 'bajo_riesgo':
                prob_pago = random.uniform(0.75, 0.95)
                dias_pago = random.randint(5, 20)
                prioridad = 'baja'
            elif clasificacion == 'medio_riesgo':
                prob_pago = random.uniform(0.50, 0.75)
                dias_pago = random.randint(15, 45)
                prioridad = 'media'
            else:  # alto_riesgo
                prob_pago = random.uniform(0.20, 0.50)
                dias_pago = random.randint(30, 90)
                prioridad = 'alta'

            factores = json.dumps([
                {'nombre': 'Días promedio de atraso', 'valor': f'{random.randint(5, 60)} días', 'importancia': 0.85},
                {'nombre': 'Tasa de cumplimiento', 'valor': f'{random.randint(40, 95)}%', 'importancia': 0.78},
                {'nombre': 'Antigüedad de saldo', 'valor': f'{random.randint(10, 120)} días', 'importancia': 0.72},
                {'nombre': 'Número de facturas vencidas', 'valor': str(random.randint(1, 10)), 'importancia': 0.65}
            ])

            query = """
                INSERT INTO ml_resultados_cliente
                (ejecucion_id, cliente_codigo, score_prediccion, clasificacion,
                 probabilidad_pago, dias_pago_predicho, monto_recuperable_predicho,
                 factores_principales, confianza_prediccion, segmento_cliente,
                 accion_recomendada, prioridad_cobranza, explicacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_query(query, (
                ejecucion_id,
                cliente['codigo'],
                round(random.uniform(0.3, 0.95), 4),
                clasificacion,
                round(prob_pago, 4),
                dias_pago,
                round(random.uniform(5000, 50000), 2),
                factores,
                round(random.uniform(0.75, 0.95), 4),
                random.choice(segmentos),
                random.choice(acciones),
                prioridad,
                f'El modelo predice que este cliente tiene una probabilidad del {int(prob_pago*100)}% de realizar el pago en los próximos {dias_pago} días, basándose en su historial de pagos y comportamiento actual.'
            ))

        print(f"  ✓ Resultados creados para ejecución {ejecucion_id} ({len(clientes_muestra)} clientes)")


def main():
    """Función principal"""
    print("=" * 60)
    print("SEED DE DATOS ML - MÓDULO DE COBRANZAS")
    print("=" * 60)
    print()

    try:
        # 0. Limpiar datos existentes
        clean_ml_tables()

        # 1. Crear modelos
        modelo_ids = seed_ml_models()

        if not modelo_ids:
            print("\n❌ Error: No se pudieron crear los modelos")
            return

        # 2. Crear ejecuciones
        ejecucion_ids = seed_ml_executions(modelo_ids)

        if not ejecucion_ids:
            print("\n❌ Error: No se pudieron crear las ejecuciones")
            return

        # 3. Crear proceso KDD
        seed_kdd_process(ejecucion_ids)

        # 4. Crear métricas
        seed_ml_metrics(ejecucion_ids)

        # 5. Crear resultados por cliente
        seed_ml_results_cliente(ejecucion_ids)

        print("\n" + "=" * 60)
        print("✅ SEED COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nResumen:")
        print(f"  - Modelos creados: {len(modelo_ids)}")
        print(f"  - Ejecuciones creadas: {len(ejecucion_ids)}")
        print(f"  - Procesos KDD: {len(ejecucion_ids)}")
        print(f"\nPuedes acceder al módulo de cobranzas y ver los resultados ML.")

    except Exception as e:
        print(f"\n❌ Error durante el seed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
