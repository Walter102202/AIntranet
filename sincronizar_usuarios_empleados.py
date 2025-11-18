"""
Script para sincronizar usuarios con empleados
Crea registros de empleados para usuarios que no los tienen
"""
import mysql.connector
from config import Config
from datetime import date

def sincronizar_usuarios_empleados():
    """Sincroniza usuarios activos con la tabla de empleados"""
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )

        cursor = connection.cursor(dictionary=True)

        print("=== Sincronización de Usuarios y Empleados ===\n")

        # Obtener todos los usuarios activos
        cursor.execute("""
            SELECT id, username, email, nombre_completo, rol
            FROM usuarios
            WHERE activo = TRUE
        """)
        usuarios = cursor.fetchall()

        print(f"Total de usuarios activos: {len(usuarios)}\n")

        empleados_creados = 0

        for usuario in usuarios:
            # Verificar si el usuario ya tiene un empleado asociado
            cursor.execute("""
                SELECT id FROM empleados WHERE usuario_id = %s
            """, (usuario['id'],))
            empleado_existente = cursor.fetchone()

            if not empleado_existente:
                # Separar nombre completo en nombre y apellido
                nombre_completo = usuario['nombre_completo'].split()
                if len(nombre_completo) >= 2:
                    nombre = nombre_completo[0]
                    apellido = ' '.join(nombre_completo[1:])
                else:
                    nombre = usuario['nombre_completo']
                    apellido = ''

                # Determinar departamento según el rol
                if usuario['rol'] == 'admin':
                    departamento_id = 1  # Tecnología
                    cargo = 'Administrador de Sistemas'
                elif usuario['rol'] == 'rrhh':
                    departamento_id = 2  # Recursos Humanos
                    cargo = 'Especialista de RRHH'
                elif usuario['rol'] == 'soporte':
                    departamento_id = 1  # Tecnología
                    cargo = 'Técnico de Soporte'
                else:  # empleado
                    departamento_id = 4  # Operaciones
                    cargo = 'Empleado'

                # Crear registro de empleado
                cursor.execute("""
                    INSERT INTO empleados (
                        usuario_id, nombre, apellido, email, telefono, extension,
                        departamento_id, cargo, fecha_ingreso, activo
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    usuario['id'],
                    nombre,
                    apellido,
                    usuario['email'],
                    '555-0000',  # Teléfono por defecto
                    '100',       # Extensión por defecto
                    departamento_id,
                    cargo,
                    date.today(),
                    True
                ))

                print(f"✓ Empleado creado para usuario: {usuario['username']} ({usuario['nombre_completo']})")
                print(f"  - Cargo: {cargo}")
                print(f"  - Departamento ID: {departamento_id}\n")

                empleados_creados += 1
            else:
                print(f"○ Usuario {usuario['username']} ya tiene empleado asociado (ID: {empleado_existente['id']})")

        connection.commit()

        print(f"\n=== Resumen ===")
        print(f"Usuarios activos: {len(usuarios)}")
        print(f"Empleados creados: {empleados_creados}")
        print(f"\n¡Sincronización completada!")

    except mysql.connector.Error as e:
        print(f"Error en la base de datos: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexión cerrada")

if __name__ == '__main__':
    sincronizar_usuarios_empleados()
