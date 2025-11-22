#!/usr/bin/env python3
"""
Script para poblar datos de ejemplo de Cobranzas en la base de datos
Incluye facturas, pagos, seguimientos y alertas
"""
import random
from datetime import datetime, timedelta
from database import execute_query


def clean_cobranzas_tables():
    """Limpia todas las tablas de cobranzas antes de insertar datos nuevos"""
    print("Limpiando tablas de cobranzas existentes...")

    # Orden de eliminación respetando foreign keys
    tables = [
        'cobranza_alertas',
        'cobranza_seguimientos',
        'pago_facturas',
        'pagos',
        'facturas'
    ]

    for table in tables:
        query = f"DELETE FROM {table}"
        execute_query(query)
        print(f"  ✓ Tabla {table} limpiada")

    print()


def get_clientes():
    """Obtiene todos los clientes de la base de datos"""
    query = "SELECT id, codigo, razon_social FROM clientes WHERE activo = 1"
    return execute_query(query, fetch=True)


def seed_facturas(clientes):
    """Crea facturas de ejemplo para los clientes"""
    print("Creando facturas...")

    if not clientes:
        print("  ⚠ No hay clientes en la base de datos. Omitiendo facturas.")
        return []

    factura_ids = []
    estados = ['pendiente', 'parcial', 'pagada', 'vencida']

    for cliente in clientes:
        # Crear 5-10 facturas por cliente
        num_facturas = random.randint(5, 10)

        for i in range(num_facturas):
            numero_factura = f"FAC-{cliente['codigo']}-{datetime.now().year}-{i+1:04d}"

            # Fecha de emisión entre 1 y 180 días atrás
            dias_atras = random.randint(1, 180)
            fecha_emision = datetime.now() - timedelta(days=dias_atras)

            # Fecha de vencimiento: emisión + 30 días
            fecha_vencimiento = fecha_emision + timedelta(days=30)

            # Montos aleatorios
            subtotal = round(random.uniform(5000, 100000), 2)
            iva = round(subtotal * 0.16, 2)
            total = subtotal + iva

            # Estado de la factura
            estado = random.choice(estados)

            # Determinar saldo pendiente según estado
            if estado == 'pagada':
                saldo_pendiente = 0
            elif estado == 'parcial':
                saldo_pendiente = round(total * random.uniform(0.3, 0.7), 2)
            else:
                saldo_pendiente = total

            # Si la fecha de vencimiento ya pasó y está pendiente, marcar como vencida
            if fecha_vencimiento < datetime.now() and estado in ['pendiente', 'parcial']:
                estado = 'vencida'

            query = """
                INSERT INTO facturas
                (numero_factura, cliente_id, fecha_emision, fecha_vencimiento,
                 subtotal, iva, total, saldo_pendiente, estado, moneda)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'MXN')
            """

            lastrowid = execute_query(query, (
                numero_factura,
                cliente['id'],
                fecha_emision.date(),
                fecha_vencimiento.date(),
                subtotal,
                iva,
                total,
                saldo_pendiente,
                estado
            ))

            if lastrowid:
                factura_ids.append({
                    'id': lastrowid,
                    'numero': numero_factura,
                    'cliente_id': cliente['id'],
                    'total': total,
                    'saldo_pendiente': saldo_pendiente,
                    'estado': estado
                })

        print(f"  ✓ Creadas {num_facturas} facturas para cliente {cliente['razon_social']}")

    print(f"\n  Total de facturas creadas: {len(factura_ids)}")
    return factura_ids


