import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Crea y retorna una conexión a la base de datos MySQL"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=None):
    """
    Ejecuta una query y retorna resultados

    Args:
        query: SQL query a ejecutar
        params: Parámetros para la query
        fetch: Si debe hacer fetch de resultados. Si es None, se detecta automáticamente

    Returns:
        - Para SELECT: lista de resultados (dict)
        - Para INSERT/UPDATE/DELETE: lastrowid o None
    """
    connection = get_db_connection()
    if connection is None:
        return None

    try:
        # Usar buffered=True para evitar "Unread result found"
        cursor = connection.cursor(dictionary=True, buffered=True)

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Auto-detectar si es SELECT si no se especificó fetch
        if fetch is None:
            fetch = query.strip().upper().startswith('SELECT')

        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        print(f"Error al ejecutar query: {e}")
        connection.rollback()
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def execute_many(query, data):
    """Ejecuta múltiples inserts"""
    connection = get_db_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        cursor.executemany(query, data)
        connection.commit()
        return True
    except Error as e:
        print(f"Error al ejecutar query: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
