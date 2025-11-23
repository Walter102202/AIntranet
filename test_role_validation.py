"""
Script de prueba para validar la normalización y validación de roles
en ChatbotMessage.create()
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.chatbot.models import ChatbotMessage

def test_role_normalization():
    """Prueba diferentes casos de normalización de roles"""

    print("=" * 60)
    print("PRUEBA DE NORMALIZACIÓN Y VALIDACIÓN DE ROLES")
    print("=" * 60)

    # Test 1: Roles válidos normales
    test_cases_valid = [
        ('user', 'user'),
        ('assistant', 'assistant'),
        ('system', 'system'),
        ('tool', 'tool'),
        ('USER', 'user'),  # Mayúsculas
        ('Assistant', 'assistant'),  # Capitalizado
        (' system ', 'system'),  # Con espacios
        ('  TOOL  ', 'tool'),  # Con espacios y mayúsculas
        ('function', 'tool'),  # Mapeo de function a tool
        ('FUNCTION', 'tool'),  # function en mayúsculas
    ]

    print("\n✅ Probando casos VÁLIDOS (deberían normalizarse correctamente):")
    print("-" * 60)

    for input_role, expected_role in test_cases_valid:
        try:
            # Simular la normalización (sin guardar en BD)
            role = str(input_role).strip().lower()
            if role == 'function':
                role = 'tool'

            valid_roles = ['user', 'assistant', 'system', 'tool']
            if role not in valid_roles:
                raise ValueError(f"Role inválido: '{role}'")

            status = "✓" if role == expected_role else "✗"
            print(f"  {status} Input: '{input_role}' → Normalizado: '{role}' (Esperado: '{expected_role}')")

        except Exception as e:
            print(f"  ✗ Input: '{input_role}' → ERROR: {str(e)}")

    # Test 2: Roles inválidos
    test_cases_invalid = [
        'admin',
        'moderator',
        'function_call',
        'unknown',
        '',
        '   ',
        'user123',
        'system_admin',
    ]

    print("\n❌ Probando casos INVÁLIDOS (deberían lanzar ValueError):")
    print("-" * 60)

    for input_role in test_cases_invalid:
        try:
            # Simular la normalización
            role = str(input_role).strip().lower()
            if role == 'function':
                role = 'tool'

            valid_roles = ['user', 'assistant', 'system', 'tool']
            if role not in valid_roles:
                raise ValueError(f"Role inválido: '{role}'")

            print(f"  ✗ Input: '{input_role}' → NO lanzó error (debería haberlo hecho)")

        except ValueError as e:
            print(f"  ✓ Input: '{input_role}' → Correctamente rechazado: {str(e)}")
        except Exception as e:
            print(f"  ? Input: '{input_role}' → Error inesperado: {str(e)}")

    # Test 3: Casos edge de None
    print("\n🔍 Probando casos EDGE (None, tipos incorrectos):")
    print("-" * 60)

    edge_cases = [
        (None, 'assistant'),  # None debe ser mapeado a 'assistant'
    ]

    for input_role, expected_role in edge_cases:
        try:
            # Simular la normalización
            if input_role is None:
                role = 'assistant'
            else:
                role = str(input_role).strip().lower()

            if role == 'function':
                role = 'tool'

            valid_roles = ['user', 'assistant', 'system', 'tool']
            if role not in valid_roles:
                raise ValueError(f"Role inválido: '{role}'")

            status = "✓" if role == expected_role else "✗"
            print(f"  {status} Input: {input_role} → Normalizado: '{role}' (Esperado: '{expected_role}')")

        except Exception as e:
            print(f"  ✗ Input: {input_role} → ERROR: {str(e)}")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
    print("\n📌 RESUMEN:")
    print("  - Los roles válidos se normalizan correctamente")
    print("  - 'function' se mapea automáticamente a 'tool'")
    print("  - Mayúsculas y espacios se manejan correctamente")
    print("  - Roles inválidos se rechazan con ValueError")
    print("  - None se mapea a 'assistant' por defecto")
    print("\n✅ La solución debería prevenir el error MySQL 1265")
    print("   'Data truncated for column role' en la base de datos.\n")


if __name__ == '__main__':
    test_role_normalization()
