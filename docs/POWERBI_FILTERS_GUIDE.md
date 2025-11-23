# Guía de Uso: Filtros en PowerBI para ChatBot

## 📋 Descripción General

Esta funcionalidad permite que el ChatBot aplique **filtros dinámicos** a los reportes de PowerBI antes de analizarlos, permitiendo respuestas más específicas y contextualizadas a las preguntas del usuario.

## 🎯 Características Principales

- ✅ Aplicación de filtros mediante parámetros URL (sintaxis OData de PowerBI)
- ✅ Soporte para múltiples tipos de filtros: strings, números, booleanos, listas
- ✅ Compatibilidad con URLs públicas y embebidas
- ✅ Múltiples operadores: igual, distinto, mayor, menor, en lista, etc.
- ✅ Backward compatible: no rompe funcionalidad existente
- ✅ Nueva herramienta `get_powerbi_report_filters` para explorar filtros disponibles

---

## 🚀 Despliegue e Instalación

### Paso 1: Aplicar Migración de Base de Datos

```bash
# Ejecutar script de migración
python3 migrate_powerbi_filters.py
```

Este script agrega las siguientes columnas a la tabla `powerbi_reports`:
- `available_filters` (JSON): Metadatos de filtros disponibles
- `embed_type` (ENUM): Tipo de URL ('public' o 'embedded')

### Paso 2: Verificar Instalación

```bash
# Ejecutar tests
python3 tests/test_filter_logic.py

# Salida esperada: 12/12 tests PASARON
```

---

## 📖 Cómo Usar los Filtros

### 1. Configurar Filtros Disponibles en un Reporte

Antes de usar filtros, debes configurar qué filtros están disponibles para cada reporte. Esto se hace actualizando el campo `available_filters` en la base de datos.

**Ejemplo de metadatos de filtros:**

```json
{
  "Mes": {
    "table": "Calendario",
    "column": "NombreMes",
    "values": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
    "type": "string"
  },
  "Región": {
    "table": "Geografía",
    "column": "Región",
    "values": ["Norte", "Sur", "Este", "Oeste", "Centro"],
    "type": "string"
  },
  "Año": {
    "table": "Calendario",
    "column": "Año",
    "values": [2022, 2023, 2024, 2025],
    "type": "number"
  },
  "Categoría": {
    "table": "Productos",
    "column": "CategoríaProducto",
    "values": ["Electrónica", "Ropa", "Alimentos", "Hogar"],
    "type": "string"
  }
}
```

**Script Python para actualizar filtros:**

```python
from models import PowerBIReport

# Actualizar filtros de un reporte existente
report_id = 1
filtros = {
    "Mes": {
        "table": "Calendario",
        "column": "NombreMes",
        "values": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
        "type": "string"
    },
    "Región": {
        "table": "Geografía",
        "column": "Región",
        "values": ["Norte", "Sur", "Este", "Oeste"],
        "type": "string"
    }
}

PowerBIReport.update_filters(report_id, filtros)
```

### 2. Usar Filtros desde el ChatBot

El ChatBot detectará automáticamente cuándo aplicar filtros según la pregunta del usuario.

#### Ejemplos de Preguntas del Usuario:

**Ejemplo 1: Filtro Simple**
```
Usuario: "Analiza el dashboard de ventas solo para el mes de marzo"

ChatBot (internamente):
  1. Detecta que necesita analizar un reporte
  2. Identifica que debe filtrar por Mes="Marzo"
  3. Llama a analyze_powerbi_report(report_id=1, filtros={"Mes": "Marzo"})
  4. Captura screenshot con filtro aplicado
  5. Analiza con visión y responde
```

**Ejemplo 2: Filtros Múltiples**
```
Usuario: "Muéstrame las ventas de marzo en la región norte"

ChatBot (internamente):
  - Filtros: {"Mes": "Marzo", "Región": "Norte"}
  - URL generada: ...&filter=Mes eq 'Marzo' and Región eq 'Norte'
```

