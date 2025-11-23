#!/usr/bin/env python3
"""
Tests unitarios para la funcionalidad de filtros en PowerBI
Valida la construcción de URLs, aplicación de filtros y compatibilidad con sistema existente
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.chatbot.screenshot_service import ScreenshotService
import unittest


class TestPowerBIFilters(unittest.TestCase):
    """Tests para funcionalidad de filtros de PowerBI"""

    def test_build_filter_expression_string(self):
        """Test: Construcción de expresión de filtro con string"""
        result = ScreenshotService._build_filter_expression("Ventas", "Región", "Norte", "eq")
        expected = "Ventas/Región eq 'Norte'"
        self.assertEqual(result, expected)

    def test_build_filter_expression_number(self):
        """Test: Construcción de expresión de filtro con número"""
        result = ScreenshotService._build_filter_expression("Datos", "Monto", 1000, "gt")
        expected = "Datos/Monto gt 1000"
        self.assertEqual(result, expected)

    def test_build_filter_expression_boolean(self):
        """Test: Construcción de expresión de filtro con booleano"""
        result = ScreenshotService._build_filter_expression("Config", "Activo", True, "eq")
        expected = "Config/Activo eq true"
        self.assertEqual(result, expected)

    def test_build_filter_expression_list(self):
        """Test: Construcción de expresión de filtro con lista (operador IN)"""
        result = ScreenshotService._build_filter_expression(
            "Calendario", "Mes", ["Enero", "Febrero", "Marzo"], "in"
        )
        expected = "Calendario/Mes in ('Enero', 'Febrero', 'Marzo')"
        self.assertEqual(result, expected)

    def test_build_filter_expression_special_chars(self):
        """Test: Construcción de expresión de filtro con caracteres especiales"""
        result = ScreenshotService._build_filter_expression("Producto", "Nombre", "O'Reilly's Book", "eq")
        expected = "Producto/Nombre eq 'O''Reilly''s Book'"
        self.assertEqual(result, expected)

    def test_build_powerbi_filter_url_simple(self):
        """Test: Construcción de URL con filtro simple"""
        base_url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {"Mes": "Marzo"}

        result = ScreenshotService.build_powerbi_filter_url(base_url, filters)

        # Verificar que contiene el filtro
        self.assertIn("&filter=", result)
        self.assertIn("Mes", result)
        self.assertIn("Marzo", result)

    def test_build_powerbi_filter_url_multiple(self):
        """Test: Construcción de URL con múltiples filtros"""
        base_url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {
            "Mes": "Marzo",
            "Región": "Norte"
        }

        result = ScreenshotService.build_powerbi_filter_url(base_url, filters)

        # Verificar que contiene ambos filtros unidos con AND
        self.assertIn("&filter=", result)
        self.assertIn("Mes", result)
        self.assertIn("Marzo", result)
        self.assertIn("and", result)
        self.assertIn("Región", result)
        self.assertIn("Norte", result)

    def test_build_powerbi_filter_url_complex(self):
        """Test: Construcción de URL con filtro complejo (formato completo)"""
        base_url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {
            "Ventas": {
                "table": "Datos",
                "column": "Monto",
                "value": 1000,
                "operator": "gt"
            }
        }

        result = ScreenshotService.build_powerbi_filter_url(base_url, filters)

        # Verificar estructura
        self.assertIn("&filter=", result)
        self.assertIn("Datos/Monto", result)
        self.assertIn("gt", result)
        self.assertIn("1000", result)

    def test_build_powerbi_filter_url_no_params(self):
        """Test: Construcción de URL sin parámetros existentes"""
        base_url = "https://app.powerbi.com/reportEmbed"
        filters = {"Mes": "Marzo"}

        result = ScreenshotService.build_powerbi_filter_url(base_url, filters)

        # Verificar que agrega ? en lugar de &
        self.assertIn("?filter=", result)

    def test_build_powerbi_filter_url_error_handling(self):
        """Test: Manejo de errores en construcción de URL"""
        base_url = "https://app.powerbi.com/reportEmbed"
        filters = None  # Esto debería causar un error pero ser manejado

        try:
            result = ScreenshotService.build_powerbi_filter_url(base_url, filters)
            # Si no hay error, debería retornar la URL original
            self.assertEqual(result, base_url)
        except Exception as e:
            self.fail(f"No debería lanzar excepción: {str(e)}")

    def test_parse_filters_from_metadata(self):
        """Test: Parseo de metadatos de filtros desde JSON"""
        metadata = {
            "Mes": {
                "table": "Calendario",
                "column": "NombreMes",
                "values": ["Enero", "Febrero", "Marzo"],
                "type": "string"
            },
            "Región": {
                "table": "Geografía",
                "column": "Región",
                "values": ["Norte", "Sur", "Este", "Oeste"],
                "type": "string"
            }
        }

        result = ScreenshotService.parse_filters_from_metadata(metadata)

        # Verificar estructura
        self.assertIn("Mes", result)
        self.assertIn("Región", result)
        self.assertEqual(result["Mes"]["table"], "Calendario")
        self.assertEqual(result["Mes"]["column"], "NombreMes")
        self.assertEqual(len(result["Mes"]["available_values"]), 3)

    def test_parse_filters_from_metadata_empty(self):
        """Test: Parseo de metadatos vacíos"""
        result = ScreenshotService.parse_filters_from_metadata(None)
        self.assertEqual(result, {})

        result = ScreenshotService.parse_filters_from_metadata({})
        self.assertEqual(result, {})

    def test_multiple_operators(self):
        """Test: Diferentes operadores de comparación"""
        operators = {
            "eq": ("Ventas/Monto eq 100", 100),
            "ne": ("Ventas/Monto ne 100", 100),
            "gt": ("Ventas/Monto gt 100", 100),
            "lt": ("Ventas/Monto lt 100", 100),
            "ge": ("Ventas/Monto ge 100", 100),
            "le": ("Ventas/Monto le 100", 100),
        }

        for operator, (expected, value) in operators.items():
            with self.subTest(operator=operator):
                result = ScreenshotService._build_filter_expression("Ventas", "Monto", value, operator)
                self.assertEqual(result, expected)

    def test_backward_compatibility(self):
        """Test: Compatibilidad con versión anterior (sin filtros)"""
        # Simular llamada sin filtros (como antes)
        base_url = "https://app.powerbi.com/reportEmbed?reportId=123"

        # Llamar con filters=None debería funcionar igual que antes
        result = ScreenshotService.build_powerbi_filter_url(base_url, None)
        self.assertEqual(result, base_url)

        # También probando con dict vacío
        result = ScreenshotService.build_powerbi_filter_url(base_url, {})
        self.assertEqual(result, base_url)


class TestPowerBIIntegration(unittest.TestCase):
    """Tests de integración para validar que no se rompió funcionalidad existente"""

    def test_capture_powerbi_report_signature(self):
        """Test: Validar que la firma del método capture_powerbi_report sigue siendo compatible"""
        import inspect

        # Obtener firma del método
        sig = inspect.signature(ScreenshotService.capture_powerbi_report)
        params = list(sig.parameters.keys())

        # Verificar que los parámetros originales siguen existiendo
        self.assertIn('embed_url', params)
        self.assertIn('width', params)
        self.assertIn('height', params)
        self.assertIn('wait_time', params)

        # Verificar que el nuevo parámetro existe
        self.assertIn('filters', params)

        # Verificar que filters tiene valor por defecto None (opcional)
        self.assertEqual(sig.parameters['filters'].default, None)

    def test_filter_url_construction_real_scenario(self):
        """Test: Escenario real de construcción de URL con filtros"""
        # Escenario: Dashboard de ventas con filtros de mes y región
        base_url = "https://app.powerbi.com/reportEmbed?reportId=abc123&groupId=xyz789"

        filters = {
            "Mes": {
                "table": "Calendario",
                "column": "NombreMes",
                "value": "Marzo",
                "operator": "eq"
            },
            "Región": {
                "table": "Geografía",
                "column": "NombreRegión",
                "value": "Norte",
                "operator": "eq"
            }
        }

        result = ScreenshotService.build_powerbi_filter_url(base_url, filters)

        # Verificar que la URL es válida
        self.assertTrue(result.startswith("https://"))
        self.assertIn("reportId=abc123", result)
        self.assertIn("groupId=xyz789", result)
        self.assertIn("&filter=", result)
        self.assertIn("Calendario/NombreMes eq 'Marzo'", result)
        self.assertIn("and", result)
        self.assertIn("Geografía/NombreRegión eq 'Norte'", result)


def run_tests():
    """Ejecuta todos los tests y genera reporte"""
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestPowerBIFilters))
    suite.addTests(loader.loadTestsFromTestCase(TestPowerBIIntegration))

    # Ejecutar tests con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retornar código de salida
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    print("=" * 70)
    print("TESTS UNITARIOS - FUNCIONALIDAD DE FILTROS EN POWERBI")
    print("=" * 70)
    print()

    exit_code = run_tests()

    print()
    print("=" * 70)
    if exit_code == 0:
        print("✓ TODOS LOS TESTS PASARON EXITOSAMENTE")
    else:
        print("✗ ALGUNOS TESTS FALLARON")
    print("=" * 70)

    sys.exit(exit_code)
