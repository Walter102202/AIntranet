import logging
from mysql.connector import Error
from mysql.connector import pooling
from config import Config

logger = logging.getLogger(__name__)

# Pool de conexiones compartido para toda la aplicación
_connection_pool = None


def _get_pool():
    """Obtiene o crea el pool de conexiones (singleton)"""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="intranet_pool",
                pool_size=10,
                pool_reset_session=True,
                host=Config.DB_CONFIG['host'],
                user=Config.DB_CONFIG['user'],
                password=Config.DB_CONFIG['password'],
                database=Config.DB_CONFIG['database']
            )
            logger.info("Pool de conexiones MySQL inicializado (tamaño: 10)")
        except Error as e:
            logger.error(f"Error al crear pool de conexiones MySQL: {e}")
            return None
    return _connection_pool


def get_db_connection():
    """Obtiene una conexión del pool de conexiones"""
    pool = _get_pool()
    if pool is None:
        return None
    try:
        connection = pool.get_connection()
        return connection
    except Error as e:
        logger.error(f"Error al obtener conexión del pool: {e}")
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
        logger.error(f"Error al ejecutar query: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Query: {query[:200]}...")
            if params:
                logger.debug(f"Params: {len(params)} parámetros")
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
        logger.error(f"Error al ejecutar query múltiple: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
