"""
Servicio para capturar screenshots de reportes PowerBI
Usa Playwright para navegación headless y renderizado completo
Soporta aplicación de filtros mediante parámetros URL
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import base64
from io import BytesIO
from PIL import Image
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreenshotService:
    """Captura screenshots de URLs (PowerBI iframes) con soporte para filtros"""

    @staticmethod
    def capture_powerbi_report(
        embed_url: str,
        width: int = 1920,
        height: int = 1080,
        wait_time: int = 8000,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Captura screenshot de un reporte PowerBI embebido con filtros opcionales

        PowerBI carga dinámicamente los gráficos usando JavaScript, por lo que
        necesitamos esperar a que todos los elementos se rendericen completamente.

        Args:
            embed_url: URL del iframe de PowerBI (URL pública o embedded)
            width: Ancho del viewport en píxeles (default: 1920)
            height: Alto del viewport en píxeles (default: 1080)
            wait_time: Tiempo de espera adicional en ms para que cargue PowerBI (default: 8000)
            filters: Diccionario de filtros a aplicar (default: None)
                Formato: {
                    "NombreFiltro": "Valor",  # Formato simple
                    o
                    "NombreFiltro": {
                        "table": "NombreTabla",
                        "column": "NombreColumna",
                        "value": "Valor",
                        "operator": "eq"  # eq, ne, gt, lt, ge, le, in
                    }
                }

        Returns:
            str: Imagen en formato base64 (sin el prefijo data:image/png;base64,)

        Raises:
            Exception: Si no se puede capturar el screenshot
        """
        # Aplicar filtros a la URL si se proporcionan
        if filters:
            logger.info(f"Aplicando filtros: {filters}")
            embed_url = ScreenshotService.build_powerbi_filter_url(embed_url, filters)

        logger.info(f"Iniciando captura de screenshot para: {embed_url[:80]}...")

        try:
            with sync_playwright() as p:
                # Lanzar navegador headless
                logger.info("Lanzando navegador Chromium...")
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu'
                    ]
                )

                # Crear contexto con viewport específico
                context = browser.new_context(
                    viewport={'width': width, 'height': height},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

                # Crear nueva página
                page = context.new_page()

                logger.info("Navegando a la URL del reporte...")

                # Navegar a la URL del reporte PowerBI
                # PowerBI puede tardar en cargar, esperamos a que se complete la red
                try:
                    page.goto(embed_url, wait_until='networkidle', timeout=30000)
                    logger.info("Página cargada, esperando renderizado de gráficos...")
                except PlaywrightTimeoutError:
                    logger.warning("Timeout en networkidle, continuando con load...")
                    page.goto(embed_url, wait_until='load', timeout=30000)

                # Esperar a que los elementos de PowerBI se rendericen
                # PowerBI usa iframes y canvas, necesitamos tiempo adicional
                page.wait_for_timeout(wait_time)

                # Intentar detectar si hay elementos de PowerBI cargados
                try:
                    # PowerBI usa elementos con estas clases comunes
                    page.wait_for_selector('iframe, canvas, svg, [class*="visual"]', timeout=5000)
                    logger.info("Elementos de PowerBI detectados")
                except PlaywrightTimeoutError:
                    logger.warning("No se detectaron elementos específicos de PowerBI, capturando de todos modos...")

                # Scroll para asegurar lazy-loading de imágenes
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                page.evaluate('window.scrollTo(0, 0)')
                page.wait_for_timeout(500)

                logger.info("Capturando screenshot...")

                # Capturar screenshot en alta calidad
                screenshot_bytes = page.screenshot(
                    full_page=True,  # Captura toda la página
                    type='png',       # Formato PNG (mejor calidad)
                    scale='device'    # Escala del dispositivo
                )

                logger.info(f"Screenshot capturado exitosamente ({len(screenshot_bytes)} bytes)")

                # Cerrar navegador
                browser.close()

                # Optimizar imagen si es muy grande (reducir tamaño para API)
                screenshot_base64 = ScreenshotService._optimize_image(screenshot_bytes)

                logger.info("Screenshot procesado y convertido a base64")
                return screenshot_base64

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout al cargar el reporte: {str(e)}")
            raise Exception(f"El reporte tardó demasiado en cargar. Verifica que la URL sea accesible: {str(e)}")
        except Exception as e:
            logger.error(f"Error capturando screenshot: {str(e)}", exc_info=True)
            raise Exception(f"No se pudo capturar el reporte: {str(e)}")

    @staticmethod
    def _optimize_image(image_bytes: bytes, max_size_mb: float = 5.0, quality: int = 85) -> str:
        """
        Optimiza una imagen para reducir su tamaño si es necesario

        La API de OpenAI tiene límites de payload, por lo que es importante
        optimizar las imágenes grandes.

        Args:
            image_bytes: Bytes de la imagen original
            max_size_mb: Tamaño máximo en MB (default: 5.0)
            quality: Calidad de compresión JPEG si es necesario (default: 85)

        Returns:
            str: Imagen optimizada en base64
        """
        try:
            # Convertir a PIL Image
            image = Image.open(BytesIO(image_bytes))

            # Calcular tamaño actual en MB
            current_size_mb = len(image_bytes) / (1024 * 1024)

            logger.info(f"Tamaño de imagen original: {current_size_mb:.2f} MB ({image.size[0]}x{image.size[1]})")

            # Si la imagen es pequeña, retornar directamente
            if current_size_mb <= max_size_mb:
                logger.info("Imagen dentro del límite, no se requiere optimización")
                return base64.b64encode(image_bytes).decode('utf-8')

            logger.info(f"Imagen excede {max_size_mb} MB, optimizando...")

            # Reducir tamaño si es necesario
            # Calcular ratio de reducción
            ratio = (max_size_mb / current_size_mb) ** 0.5  # Raíz cuadrada porque área = width * height
            new_width = int(image.size[0] * ratio * 0.9)  # 0.9 para margen de seguridad
            new_height = int(image.size[1] * ratio * 0.9)

            logger.info(f"Redimensionando a {new_width}x{new_height}")

            # Redimensionar con antialiasing de alta calidad
            image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convertir a RGB si es necesario (para JPEG)
            if image_resized.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image_resized.size, (255, 255, 255))
                if image_resized.mode == 'P':
                    image_resized = image_resized.convert('RGBA')
                background.paste(image_resized, mask=image_resized.split()[-1] if image_resized.mode == 'RGBA' else None)
                image_resized = background

            # Guardar optimizada
            output_buffer = BytesIO()
            image_resized.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            optimized_bytes = output_buffer.getvalue()

            optimized_size_mb = len(optimized_bytes) / (1024 * 1024)
            logger.info(f"Imagen optimizada: {optimized_size_mb:.2f} MB (reducción del {((current_size_mb - optimized_size_mb) / current_size_mb * 100):.1f}%)")

            return base64.b64encode(optimized_bytes).decode('utf-8')

        except Exception as e:
            logger.warning(f"Error al optimizar imagen, usando original: {str(e)}")
            # Si falla la optimización, retornar imagen original
            return base64.b64encode(image_bytes).decode('utf-8')

    @staticmethod
    def build_powerbi_filter_url(embed_url: str, filters: Dict[str, Any]) -> str:
        """
        Construye una URL de PowerBI con filtros aplicados

        PowerBI soporta filtros mediante parámetros URL usando sintaxis OData.
        Formato: &filter=TableName/ColumnName eq 'Value'

        Args:
            embed_url: URL original del reporte PowerBI
            filters: Diccionario de filtros a aplicar

        Returns:
            str: URL con filtros aplicados

        Examples:
            >>> filters = {"Mes": "Marzo", "Región": "Norte"}
            >>> build_powerbi_filter_url(url, filters)
            'url?...&filter=Mes eq 'Marzo' and Región eq 'Norte''

            >>> filters = {"Ventas": {"table": "Datos", "column": "Monto", "value": 1000, "operator": "gt"}}
            >>> build_powerbi_filter_url(url, filters)
            'url?...&filter=Datos/Monto gt 1000'
        """
        try:
            # Construir expresión de filtro OData
            filter_expressions = []

            for filter_name, filter_config in filters.items():
                # Determinar formato del filtro
                if isinstance(filter_config, dict):
                    # Formato completo con tabla, columna, valor, operador
                    table = filter_config.get('table', filter_name)
                    column = filter_config.get('column', filter_name)
                    value = filter_config.get('value')
                    operator = filter_config.get('operator', 'eq')
                else:
                    # Formato simple: solo valor (inferir tabla/columna del nombre)
                    table = filter_name
                    column = filter_name
                    value = filter_config
                    operator = 'eq'

                # Construir expresión
                filter_expr = ScreenshotService._build_filter_expression(
                    table, column, value, operator
                )
                filter_expressions.append(filter_expr)

            # Combinar todas las expresiones con AND
            combined_filter = ' and '.join(filter_expressions)

            # Agregar filtro a la URL
            # PowerBI requiere que el filtro esté en el formato correcto
            if '?' in embed_url:
                # Ya tiene parámetros, agregar con &
                filtered_url = f"{embed_url}&filter={combined_filter}"
            else:
                # No tiene parámetros, agregar con ?
                filtered_url = f"{embed_url}?filter={combined_filter}"

            logger.info(f"URL con filtros construida: {filtered_url[:120]}...")
            return filtered_url

        except Exception as e:
            logger.error(f"Error construyendo URL con filtros: {str(e)}")
            # En caso de error, retornar URL original
            logger.warning("Usando URL original sin filtros debido al error")
            return embed_url

    @staticmethod
    def _build_filter_expression(table: str, column: str, value: Any, operator: str = 'eq') -> str:
        """
        Construye una expresión de filtro individual en sintaxis OData

        Args:
            table: Nombre de la tabla
            column: Nombre de la columna
            value: Valor a filtrar
            operator: Operador de comparación (eq, ne, gt, lt, ge, le, in)

        Returns:
            str: Expresión de filtro en formato OData

        Examples:
            >>> _build_filter_expression("Ventas", "Región", "Norte", "eq")
            "Ventas/Región eq 'Norte'"

            >>> _build_filter_expression("Datos", "Monto", 1000, "gt")
            "Datos/Monto gt 1000"

            >>> _build_filter_expression("Calendario", "Mes", ["Enero", "Febrero"], "in")
            "Calendario/Mes in ('Enero', 'Febrero')"
        """
        # Determinar tipo de valor y formatear apropiadamente
        if operator.lower() == 'in' and isinstance(value, (list, tuple)):
            # Operador IN con lista de valores
            formatted_values = []
            for v in value:
                if isinstance(v, str):
                    # Escapar comillas simples en strings
                    v_escaped = v.replace("'", "''")
                    formatted_values.append(f"'{v_escaped}'")
                else:
                    formatted_values.append(str(v))
            value_str = f"({', '.join(formatted_values)})"
            return f"{table}/{column} {operator} {value_str}"
        elif isinstance(value, str):
            # String: envolver en comillas simples y escapar
            value_escaped = value.replace("'", "''")
            return f"{table}/{column} {operator} '{value_escaped}'"
        elif isinstance(value, bool):
            # Boolean: true/false en minúsculas
            return f"{table}/{column} {operator} {str(value).lower()}"
        elif isinstance(value, (int, float)):
            # Número: sin comillas
            return f"{table}/{column} {operator} {value}"
        elif value is None:
            # Null
            return f"{table}/{column} {operator} null"
        else:
            # Otros tipos: intentar convertir a string
            value_str = str(value).replace("'", "''")
            return f"{table}/{column} {operator} '{value_str}'"

    @staticmethod
    def parse_filters_from_metadata(available_filters: Optional[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Parsea metadatos de filtros disponibles desde la BD

        Args:
            available_filters: JSON con metadatos de filtros del reporte

        Returns:
            Dict con filtros parseados en formato simplificado

        Example:
            >>> metadata = {
            ...     "Mes": {"table": "Calendario", "column": "Nombre", "values": ["Enero", "Febrero"]},
            ...     "Región": {"table": "Geo", "column": "Region", "values": ["Norte", "Sur"]}
            ... }
            >>> parse_filters_from_metadata(metadata)
            {
                "Mes": {
                    "table": "Calendario",
                    "column": "Nombre",
                    "available_values": ["Enero", "Febrero"],
                    "type": "string"
                },
                ...
            }
        """
        if not available_filters:
            return {}

        parsed = {}
        for filter_name, filter_config in available_filters.items():
            if isinstance(filter_config, dict):
                parsed[filter_name] = {
                    'table': filter_config.get('table', filter_name),
                    'column': filter_config.get('column', filter_name),
                    'available_values': filter_config.get('values', []),
                    'type': filter_config.get('type', 'string')
                }
            else:
                # Formato legacy o simple
                parsed[filter_name] = {
                    'table': filter_name,
                    'column': filter_name,
                    'available_values': [],
                    'type': 'string'
                }

        return parsed

    @staticmethod
    def test_capture(url: str = "https://www.example.com") -> bool:
        """
        Función de prueba para verificar que Playwright funciona correctamente

        Args:
            url: URL de prueba (default: example.com)

        Returns:
            bool: True si la captura fue exitosa
        """
        try:
            logger.info(f"Ejecutando prueba de captura en: {url}")
            screenshot = ScreenshotService.capture_powerbi_report(url, width=1280, height=720, wait_time=2000)
            logger.info(f"Prueba exitosa! Screenshot de {len(screenshot)} caracteres en base64")
            return True
        except Exception as e:
            logger.error(f"Prueba fallida: {str(e)}")
            return False
