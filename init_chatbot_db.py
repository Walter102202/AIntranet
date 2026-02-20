"""
Script para inicializar las tablas del chatbot con IA
Ejecuta este script después de init_db.py para crear las tablas necesarias
"""
import mysql.connector

# ✅ CARGAR .env ANTES DE IMPORTAR Config
from dotenv import load_dotenv
load_dotenv()

from config import Config

def init_chatbot_tables():
    """Crea las tablas necesarias para el chatbot"""

    print("\n" + "="*60)
    print("INICIALIZANDO BASE DE DATOS DEL CHATBOT")
    print("="*60 + "\n")

    try:
        # Conectar a la base de datos
        print("Conectando a la base de datos...")
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = connection.cursor()

        print("✓ Conexión establecida\n")

        # Leer el archivo SQL
        print("Leyendo chatbot_schema.sql...")
        with open('chatbot_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Separar y ejecutar cada comando SQL
        print("Ejecutando comandos SQL...\n")

        # Dividir por punto y coma y filtrar comandos vacíos
        commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]

        for i, command in enumerate(commands, 1):
            if command.upper().startswith('USE'):
                print(f"  [{i}/{len(commands)}] Seleccionando base de datos...")
            elif 'chatbot_sessions' in command:
                print(f"  [{i}/{len(commands)}] Creando tabla chatbot_sessions...")
            elif 'chatbot_messages' in command:
                print(f"  [{i}/{len(commands)}] Creando tabla chatbot_messages...")
            elif 'chatbot_actions' in command:
                print(f"  [{i}/{len(commands)}] Creando tabla chatbot_actions...")
            else:
                print(f"  [{i}/{len(commands)}] Ejecutando comando...")

            cursor.execute(command)

        connection.commit()

        print("\n" + "="*60)
        print("✓ TABLAS DEL CHATBOT CREADAS EXITOSAMENTE")
        print("="*60)

        # Verificar tablas creadas
        print("\nVerificando tablas creadas:")
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME LIKE 'chatbot%%'
            ORDER BY TABLE_NAME
        """, (Config.DB_CONFIG['database'],))

        tables = cursor.fetchall()

        if tables:
            for table in tables:
                print(f"  ✓ {table[0]}")
        else:
            print("  ⚠ No se encontraron tablas del chatbot")

        print("\n" + "="*60)
        print("INICIALIZACIÓN COMPLETADA")
        print("="*60)
        print("\nPróximos pasos:")
        print("1. Configura tu API key del LLM:")
        print("   - Crea un archivo .env")
        print("   - Agrega: LLM_API_KEY=tu-api-key-aqui")
        print("\n2. Inicia el servidor:")
        print("   python app.py")
        print("\n3. Consulta la documentación:")
        print("   chatbot_documentation.md")
        print("="*60 + "\n")

    except mysql.connector.Error as err:
        print(f"\n✗ Error de MySQL: {err}")
        print("\nAsegúrate de que:")
        print("  - El servidor MySQL está corriendo")
        print("  - Las credenciales en config.py son correctas")
        print("  - La base de datos existe (ejecuta init_db.py primero)")
        return False

    except FileNotFoundError:
        print("\n✗ Error: No se encontró el archivo chatbot_schema.sql")
        print("Asegúrate de estar en el directorio correcto del proyecto")
        return False

    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

    return True


if __name__ == '__main__':
    import sys

    # Preguntar confirmación
    print("\nEste script creará las tablas necesarias para el chatbot con IA.")
    print(f"Base de datos: {Config.DB_CONFIG['database']}")
    print(f"Host: {Config.DB_CONFIG['host']}")

    respuesta = input("\n¿Deseas continuar? (s/n): ")

    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        success = init_chatbot_tables()
        sys.exit(0 if success else 1)
    else:
        print("\nOperación cancelada.")
        sys.exit(0)