**Ejemplo 3: Filtro Numérico**
```
Usuario: "Analiza solo las ventas mayores a 10000 en el último trimestre"

ChatBot (internamente):
  - Filtros: {
      "Ventas": {"table": "Datos", "column": "Monto", "value": 10000, "operator": "gt"}
    }
```

### 3. Usar la Nueva Herramienta `get_powerbi_report_filters`

El ChatBot ahora puede consultar qué filtros están disponibles antes de aplicarlos:

```
Usuario: "¿Qué filtros puedo usar en el dashboard de ventas?"

ChatBot (internamente):
  1. Llama a get_powerbi_report_filters(report_id=1)
  2. Recibe lista de filtros disponibles
  3. Responde al usuario con los filtros disponibles

ChatBot: "El dashboard de ventas tiene los siguientes filtros disponibles:
  - Mes: Enero, Febrero, Marzo, ..., Diciembre
  - Región: Norte, Sur, Este, Oeste, Centro
  - Año: 2022, 2023, 2024, 2025"
```

---

## 🛠️ API de Programación

### Método: `ScreenshotService.capture_powerbi_report()`

**Firma actualizada:**

```python
ScreenshotService.capture_powerbi_report(
    embed_url: str,
    width: int = 1920,
    height: int = 1080,
    wait_time: int = 8000,
    filters: Optional[Dict[str, Any]] = None  # NUEVO parámetro
) -> str
```

**Parámetros:**
- `embed_url`: URL del reporte PowerBI (pública o embedded)
- `width`: Ancho del viewport
- `height`: Alto del viewport
- `wait_time`: Tiempo de espera para renderizado (ms)
- `filters`: **NUEVO** - Diccionario de filtros a aplicar

**Ejemplo de uso:**

```python
from modules.chatbot.screenshot_service import ScreenshotService

# Sin filtros (como antes - backward compatible)
screenshot = ScreenshotService.capture_powerbi_report(
    embed_url="https://app.powerbi.com/reportEmbed?reportId=123"
)

# Con filtros simples
screenshot = ScreenshotService.capture_powerbi_report(
    embed_url="https://app.powerbi.com/reportEmbed?reportId=123",
    filters={"Mes": "Marzo", "Región": "Norte"}
)

# Con filtros complejos
screenshot = ScreenshotService.capture_powerbi_report(
    embed_url="https://app.powerbi.com/reportEmbed?reportId=123",
    filters={
        "Ventas": {
            "table": "Datos",
            "column": "MontoVentas",
            "value": 10000,
            "operator": "gt"
        }
    }
)
```

### Herramienta del ChatBot: `analyze_powerbi_report`

**Definición actualizada:**

```json
{
  "name": "analyze_powerbi_report",
  "description": "Analiza visualmente un reporte de Power BI. SOPORTA FILTROS para obtener datos específicos.",
  "parameters": {
    "report_id": "ID del reporte (requerido)",
    "pregunta": "Pregunta específica (opcional)",
    "filtros": "Filtros a aplicar (opcional) - NUEVO"
  }
}
```

**Formato de filtros:**

```python
# Formato simple (recomendado)
filtros = {
    "Mes": "Marzo",
    "Región": "Norte"
}

# Formato completo (avanzado)
filtros = {
    "Ventas": {
        "table": "Datos",
        "column": "MontoVentas",
        "value": 10000,
        "operator": "gt"  # eq, ne, gt, lt, ge, le, in
    }
}
```

### Nueva Herramienta: `get_powerbi_report_filters`

```json
{
  "name": "get_powerbi_report_filters",
  "description": "Obtiene información sobre los filtros disponibles para un reporte",
  "parameters": {
    "report_id": "ID del reporte (requerido)"
  }
}
```

**Ejemplo de respuesta:**

```json
{
  "success": true,
  "report": {
    "id": 1,
    "titulo": "Dashboard de Ventas"
  },
  "filtros": {
    "Mes": {
      "table": "Calendario",
      "column": "NombreMes",
      "available_values": ["Enero", "Febrero", "Marzo", ...],
      "type": "string"
    },
    "Región": {
      "table": "Geografía",
      "column": "Región",
      "available_values": ["Norte", "Sur", "Este", "Oeste"],
      "type": "string"
    }
  },
  "total_filtros": 2
}
```

