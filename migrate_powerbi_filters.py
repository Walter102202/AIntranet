#!/usr/bin/env python3
"""
Script de migración para agregar soporte de filtros a PowerBI Reports
Ejecuta las migraciones SQL necesarias en la base de datos
"""

import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from database import execute_query
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_migration():
    """Ejecuta la migración para agregar columnas de filtros"""

    logger.info("=== Iniciando migración de PowerBI Reports ===")

    migrations = [
        {
            'name': 'Agregar columna available_filters',
            'sql': """
                ALTER TABLE powerbi_reports
                ADD COLUMN IF NOT EXISTS available_filters JSON DEFAULT NULL
                COMMENT 'Metadatos de filtros disponibles en formato JSON'
            """
        },
        {
            'name': 'Agregar columna embed_type',
            'sql': """
                ALTER TABLE powerbi_reports
                ADD COLUMN IF NOT EXISTS embed_type ENUM('public', 'embedded') DEFAULT 'public'
                COMMENT 'Tipo de URL de PowerBI: public o embedded'
            """
        },
        {
            'name': 'Crear índice para embed_type',
            'sql': """
                CREATE INDEX IF NOT EXISTS idx_powerbi_embed_type
                ON powerbi_reports(embed_type)
            """
        }
    ]

    success_count = 0
    error_count = 0

    for migration in migrations:
        try:
            logger.info(f"Ejecutando: {migration['name']}")
            execute_query(migration['sql'])
            logger.info(f"✓ {migration['name']} - ÉXITO")
            success_count += 1
        except Exception as e:
            logger.error(f"✗ {migration['name']} - ERROR: {str(e)}")
            error_count += 1

    logger.info("\n=== Resumen de Migración ===")
    logger.info(f"Total de migraciones: {len(migrations)}")
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

    try:
        # Verificar estructura de tabla
        query = """
            DESCRIBE powerbi_reports
        """
        result = execute_query(query, fetch=True)

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

    except Exception as e:
        logger.error(f"Error al verificar migración: {str(e)}")
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
