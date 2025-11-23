#!/usr/bin/env python3
"""
Script de migración para agregar soporte de filtros a PowerBI Reports
Ejecuta las migraciones SQL necesarias en la base de datos
"""

import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

# ✅ CARGAR .env ANTES DE IMPORTAR config
from dotenv import load_dotenv
load_dotenv()

# ✅ Ahora sí importar Config (con .env cargado)
from config import Config
import mysql.connector
from mysql.connector import Error
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_connection():
    """Crea conexión a MySQL usando credenciales del .env"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )
        return connection
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        return None


def column_exists(cursor, table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result['count'] > 0


def index_exists(cursor, table_name, index_name):
    """Verifica si un índice existe en una tabla"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
    """, (table_name, index_name))
    result = cursor.fetchone()
    return result['count'] > 0


def run_migration():
    """Ejecuta la migración para agregar columnas de filtros"""

    logger.info("=== Iniciando migración de PowerBI Reports ===")

    connection = get_connection()
    if not connection:
        logger.error("No se pudo conectar a la base de datos")
        return False

    cursor = connection.cursor(dictionary=True)
    success_count = 0
    error_count = 0

    # Migración 1: Agregar columna available_filters
    try:
        logger.info("Ejecutando: Agregar columna available_filters")
        if not column_exists(cursor, 'powerbi_reports', 'available_filters'):
            cursor.execute("""
                ALTER TABLE powerbi_reports
                ADD COLUMN available_filters JSON DEFAULT NULL
                COMMENT 'Metadatos de filtros disponibles en formato JSON'
            """)
            connection.commit()
            logger.info("✓ Agregar columna available_filters - ÉXITO")
            success_count += 1
        else:
            logger.info("✓ Columna available_filters ya existe - OMITIDO")
            success_count += 1
    except Error as e:
        logger.error(f"✗ Error al agregar available_filters: {e}")
        error_count += 1

    # Migración 2: Agregar columna embed_type
    try:
        logger.info("Ejecutando: Agregar columna embed_type")
        if not column_exists(cursor, 'powerbi_reports', 'embed_type'):
            cursor.execute("""
                ALTER TABLE powerbi_reports
                ADD COLUMN embed_type ENUM('public', 'embedded') DEFAULT 'public'
                COMMENT 'Tipo de URL de PowerBI: public o embedded'
            """)
            connection.commit()
            logger.info("✓ Agregar columna embed_type - ÉXITO")
            success_count += 1
        else:
            logger.info("✓ Columna embed_type ya existe - OMITIDO")
            success_count += 1
    except Error as e:
        logger.error(f"✗ Error al agregar embed_type: {e}")
        error_count += 1

    # Migración 3: Crear índice para embed_type
    try:
        logger.info("Ejecutando: Crear índice para embed_type")
        if not index_exists(cursor, 'powerbi_reports', 'idx_powerbi_embed_type'):
            cursor.execute("""
                CREATE INDEX idx_powerbi_embed_type
                ON powerbi_reports(embed_type)
            """)
            connection.commit()
            logger.info("✓ Crear índice para embed_type - ÉXITO")
            success_count += 1
        else:
            logger.info("✓ Índice idx_powerbi_embed_type ya existe - OMITIDO")
            success_count += 1
    except Error as e:
        logger.error(f"✗ Error al crear índice: {e}")
        error_count += 1

    cursor.close()
    connection.close()

    # Resumen
    logger.info("\n=== Resumen de Migración ===")
    logger.info(f"Total de migraciones: 3")
    logger.info(f"Exitosas: {success_count}")
    logger.info(f"Fallidas: {error_count}")

    if error_count == 0:
        logger.info("\n✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        return True
    else:
        logger.warning(f"\n⚠ MIGRACIÓN COMPLETADA CON {error_count} ERRORES")
        return False


def verify_migration():
    """Verifica que las columnas fueron agregadas correctamente"""
    logger.info("\n=== Verificando migración ===")

    connection = get_connection()
    if not connection:
        logger.error("No se pudo conectar para verificar la migración")
        return False

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("DESCRIBE powerbi_reports")
        result = cursor.fetchall()
        cursor.close()
        connection.close()

        if not result:
            logger.error("No se pudo obtener la estructura de la tabla")
            return False

        columns = [row['Field'] for row in result]

        required_columns = ['available_filters', 'embed_type']
        missing_columns = [col for col in required_columns if col not in columns]

        if not missing_columns:
            logger.info("✓ Todas las columnas fueron agregadas correctamente")
            logger.info(f"  - available_filters: {'Presente' if 'available_filters' in columns else 'FALTA'}")
            logger.info(f"  - embed_type: {'Presente' if 'embed_type' in columns else 'FALTA'}")
            return True
        else:
            logger.error(f"✗ Faltan columnas: {', '.join(missing_columns)}")
            return False

    except Error as e:
        logger.error(f"Error al verificar migración: {str(e)}")
        if connection and connection.is_connected():
            connection.close()
        return False


if __name__ == '__main__':
    logger.info("SCRIPT DE MIGRACIÓN - PowerBI Filters")
    logger.info("=" * 50)

    # Ejecutar migración
    migration_success = run_migration()

    # Verificar migración
    verification_success = verify_migration()

    if migration_success and verification_success:
        logger.info("\n" + "=" * 50)
        logger.info("MIGRACIÓN FINALIZADA EXITOSAMENTE")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 50)
        logger.error("MIGRACIÓN FINALIZADA CON ERRORES")
        logger.error("=" * 50)
        sys.exit(1)
