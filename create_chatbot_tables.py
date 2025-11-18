"""
Script para crear las tablas del chatbot en la base de datos
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def create_tables():
    """Crea las tablas del chatbot en la base de datos"""
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'intranet_db')
        )

        cursor = conn.cursor()

        print("Conectado a la base de datos")
        print(f"Base de datos: {os.getenv('DB_NAME', 'intranet_db')}")
        print("-" * 50)

        # Leer el schema SQL
        with open('chatbot_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Ejecutar cada statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]

        for statement in statements:
            # Saltar comentarios y USE
            if statement.startswith('--') or statement.startswith('USE'):
                continue

            try:
                cursor.execute(statement)
                # Extraer nombre de tabla del CREATE TABLE
                if 'CREATE TABLE' in statement:
                    table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                    print(f'✅ Tabla creada/verificada: {table_name}')
            except mysql.connector.Error as e:
                print(f'❌ Error al ejecutar statement: {e}')
                print(f'   Statement: {statement[:100]}...')

        conn.commit()

        # Verificar tablas creadas
        cursor.execute("SHOW TABLES LIKE 'chatbot_%'")
        tables = cursor.fetchall()

        print("-" * 50)
        print(f"✅ Total de tablas del chatbot: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")

        cursor.close()
        conn.close()

        print("\n✅ ¡Proceso completado exitosamente!")
        return True

    except mysql.connector.Error as e:
        print(f"\n❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_tables()
