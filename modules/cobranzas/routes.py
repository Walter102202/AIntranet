"""
Rutas para el módulo de Cobranzas
"""
from flask import render_template, jsonify, request, session
from modules.cobranzas import cobranzas_bp
from modules.auth.routes import login_required
from models import (Cliente, Factura, Pago, CobranzaSeguimiento, Cobranza,
                    MLModelo, MLEjecucion, MLResultadoCliente, MLKDDProceso,
                    MLMetricasModelo, MLComparacion)
import json


@cobranzas_bp.route('/')
@login_required
def index():
    """Página principal del módulo de cobranzas"""
    # Solo admin, rrhh y soporte pueden acceder
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return render_template('error.html',
                             error='No tienes permisos para acceder a este módulo'), 403

    # Obtener métricas del dashboard
    dashboard = Cobranza.get_dashboard_cobranzas()

    # Obtener lista de clientes con saldo
    clientes = Cliente.buscar('')  # Obtiene todos los clientes

    return render_template('cobranzas/index.html',
                         dashboard=dashboard,
                         clientes=clientes)


@cobranzas_bp.route('/cliente/<codigo>')
@login_required
def detalle_cliente(codigo):
    """Detalle de cobranza de un cliente"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return render_template('error.html',
                             error='No tienes permisos para acceder a este módulo'), 403

    # Obtener información del cliente
    cliente = Cliente.get_by_codigo(codigo)
    if not cliente:
        return render_template('error.html',
                             error='Cliente no encontrado'), 404

    # Obtener resumen completo de cobranza
    resumen = Cobranza.get_resumen_cliente_completo(codigo)

    # Obtener facturas del cliente
    facturas = Factura.get_by_cliente(codigo)

    # Obtener seguimientos
    seguimientos = CobranzaSeguimiento.get_by_cliente(codigo)

    return render_template('cobranzas/detalle_cliente.html',
                         cliente=cliente,
                         resumen=resumen,
                         facturas=facturas,
                         seguimientos=seguimientos)


@cobranzas_bp.route('/ml-results')
@login_required
def ml_results():
    """Página de resultados de Machine Learning"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return render_template('error.html',
                             error='No tienes permisos para acceder a este módulo'), 403

    # Obtener modelos activos
    modelos = MLModelo.get_all_activos()

    # Obtener clientes con resultados ML
    clientes = MLResultadoCliente.get_clientes_con_resultados()

    # Obtener últimas ejecuciones
    ultimas_ejecuciones = MLEjecucion.get_ultimas_ejecuciones(limit=10)

    return render_template('cobranzas/ml_results.html',
                         modelos=modelos,
                         clientes=clientes,
                         ultimas_ejecuciones=ultimas_ejecuciones)


@cobranzas_bp.route('/api/ml-results/cliente/<codigo>')
@login_required
def api_ml_results_cliente(codigo):
    """API: Obtiene resultados ML de un cliente"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return jsonify({'error': 'Sin permisos'}), 403

    # Obtener resultados del cliente
    resultados = MLResultadoCliente.get_by_cliente(codigo)

    if not resultados:
        return jsonify({'error': 'No hay resultados para este cliente'}), 404

    # Convertir resultados a formato JSON serializable
    resultados_json = []
    for r in resultados:
        resultado_dict = dict(r)

        # Parsear JSON strings si existen
        if resultado_dict.get('factores_principales'):
            try:
                resultado_dict['factores_principales'] = json.loads(resultado_dict['factores_principales'])
            except:
                pass

        if resultado_dict.get('datos_entrada'):
            try:
                resultado_dict['datos_entrada'] = json.loads(resultado_dict['datos_entrada'])
            except:
                pass

        resultados_json.append(resultado_dict)

    return jsonify(resultados_json)


@cobranzas_bp.route('/api/ml-results/ejecucion/<int:ejecucion_id>')
@login_required
def api_ml_ejecucion_detalle(ejecucion_id):
    """API: Obtiene detalles de una ejecución ML"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return jsonify({'error': 'Sin permisos'}), 403

    # Obtener ejecución
    ejecucion = MLEjecucion.get_by_id(ejecucion_id)
    if not ejecucion:
        return jsonify({'error': 'Ejecución no encontrada'}), 404

    # Obtener proceso KDD
    proceso_kdd = MLKDDProceso.get_by_ejecucion(ejecucion_id)

    # Obtener métricas
    metricas = MLMetricasModelo.get_by_ejecucion(ejecucion_id)

    # Obtener resultados
    resultados = MLResultadoCliente.get_by_ejecucion(ejecucion_id)

    return jsonify({
        'ejecucion': dict(ejecucion),
        'proceso_kdd': [dict(p) for p in proceso_kdd] if proceso_kdd else [],
        'metricas': dict(metricas) if metricas else None,
        'num_resultados': len(resultados) if resultados else 0
    })


@cobranzas_bp.route('/api/ml-results/comparar', methods=['POST'])
@login_required
def api_ml_comparar_modelos():
    """API: Compara resultados de múltiples modelos"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return jsonify({'error': 'Sin permisos'}), 403

    data = request.get_json()
    cliente_codigo = data.get('cliente_codigo')

    if not cliente_codigo:
        return jsonify({'error': 'Cliente no especificado'}), 400

    # Obtener todos los resultados del cliente
    resultados = MLResultadoCliente.get_by_cliente(cliente_codigo)

    if not resultados:
        return jsonify({'error': 'No hay resultados para comparar'}), 404

    # Agrupar por modelo
    comparacion = {}
    for r in resultados:
        modelo_nombre = r['modelo_nombre']
        if modelo_nombre not in comparacion:
            comparacion[modelo_nombre] = []

        comparacion[modelo_nombre].append({
            'fecha_ejecucion': str(r['fecha_ejecucion']),
            'score_prediccion': r['score_prediccion'],
            'clasificacion': r['clasificacion'],
            'probabilidad_pago': r['probabilidad_pago'],
            'dias_pago_predicho': r['dias_pago_predicho'],
            'confianza_prediccion': r['confianza_prediccion'],
            'accion_recomendada': r['accion_recomendada']
        })

    return jsonify(comparacion)


@cobranzas_bp.route('/api/ml-results/kdd-proceso/<int:ejecucion_id>')
@login_required
def api_ml_kdd_proceso(ejecucion_id):
    """API: Obtiene el proceso KDD de una ejecución"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return jsonify({'error': 'Sin permisos'}), 403

    proceso = MLKDDProceso.get_by_ejecucion(ejecucion_id)

    if not proceso:
        return jsonify({'error': 'Proceso KDD no encontrado'}), 404

    # Convertir a formato JSON
    proceso_json = []
    for p in proceso:
        etapa_dict = dict(p)

        # Parsear métricas si existen
        if etapa_dict.get('metricas_etapa'):
            try:
                etapa_dict['metricas_etapa'] = json.loads(etapa_dict['metricas_etapa'])
            except:
                pass

        proceso_json.append(etapa_dict)

    return jsonify(proceso_json)


@cobranzas_bp.route('/api/clientes/buscar')
@login_required
def api_buscar_clientes():
    """API: Busca clientes por nombre o código"""
    if session.get('rol') not in ['admin', 'rrhh', 'soporte']:
        return jsonify({'error': 'Sin permisos'}), 403

    query = request.args.get('q', '')
    clientes = Cliente.buscar(query)

    return jsonify([{
        'codigo': c['codigo'],
        'razon_social': c['razon_social'],
        'rfc': c['rfc']
    } for c in clientes] if clientes else [])