def seed_pagos(clientes, facturas):
    """Crea pagos de ejemplo"""
    print("\nCreando pagos...")

    if not clientes or not facturas:
        print("  ⚠ No hay clientes o facturas. Omitiendo pagos.")
        return []

    pago_ids = []
    metodos = ['efectivo', 'transferencia', 'cheque', 'tarjeta']

    # Agrupar facturas por cliente
    facturas_por_cliente = {}
    for factura in facturas:
        cliente_id = factura['cliente_id']
        if cliente_id not in facturas_por_cliente:
            facturas_por_cliente[cliente_id] = []
        facturas_por_cliente[cliente_id].append(factura)

    for cliente in clientes:
        cliente_id = cliente['id']

        if cliente_id not in facturas_por_cliente:
            continue

        # Crear 2-5 pagos por cliente
        num_pagos = random.randint(2, 5)

        for i in range(num_pagos):
            numero_pago = f"PAG-{cliente['codigo']}-{datetime.now().year}-{i+1:04d}"

            # Fecha de pago entre 1 y 120 días atrás
            fecha_pago = datetime.now() - timedelta(days=random.randint(1, 120))

            # Monto del pago
            monto = round(random.uniform(10000, 80000), 2)

            query = """
                INSERT INTO pagos
                (numero_pago, cliente_id, fecha_pago, monto, metodo_pago, referencia)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            lastrowid = execute_query(query, (
                numero_pago,
                cliente_id,
                fecha_pago.date(),
                monto,
                random.choice(metodos),
                f"REF-{random.randint(100000, 999999)}"
            ))

            if lastrowid:
                pago_ids.append({
                    'id': lastrowid,
                    'numero': numero_pago,
                    'cliente_id': cliente_id,
                    'monto': monto
                })

                # Aplicar el pago a 1-3 facturas del cliente
                facturas_cliente = facturas_por_cliente[cliente_id]
                facturas_a_aplicar = random.sample(facturas_cliente, min(random.randint(1, 3), len(facturas_cliente)))

                monto_restante = monto
                for factura in facturas_a_aplicar:
                    if monto_restante <= 0:
                        break

                    monto_aplicado = min(monto_restante, factura['saldo_pendiente'])

                    query_aplicacion = """
                        INSERT INTO pago_facturas (pago_id, factura_id, monto_aplicado)
                        VALUES (%s, %s, %s)
                    """
                    execute_query(query_aplicacion, (lastrowid, factura['id'], monto_aplicado))

                    monto_restante -= monto_aplicado

        print(f"  ✓ Creados {num_pagos} pagos para cliente {cliente['razon_social']}")

    print(f"\n  Total de pagos creados: {len(pago_ids)}")
    return pago_ids


def seed_seguimientos(clientes, facturas):
    """Crea seguimientos de cobranza de ejemplo"""
    print("\nCreando seguimientos de cobranza...")

    if not clientes or not facturas:
        print("  ⚠ No hay clientes o facturas. Omitiendo seguimientos.")
        return

    # Obtener un usuario para asignar los seguimientos
    query_usuario = "SELECT id FROM usuarios LIMIT 1"
    usuario = execute_query(query_usuario, fetch=True)

    if not usuario:
        print("  ⚠ No hay usuarios. Omitiendo seguimientos.")
        return

    usuario_id = usuario[0]['id']

    tipos_contacto = ['llamada', 'email', 'whatsapp', 'visita']
    resultados = ['contactado', 'no_contesta', 'promesa_pago', 'rechaza_pago', 'pago_realizado']

    # Agrupar facturas por cliente
    facturas_por_cliente = {}
    for factura in facturas:
        cliente_id = factura['cliente_id']
        if cliente_id not in facturas_por_cliente:
            facturas_por_cliente[cliente_id] = []
        facturas_por_cliente[cliente_id].append(factura)

    count = 0
    for cliente in clientes:
        cliente_id = cliente['id']

        if cliente_id not in facturas_por_cliente:
            continue

        # Crear 3-8 seguimientos por cliente
        num_seguimientos = random.randint(3, 8)

        for i in range(num_seguimientos):
            # Fecha de contacto entre 1 y 90 días atrás
            fecha_contacto = datetime.now() - timedelta(days=random.randint(1, 90))

            resultado = random.choice(resultados)

            # Si es promesa de pago, agregar fecha promesa
            fecha_promesa = None
            monto_prometido = None
            if resultado == 'promesa_pago':
                fecha_promesa = (datetime.now() + timedelta(days=random.randint(5, 30))).date()
                monto_prometido = round(random.uniform(10000, 50000), 2)

            # Próximo seguimiento
            proximo_seguimiento = (datetime.now() + timedelta(days=random.randint(3, 15))).date()

            # Seleccionar una factura aleatoria del cliente
            factura = random.choice(facturas_por_cliente[cliente_id])

            query = """
                INSERT INTO cobranza_seguimientos
                (cliente_id, factura_id, tipo_contacto, fecha_contacto, resultado,
                 fecha_promesa_pago, monto_prometido, proximo_seguimiento, realizado_por,
                 notas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_query(query, (
                cliente_id,
                factura['id'],
                random.choice(tipos_contacto),
                fecha_contacto,
                resultado,
                fecha_promesa,
                monto_prometido,
                proximo_seguimiento,
                usuario_id,
                f"Seguimiento {i+1} - {resultado.replace('_', ' ').title()}"
            ))

            count += 1

    print(f"  ✓ Total de seguimientos creados: {count}")


def seed_alertas(clientes, facturas):
    """Crea alertas de cobranza de ejemplo"""
    print("\nCreando alertas de cobranza...")

    if not clientes or not facturas:
        print("  ⚠ No hay clientes o facturas. Omitiendo alertas.")
        return

    tipos_alerta = ['vencimiento_proximo', 'vencida', 'promesa_incumplida', 'limite_credito']

    # Filtrar facturas vencidas y por vencer
    facturas_vencidas = [f for f in facturas if f['estado'] == 'vencida']

    count = 0

    # Crear alertas para facturas vencidas
    for factura in random.sample(facturas_vencidas, min(10, len(facturas_vencidas))):
        query = """
            INSERT INTO cobranza_alertas
            (cliente_id, factura_id, tipo_alerta, mensaje, leida, activa)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        execute_query(query, (
            factura['cliente_id'],
            factura['id'],
            'vencida',
            f"Factura {factura['numero']} está vencida con saldo de ${factura['saldo_pendiente']:,.2f}",
            random.choice([True, False]),
            True
        ))
        count += 1

    print(f"  ✓ Total de alertas creadas: {count}")


def main():
    """Función principal"""
    print("=" * 60)
    print("SEED DE DATOS DE COBRANZAS")
    print("=" * 60)
    print()

    try:
        # 0. Limpiar datos existentes
        clean_cobranzas_tables()

        # 1. Obtener clientes
        clientes = get_clientes()

        if not clientes:
            print("\n❌ Error: No hay clientes en la base de datos.")
            print("   Sugerencia: Primero ejecuta el schema de cobranzas que crea clientes de ejemplo.")
            return

        print(f"Clientes encontrados: {len(clientes)}\n")

        # 2. Crear facturas
        facturas = seed_facturas(clientes)

        if not facturas:
            print("\n❌ Error: No se pudieron crear facturas")
            return

        # 3. Crear pagos
        pagos = seed_pagos(clientes, facturas)

        # 4. Crear seguimientos
        seed_seguimientos(clientes, facturas)

        # 5. Crear alertas
        seed_alertas(clientes, facturas)

        print("\n" + "=" * 60)
        print("✅ SEED COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nResumen:")
        print(f"  - Clientes: {len(clientes)}")
        print(f"  - Facturas creadas: {len(facturas)}")
        print(f"  - Pagos creados: {len(pagos)}")
        print(f"\nPuedes acceder al módulo de cobranzas y ver el dashboard actualizado.")

    except Exception as e:
        print(f"\n❌ Error durante el seed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