---

## 📝 Sintaxis de Filtros de PowerBI (OData)

Los filtros se construyen usando sintaxis OData de Microsoft PowerBI:

### Operadores Soportados

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `eq` | Igual a | `Mes eq 'Marzo'` |
| `ne` | No igual a | `Estado ne 'Inactivo'` |
| `gt` | Mayor que | `Ventas gt 10000` |
| `lt` | Menor que | `Precio lt 100` |
| `ge` | Mayor o igual | `Cantidad ge 50` |
| `le` | Menor o igual | `Descuento le 0.2` |
| `in` | En lista | `Región in ('Norte', 'Sur')` |

### Tipos de Datos

```python
# String
{"Mes": "Marzo"}  →  Mes eq 'Marzo'

# Número
{"Ventas": {"value": 1000, "operator": "gt"}}  →  Ventas gt 1000

# Booleano
{"Activo": True}  →  Activo eq true

# Lista (IN)
{"Región": {"value": ["Norte", "Sur"], "operator": "in"}}
  →  Región in ('Norte', 'Sur')

# Null
{"Comentarios": None}  →  Comentarios eq null
```

### Filtros Múltiples (AND)

```python
{
    "Mes": "Marzo",
    "Región": "Norte",
    "Año": 2024
}
```

**URL generada:**
```
...&filter=Mes eq 'Marzo' and Región eq 'Norte' and Año eq 2024
```

### Caracteres Especiales

El sistema maneja automáticamente el escape de caracteres especiales:

```python
{"Producto": "O'Reilly's Book"}
  →  Producto eq 'O''Reilly''s Book'  # Comillas escapadas
```

---

## 🔍 Ejemplos Completos de Uso

### Ejemplo 1: Dashboard de Ventas Mensuales

```python
# Configuración de filtros (una vez)
PowerBIReport.update_filters(report_id=1, available_filters={
    "Mes": {
        "table": "Calendario",
        "column": "NombreMes",
        "values": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
        "type": "string"
    },
    "Vendedor": {
        "table": "Ventas",
        "column": "NombreVendedor",
        "values": ["Juan Pérez", "María García", "Carlos López"],
        "type": "string"
    }
})

# Uso del ChatBot
Usuario: "Muéstrame las ventas de marzo del vendedor Juan Pérez"

# El ChatBot automáticamente aplica:
filtros = {
    "Mes": "Marzo",
    "Vendedor": "Juan Pérez"
}
```

### Ejemplo 2: Análisis de Cobranzas

```python
# Configuración
PowerBIReport.update_filters(report_id=2, available_filters={
    "Rango_Mora": {
        "table": "Cobranzas",
        "column": "RangoMora",
        "values": ["1-30 días", "31-60 días", "61-90 días", "+90 días"],
        "type": "string"
    },
    "Monto_Minimo": {
        "table": "Cobranzas",
        "column": "MontoDeuda",
        "type": "number"
    }
})

# Uso
Usuario: "Analiza las deudas con más de 60 días de mora y montos mayores a 5000"

filtros = {
    "Rango_Mora": "61-90 días",
    "Monto_Minimo": {
        "table": "Cobranzas",
        "column": "MontoDeuda",
        "value": 5000,
        "operator": "gt"
    }
}
```

### Ejemplo 3: KPIs Operacionales

```python
# Configuración
PowerBIReport.update_filters(report_id=3, available_filters={
    "Sucursal": {
        "table": "Operaciones",
        "column": "NombreSucursal",
        "values": ["Sucursal Centro", "Sucursal Norte", "Sucursal Sur"],
        "type": "string"
    },
    "Trimestre": {
        "table": "Calendario",
        "column": "Trimestre",
        "values": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
        "type": "string"
    }
})

# Uso
Usuario: "Compara los KPIs del Q1 y Q2 2024 para la sucursal norte"

# El ChatBot haría dos análisis:
# 1. Filtros: {"Trimestre": "Q1 2024", "Sucursal": "Sucursal Norte"}
# 2. Filtros: {"Trimestre": "Q2 2024", "Sucursal": "Sucursal Norte"}
# Luego compararía los resultados
```

