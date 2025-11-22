"""
Servicio para capturar screenshots de reportes PowerBI
Usa Playwright para navegación headless y renderizado completo
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import base64
from io import BytesIO
from PIL import Image
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreenshotService:
    """Captura screenshots de URLs (PowerBI iframes)"""

    @staticmethod
    def capture_powerbi_report(embed_url: str, width: int = 1920, height: int = 1080, wait_time: int = 8000) -> str:
        """
        Captura screenshot de un reporte PowerBI embebido

        PowerBI carga dinámicamente los gráficos usando JavaScript, por lo que
        necesitamos esperar a que todos los elementos se rendericen completamente.

        Args:
            embed_url: URL del iframe de PowerBI (URL pública del reporte compartido)
            width: Ancho del viewport en píxeles (default: 1920)
            height: Alto del viewport en píxeles (default: 1080)
            wait_time: Tiempo de espera adicional en ms para que cargue PowerBI (default: 8000)

        Returns:
            str: Imagen en formato base64 (sin el prefijo data:image/png;base64,)

        Raises:
            Exception: Si no se puede capturar el screenshot
        """
        logger.info(f"Iniciando captura de screenshot para: {embed_url[:50]}...")

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
