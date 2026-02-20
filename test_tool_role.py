"""
Script de prueba rápida para verificar que el role='tool' funciona
después de ejecutar la migración
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ✅ CARGAR .env ANTES DE IMPORTAR Config
from dotenv import load_dotenv
load_dotenv()

from modules.chatbot.models import ChatbotMessage, ChatbotSession


def test_insertar_mensaje_tool():
    """Prueba insertar un mensaje con role='tool'"""
    print("="*60)
    print("PRUEBA: Insertar mensaje con role='tool'")
    print("="*60)

    try:
        # Crear una sesión de prueba (o usar una existente)
        # Nota: Esto requiere que tengas al menos un usuario en la BD
        print("\nCreando sesión de prueba...")

        # Usar usuario ID 1 (ajusta si tu usuario tiene otro ID)
        test_user_id = 1
        session = ChatbotSession.get_or_create_session(test_user_id)

        print(f"✅ Sesión creada/obtenida: ID {session['id']}")

        # Intentar insertar un mensaje con role='tool'
        print("\nIntentando insertar mensaje con role='tool'...")

        message_id = ChatbotMessage.create(
            session_id=session['id'],
            role='tool',
            content='Este es un mensaje de prueba con role=tool',
            metadata={'test': True, 'tool_call_id': 'test_call_123'}
        )

        if message_id:
            print(f"✅ ¡ÉXITO! Mensaje con role='tool' insertado con ID: {message_id}")
            print("\n" + "="*60)
            print("✅ LA MIGRACIÓN FUE EXITOSA")
            print("="*60)
            print("\nEl role='tool' ahora funciona correctamente en la BD.")
            print("Puedes proceder a probar el análisis de Power BI.\n")
            return True
        else:
            print("❌ FALLÓ: No se pudo insertar el mensaje (message_id es None)")
            print("\n" + "="*60)
            print("❌ LA MIGRACIÓN NO FUNCIONÓ")
            print("="*60)
            print("\nRecomendaciones:")
            print("  1. Verifica que ejecutaste el script migrate_role_enum.py")
            print("  2. Verifica el schema con: SHOW COLUMNS FROM chatbot_messages LIKE 'role';")
            print("  3. Revisa los logs de error en la consola\n")
            return False

    except ValueError as e:
        if "Role inválido" in str(e):
            print(f"❌ Error de validación en Python: {e}")
            print("\nEsto no debería ocurrir. El código Python considera 'tool' válido.")
            print("Revisa modules/chatbot/models.py\n")
        else:
            print(f"❌ Error inesperado: {e}\n")
        return False

    except Exception as e:
        print(f"❌ Error al insertar mensaje con role='tool': {e}")
        print("\n" + "="*60)
        print("❌ LA MIGRACIÓN NO FUNCIONÓ CORRECTAMENTE")
        print("="*60)
        print("\nRecomendaciones:")
        print("  1. Ejecuta: python migrate_role_enum.py")
        print("  2. Verifica el schema manualmente en MySQL")
        print("  3. Revisa el error anterior para más detalles\n")
        return False


if __name__ == '__main__':
    print("\n🔍 Este script verifica que la migración del ENUM fue exitosa\n")
    exito = test_insertar_mensaje_tool()
    sys.exit(0 if exito else 1)
