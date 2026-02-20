"""
Script de migración para agregar 'tool' al ENUM de la columna 'role'
en la tabla chatbot_messages

Este script:
1. Verifica el schema actual
2. Detecta si 'tool' ya está en el ENUM
3. Si no está, ejecuta la migración
4. Verifica que la migración fue exitosa
"""
import sys
import mysql.connector
from mysql.connector import Error

# ✅ CARGAR .env ANTES DE IMPORTAR Config
from dotenv import load_dotenv
load_dotenv()

from config import Config


def verificar_schema_actual(cursor):
    """Verifica el schema actual de la columna role"""
    print("\n" + "="*60)
    print("PASO 1: Verificando schema actual de chatbot_messages.role")
    print("="*60)

    query = """
        SELECT COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = 'chatbot_messages'
          AND COLUMN_NAME = 'role'
    """

    cursor.execute(query, (Config.DB_CONFIG['database'],))
    result = cursor.fetchone()

    if not result:
        print("❌ ERROR: No se encontró la tabla chatbot_messages o la columna role")
        return None

    column_type = result[0]
    print(f"\n✅ Schema actual de la columna 'role':")
    print(f"   {column_type}")

    # Verificar si 'tool' está en el ENUM
    tiene_tool = "'tool'" in column_type or '"tool"' in column_type

    return {
        'column_type': column_type,
        'tiene_tool': tiene_tool
    }


def ejecutar_migracion(cursor, connection):
    """Ejecuta la migración para agregar 'tool' al ENUM"""
    print("\n" + "="*60)
    print("PASO 2: Ejecutando migración - Agregando 'tool' al ENUM")
    print("="*60)

    try:
        query = """
            ALTER TABLE chatbot_messages
            MODIFY COLUMN role ENUM('user', 'assistant', 'system', 'tool') NOT NULL
        """

        print("\nEjecutando:")
        print(query)

        cursor.execute(query)
        connection.commit()

        print("\n✅ Migración ejecutada exitosamente!")
        return True

    except Error as e:
        print(f"\n❌ Error durante la migración: {e}")
        connection.rollback()
        return False


def verificar_migracion(cursor):
    """Verifica que la migración fue exitosa"""
    print("\n" + "="*60)
    print("PASO 3: Verificando que la migración fue exitosa")
    print("="*60)

    schema_info = verificar_schema_actual(cursor)

    if schema_info and schema_info['tiene_tool']:
        print("\n✅ MIGRACIÓN EXITOSA!")
        print("   La columna 'role' ahora incluye 'tool' en el ENUM")
        return True
    else:
        print("\n❌ MIGRACIÓN FALLÓ!")
        print("   La columna 'role' todavía no tiene 'tool' en el ENUM")
        return False


def main():
    print("="*60)
    print("SCRIPT DE MIGRACIÓN: Agregar 'tool' al ENUM de role")
    print("="*60)

    # Conectar a la base de datos
    try:
        connection = mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )

        cursor = connection.cursor()
        print(f"\n✅ Conectado a la base de datos: {Config.DB_CONFIG['database']}")

        # PASO 1: Verificar schema actual
        schema_info = verificar_schema_actual(cursor)

        if not schema_info:
            print("\n❌ No se pudo verificar el schema. Abortando.")
            return False

        # Verificar si ya tiene 'tool'
        if schema_info['tiene_tool']:
            print("\n⚠️  El ENUM ya incluye 'tool'. No se requiere migración.")
            print("   Si el error persiste, el problema es otro.")
            return True

        # PASO 2: Ejecutar migración
        print("\n⚠️  El ENUM NO incluye 'tool'. Se requiere migración.")
        print("\n¿Deseas continuar con la migración? (s/n): ", end='')

        # Para ejecución automática, comentar las siguientes 3 líneas
        # y descomentar: respuesta = 's'
        respuesta = input().strip().lower()
        if respuesta != 's':
            print("\n❌ Migración cancelada por el usuario.")
            return False

        # Descomentar para ejecución automática:
        # respuesta = 's'

        if not ejecutar_migracion(cursor, connection):
            return False

        # PASO 3: Verificar migración
        if not verificar_migracion(cursor):
            return False

        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\nAhora puedes:")
        print("  1. Reiniciar el servidor Flask si está corriendo")
        print("  2. Probar el análisis de Power BI en el chatbot")
        print("  3. El error 1265 debería estar resuelto")
        print()

        return True

    except Error as e:
        print(f"\n❌ Error de conexión a la base de datos: {e}")
        return False

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔒 Conexión a la base de datos cerrada.")


if __name__ == '__main__':
    exito = main()
    sys.exit(0 if exito else 1)
