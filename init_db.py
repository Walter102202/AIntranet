"""
Script para inicializar la base de datos
Crea las tablas y el usuario inicial
"""
import os
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from config import Config

# Cargar variables de entorno
load_dotenv()

def init_database():
    """Inicializa la base de datos con las tablas y datos iniciales"""
    try:
        # Conectar a MySQL
        connection = mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )

        cursor = connection.cursor()

        print("Conectado a la base de datos")

        # Leer el archivo SQL
        with open('schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Separar las instrucciones SQL
        sql_commands = sql_script.split(';')

        # Ejecutar cada comando
        for command in sql_commands:
            command = command.strip()
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                except mysql.connector.Error as e:
                    # Ignorar errores de tablas ya existentes
                    if "already exists" not in str(e):
                        print(f"Error ejecutando comando: {e}")

        # Obtener credenciales del usuario inicial desde variables de entorno
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'AIntranet2026%')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@empresa.com')

        # Generar hash de la contraseña del usuario inicial
        password_hash = generate_password_hash(admin_password)

        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (admin_username,))
        user_exists = cursor.fetchone()

        if not user_exists:
            # Insertar usuario inicial con el hash correcto
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, email, nombre_completo, rol, activo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (admin_username, password_hash, admin_email, 'Administrador', 'admin', True))

            user_id = cursor.lastrowid

            # Insertar empleado asociado
            cursor.execute("""
                INSERT INTO empleados (usuario_id, nombre, apellido, email, telefono, extension,
                                     departamento_id, cargo, fecha_ingreso, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, 'Admin', 'Sistema', admin_email, '555-0001', '101',
                  1, 'Administrador de Sistemas', '2024-01-01', True))

            print(f"Usuario '{admin_username}' creado exitosamente")
        else:
            print(f"El usuario '{admin_username}' ya existe")
            # Actualizar la contraseña por si acaso
            cursor.execute("""
                UPDATE usuarios SET password_hash = %s WHERE username = %s
            """, (password_hash, admin_username))
            print("Contraseña actualizada")

        connection.commit()
        print("\n¡Base de datos inicializada correctamente!")
        print("\nUsuario administrador creado/actualizado")
        print("Revisa tu archivo .env para las credenciales")

    except mysql.connector.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexión cerrada")

if __name__ == '__main__':
    init_database()
