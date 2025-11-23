#!/usr/bin/env python3
"""
Tests simples para validar la lógica de construcción de filtros
Sin dependencias externas
"""

import unittest
from typing import Dict, Any, Optional, List


# Copia de la lógica de filtros para testing independiente
def build_filter_expression(table: str, column: str, value: Any, operator: str = 'eq') -> str:
    """
    Construye una expresión de filtro individual en sintaxis OData
    """
    if operator.lower() == 'in' and isinstance(value, (list, tuple)):
        formatted_values = []
        for v in value:
            if isinstance(v, str):
                v_escaped = v.replace("'", "''")
                formatted_values.append(f"'{v_escaped}'")
            else:
                formatted_values.append(str(v))
        value_str = f"({', '.join(formatted_values)})"
        return f"{table}/{column} {operator} {value_str}"
    elif isinstance(value, str):
        value_escaped = value.replace("'", "''")
        return f"{table}/{column} {operator} '{value_escaped}'"
    elif isinstance(value, bool):
        return f"{table}/{column} {operator} {str(value).lower()}"
    elif isinstance(value, (int, float)):
        return f"{table}/{column} {operator} {value}"
    elif value is None:
        return f"{table}/{column} {operator} null"
    else:
        value_str = str(value).replace("'", "''")
        return f"{table}/{column} {operator} '{value_str}'"


def build_powerbi_filter_url(embed_url: str, filters: Dict[str, Any]) -> str:
    """
    Construye una URL de PowerBI con filtros aplicados
    """
    try:
        if not filters:
            return embed_url

        filter_expressions = []

        for filter_name, filter_config in filters.items():
            if isinstance(filter_config, dict):
                table = filter_config.get('table', filter_name)
                column = filter_config.get('column', filter_name)
                value = filter_config.get('value')
                operator = filter_config.get('operator', 'eq')
            else:
                table = filter_name
                column = filter_name
                value = filter_config
                operator = 'eq'

            filter_expr = build_filter_expression(table, column, value, operator)
            filter_expressions.append(filter_expr)

        combined_filter = ' and '.join(filter_expressions)

        if '?' in embed_url:
            filtered_url = f"{embed_url}&filter={combined_filter}"
        else:
            filtered_url = f"{embed_url}?filter={combined_filter}"

        return filtered_url

    except Exception as e:
        return embed_url