---

## ⚠️ Consideraciones Importantes

### 1. Compatibilidad con Reportes Existentes

- ✅ Los reportes sin filtros configurados funcionan como antes
- ✅ La funcionalidad es 100% backward compatible
- ✅ No se requiere modificar reportes existentes

### 2. Limitaciones

- 🔸 Los nombres de tabla y columna deben coincidir con el modelo de datos de PowerBI
- 🔸 Filtros muy complejos (OR múltiples, funciones) pueden no ser soportados por URL
- 🔸 La URL tiene límite de longitud (~2000 caracteres)

### 3. Mejores Prácticas

1. **Documentar filtros**: Mantén actualizado el campo `available_filters`
2. **Valores válidos**: Lista todos los valores posibles en `values`
3. **Nombres claros**: Usa nombres descriptivos para filtros
4. **Probar filtros**: Verifica que funcionen en PowerBI directamente
5. **Monitorear uso**: Revisa logs para detectar filtros incorrectos

---

## 🐛 Troubleshooting

### Problema: El filtro no se aplica

**Solución:**
1. Verificar que el nombre de tabla/columna coincida con PowerBI
2. Revisar los logs: buscar "Aplicando filtros" y "URL con filtros construida"
3. Probar la URL manualmente en el navegador

### Problema: Error al capturar screenshot

**Solución:**
1. Verificar que la URL del reporte es accesible
2. Aumentar `wait_time` si el reporte carga lento
3. Revisar que el formato de filtro sea correcto

### Problema: El ChatBot no detecta que debe usar filtros

**Solución:**
1. Ser más explícito en la pregunta: "Analiza el reporte con filtro de mes=Marzo"
2. Usar `get_powerbi_report_filters` primero para ver filtros disponibles
3. Verificar que `available_filters` esté configurado en la BD

---

## 📊 Métricas y Monitoring

Los filtros aplicados se registran en:

1. **Logs del sistema:**
```
INFO: Aplicando filtros: {'Mes': 'Marzo', 'Región': 'Norte'}
INFO: URL con filtros construida: https://app.powerbi.com/reportEmbed?...&filter=Mes eq 'Marzo' and Región eq 'Norte'
```

2. **Respuesta del ChatBot:**
```json
{
  "analisis": "...",
  "filtros_aplicados": {"Mes": "Marzo", "Región": "Norte"},
  "metadata": {
    "con_filtros": true
  }
}
```

3. **Tabla `chatbot_actions`:**
```sql
SELECT action_params, action_result
FROM chatbot_actions
WHERE action_type = 'analyze_powerbi_report'
AND JSON_EXTRACT(action_params, '$.filtros') IS NOT NULL
```

---

## 🔄 Actualización de Reportes Existentes

Para agregar filtros a un reporte existente:

```python
from models import PowerBIReport

# 1. Obtener reporte actual
report = PowerBIReport.get_by_id(1)

# 2. Definir filtros
nuevos_filtros = {
    "Mes": {
        "table": "Calendario",
        "column": "NombreMes",
        "values": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
        "type": "string"
    }
}

# 3. Actualizar
PowerBIReport.update_filters(1, nuevos_filtros)

# 4. Verificar
filtros = PowerBIReport.get_filters(1)
print(filtros)
```

---

## 📚 Referencias

- [PowerBI URL Filters Documentation](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-url-filters)
- [OData Filter Syntax](https://docs.oasis-open.org/odata/odata/v4.01/odata-v4.01-part2-url-conventions.html)
- [PowerBI Embedded API](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embed-sample-for-your-organization)

---

## ✅ Checklist de Implementación

- [x] Migración de BD aplicada
- [x] Tests unitarios pasando (12/12)
- [ ] Reportes configurados con `available_filters`
- [ ] ChatBot probado con filtros
- [ ] Documentación compartida con equipo
- [ ] Monitoreo de logs configurado

---

**Versión:** 1.0.0
**Fecha:** 2025-11-23
**Autor:** Claude Code Assistant