class TestFilterLogic(unittest.TestCase):
    """Tests para lógica de construcción de filtros"""

    def test_simple_string_filter(self):
        """Test: Filtro simple con string"""
        result = build_filter_expression("Ventas", "Región", "Norte", "eq")
        self.assertEqual(result, "Ventas/Región eq 'Norte'")
        print("✓ Test filtro string simple: PASÓ")

    def test_numeric_filter(self):
        """Test: Filtro con número"""
        result = build_filter_expression("Datos", "Monto", 1000, "gt")
        self.assertEqual(result, "Datos/Monto gt 1000")
        print("✓ Test filtro numérico: PASÓ")

    def test_boolean_filter(self):
        """Test: Filtro con booleano"""
        result = build_filter_expression("Config", "Activo", True, "eq")
        self.assertEqual(result, "Config/Activo eq true")
        print("✓ Test filtro booleano: PASÓ")

    def test_list_filter(self):
        """Test: Filtro con lista (IN)"""
        result = build_filter_expression("Calendario", "Mes", ["Enero", "Febrero"], "in")
        self.assertEqual(result, "Calendario/Mes in ('Enero', 'Febrero')")
        print("✓ Test filtro con lista: PASÓ")

    def test_special_characters(self):
        """Test: Manejo de caracteres especiales"""
        result = build_filter_expression("Producto", "Nombre", "O'Reilly's", "eq")
        self.assertEqual(result, "Producto/Nombre eq 'O''Reilly''s'")
        print("✓ Test caracteres especiales: PASÓ")

    def test_url_simple_filter(self):
        """Test: URL con filtro simple"""
        url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {"Mes": "Marzo"}
        result = build_powerbi_filter_url(url, filters)

        self.assertIn("&filter=", result)
        self.assertIn("Mes eq 'Marzo'", result)
        print("✓ Test URL con filtro simple: PASÓ")

    def test_url_multiple_filters(self):
        """Test: URL con múltiples filtros"""
        url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {
            "Mes": "Marzo",
            "Región": "Norte"
        }
        result = build_powerbi_filter_url(url, filters)

        self.assertIn("&filter=", result)
        self.assertIn("Mes eq 'Marzo'", result)
        self.assertIn("and", result)
        self.assertIn("Región eq 'Norte'", result)
        print("✓ Test URL con filtros múltiples: PASÓ")

    def test_url_complex_filter(self):
        """Test: URL con filtro complejo"""
        url = "https://app.powerbi.com/reportEmbed?reportId=123"
        filters = {
            "Ventas": {
                "table": "Datos",
                "column": "Monto",
                "value": 1000,
                "operator": "gt"
            }
        }
        result = build_powerbi_filter_url(url, filters)

        self.assertIn("&filter=", result)
        self.assertIn("Datos/Monto gt 1000", result)
        print("✓ Test URL con filtro complejo: PASÓ")

    def test_url_no_params(self):
        """Test: URL sin parámetros existentes"""
        url = "https://app.powerbi.com/reportEmbed"
        filters = {"Mes": "Marzo"}
        result = build_powerbi_filter_url(url, filters)

        self.assertIn("?filter=", result)
        print("✓ Test URL sin parámetros: PASÓ")

    def test_backward_compatibility(self):
        """Test: Compatibilidad con versión anterior (sin filtros)"""
        url = "https://app.powerbi.com/reportEmbed?reportId=123"

        # Sin filtros
        result = build_powerbi_filter_url(url, None)
        self.assertEqual(result, url)

        # Con dict vacío
        result = build_powerbi_filter_url(url, {})
        self.assertEqual(result, url)
        print("✓ Test compatibilidad retroactiva: PASÓ")

    def test_all_operators(self):
        """Test: Todos los operadores de comparación"""
        operators = ["eq", "ne", "gt", "lt", "ge", "le"]
        for op in operators:
            result = build_filter_expression("Ventas", "Monto", 100, op)
            self.assertIn(f"Monto {op} 100", result)
        print(f"✓ Test todos los operadores ({', '.join(operators)}): PASÓ")

    def test_real_world_scenario(self):
        """Test: Escenario real completo"""
        url = "https://app.powerbi.com/reportEmbed?reportId=abc123&groupId=xyz789"
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
            },
            "Ventas": {
                "table": "Datos",
                "column": "MontoVentas",
                "value": 10000,
                "operator": "gt"
            }
        }

        result = build_powerbi_filter_url(url, filters)

        # Verificaciones
        self.assertIn("reportId=abc123", result)
        self.assertIn("groupId=xyz789", result)
        self.assertIn("Calendario/NombreMes eq 'Marzo'", result)
        self.assertIn("Geografía/NombreRegión eq 'Norte'", result)
        self.assertIn("Datos/MontoVentas gt 10000", result)
        self.assertEqual(result.count(" and "), 2)  # Debe haber 2 ANDs (3 filtros)

        print("✓ Test escenario real completo: PASÓ")


if __name__ == '__main__':
    print("=" * 70)
    print("TESTS DE LÓGICA DE FILTROS POWERBI")
    print("=" * 70)
    print()

    # Ejecutar tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFilterLogic)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("RESUMEN:")
    print(f"  Tests ejecutados: {result.testsRun}")
    print(f"  Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Fallidos: {len(result.failures)}")
    print(f"  Errores: {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("\n✓ TODOS LOS TESTS PASARON EXITOSAMENTE\n")
        exit(0)
    else:
        print("\n✗ ALGUNOS TESTS FALLARON\n")
        exit(1)
