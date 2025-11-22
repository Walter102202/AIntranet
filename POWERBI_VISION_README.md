# 🔍 Análisis de Reportes PowerBI con Visión AI

## 📋 Descripción General

Este módulo agrega capacidades de **Visión Artificial (VLM - Vision Language Model)** al chatbot de la intranet, permitiendo analizar visualmente los reportes de Power BI y responder preguntas sobre gráficos, KPIs y tendencias.

### ✨ Características

- 🤖 **Análisis Visual con GPT-5.1**: Utiliza IA con capacidades de visión para "ver" los gráficos
- 📊 **Análisis Completo**: Identifica gráficos, KPIs, tendencias y anomalías
- ❓ **Preguntas Específicas**: Responde preguntas concretas sobre los datos mostrados
- 💬 **Integración con Chatbot**: Todo desde la misma interfaz de chat existente
- 🔒 **Seguro**: Respeta permisos de usuario y no almacena screenshots

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
# Instalar paquetes Python
pip install -r requirements.txt

# Instalar navegador para Playwright
playwright install chromium
```

### 2. Configurar Variables de Entorno

Copia `.env.example` a `.env` y configura:

```bash
# API de OpenAI (requerido)
LLM_API_KEY=sk-tu-api-key-aqui

# Modelo con visión (recomendado GPT-5.1)
LLM_MODEL=gpt-5.1

# Reasoning effort para visión (IMPORTANTE: usar 'low')
LLM_VISION_REASONING_EFFORT=low

# Tokens (aumentar para análisis detallados)
LLM_MAX_TOKENS=4000
```

### 3. Verificar Instalación

```python
# Ejecutar prueba desde Python
from modules.chatbot.screenshot_service import ScreenshotService

# Probar captura de screenshot
ScreenshotService.test_capture()
```

---

## 📖 Cómo Usar

### Desde el Chatbot (Interfaz de Usuario)

#### **Paso 1: Listar Reportes Disponibles**

```
Usuario: "¿Qué reportes de PowerBI tenemos disponibles?"

Bot: "Tenemos 5 reportes activos:
1. Dashboard de Ventas Q1 2024 (ID: 1) - Categoría: ventas
2. Análisis Financiero Mensual (ID: 2) - Categoría: finanzas
3. KPIs de RRHH (ID: 3) - Categoría: rrhh
4. Métricas de Operaciones (ID: 4) - Categoría: operaciones
5. Performance Marketing (ID: 5) - Categoría: marketing"
```

#### **Paso 2: Analizar un Reporte**

**Análisis General:**
```
Usuario: "Analiza el reporte de ventas"

Bot: [Captura screenshot + análisis con GPT-5.1]
"He analizado el Dashboard de Ventas Q1 2024:

📊 **Descripción General:**
Este reporte muestra el desempeño de ventas del primer trimestre...

📈 **Gráficos Principales:**
1. Gráfico de Barras: Ventas mensuales
   - Enero: $180,000
   - Febrero: $220,000 (+22%)
   - Marzo: $250,000 (+13.6%)

2. KPI Cards:
   - Ventas Totales: $650,000
   - Objetivo: $600,000 ✅ (+8.3%)
   - Clientes Nuevos: 47
   - Tasa Conversión: 34%

..."
```

**Pregunta Específica:**
```
Usuario: "¿Qué mes tuvo mejor desempeño en el reporte de ventas?"

Bot: "Según el análisis visual del reporte, marzo fue el mes con mejor desempeño:
- Ventas de marzo: $250,000
- 38% superior a enero
- 13.6% superior a febrero
- Superó el objetivo mensual por $25,000"
```

#### **Paso 3: Preguntas de Seguimiento**

```
Usuario: "¿Hay alguna tendencia preocupante?"

Bot: "No, la tendencia general es positiva con crecimiento sostenido.
Sin embargo, observo que:
- La tasa de conversión bajó 2% en marzo vs febrero
- Los clientes recurrentes disminuyeron 8%
Sugiero revisar la retención de clientes."
```

---

## 💡 Ejemplos de Uso

### Caso de Uso 1: Análisis de KPIs

```
Usuario: "Resume los KPIs del reporte financiero"

Bot: [Analiza el reporte]
"KPIs Principales del Análisis Financiero Mensual:

💰 Ingresos:
- Total: $1.2M
- Vs. mes anterior: +15%
- Vs. objetivo: +3%

💸 Gastos:
- Total: $850K
- Operativos: $620K (73%)
- Administrativos: $230K (27%)

📊 Márgenes:
- Margen Bruto: 42%
- Margen Neto: 29%
- EBITDA: $380K

🎯 Indicadores:
- ROI: 18%
- Liquidez: 2.1
- Endeudamiento: 0.4"
```

### Caso de Uso 2: Comparación de Períodos

```
Usuario: "Compara los resultados de Q1 vs Q4 del año pasado"

Bot: "Analizando el gráfico comparativo:

📈 **Crecimiento Q1 2024 vs Q4 2023:**

Ventas:
- Q1 2024: $650K
- Q4 2023: $580K
- Crecimiento: +12% (+$70K)

Clientes:
- Q1: 47 nuevos
- Q4: 38 nuevos
- Crecimiento: +24%

Ticket Promedio:
- Q1: $13,830
- Q4: $15,260
- Cambio: -9.4% (cliente más económicos)

✅ Conclusión: Mayor volumen, menor ticket promedio"
```

### Caso de Uso 3: Detección de Anomalías

```
Usuario: "¿Ves algo raro en el reporte de operaciones?"

Bot: "Sí, identifico 2 anomalías:

⚠️ **Anomalía 1 - Pico en Semana 12:**
- Producción aumentó 340% (de 1,200 a 5,280 unidades)
- Posible error de registro o evento especial

⚠️ **Anomalía 2 - Caída en Eficiencia:**
- Eficiencia bajó de 94% a 67% en marzo
- Coincide con aumento de personal nuevo (+15 empleados)

💡 Recomendación: Revisar datos de semana 12 y plan de capacitación"
```

---

## 🛠️ Arquitectura Técnica

### Flujo de Procesamiento

```
┌─────────────┐
│   Usuario   │ "Analiza el reporte 3"
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│  1. Chatbot detecta herramienta     │
│     analyze_powerbi_report(id=3)    │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│  2. Screenshot Service              │
│     - Playwright abre navegador     │
│     - Carga iframe de PowerBI       │
│     - Espera renderizado (8s)       │
│     - Captura screenshot 1920x1080  │
│     - Optimiza y convierte a base64 │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│  3. LLM Client (GPT-5.1)            │
│     - Envía imagen + contexto       │
│     - reasoning_effort = 'low'      │
│     - Modelo analiza visualmente    │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│  4. Respuesta al Usuario            │
│     "Este reporte muestra..."       │
└─────────────────────────────────────┘
```

### Componentes

#### 1. **Screenshot Service** (`modules/chatbot/screenshot_service.py`)

```python
class ScreenshotService:
    @staticmethod
    def capture_powerbi_report(embed_url, width=1920, height=1080, wait_time=8000):
        """Captura screenshot de reporte PowerBI usando Playwright"""
        # - Lanza navegador headless Chromium
        # - Renderiza JavaScript de PowerBI
        # - Espera carga completa
        # - Optimiza imagen para API
        # - Retorna base64
```

#### 2. **LLM Client con Visión** (`modules/chatbot/llm_client.py`)

```python
class LLMClient:
    def chat_completion_with_vision(self, messages, image_base64, tools, tool_choice):
        """Envía imagen a GPT-5.1 para análisis"""
        # - Construye payload con imagen en base64
        # - Usa reasoning_effort='low' para visión
        # - Envía a OpenAI API
        # - Retorna análisis del modelo
```

#### 3. **Herramientas del Chatbot** (`modules/chatbot/tools.py`)

```python
# Herramienta 1: Listar reportes
def _execute_list_powerbi_reports(self, args):
    """Lista reportes activos por categoría"""

# Herramienta 2: Analizar reporte
def _execute_analyze_powerbi_report(self, args):
    """Captura + Analiza reporte con visión"""
```

---

## ⚙️ Configuración Avanzada

### Ajustar Calidad de Screenshot

```python
# En screenshot_service.py, línea 18
ScreenshotService.capture_powerbi_report(
    embed_url=url,
    width=2560,      # Mayor resolución
    height=1440,     # Mayor resolución
    wait_time=12000  # Esperar 12 segundos
)
```

### Cambiar Modelo de Visión

```bash
# .env - Usar GPT-4o (más económico)
LLM_MODEL=gpt-4o
# No usar LLM_VISION_REASONING_EFFORT (GPT-4o no lo soporta)

# .env - Usar GPT-5.1 con más razonamiento
LLM_MODEL=gpt-5.1
LLM_VISION_REASONING_EFFORT=medium  # Cuidado: puede empeorar visión
```

### Optimizar Costos

```python
# Reducir tamaño máximo de imagen (en screenshot_service.py línea 150)
screenshot_base64 = ScreenshotService._optimize_image(
    screenshot_bytes,
    max_size_mb=2.0,  # Reducir de 5MB a 2MB
    quality=75        # Reducir calidad de 85 a 75
)
```

---

## 🐛 Solución de Problemas

### Error: "playwright._impl._api_types.TimeoutError"

**Causa:** El reporte tardó más de 30 segundos en cargar.

**Solución:**
```python
# Aumentar timeout en screenshot_service.py línea 47
page.goto(embed_url, wait_until='networkidle', timeout=60000)  # 60 segundos
```

### Error: "No se pudo capturar el reporte"

**Causa:** La URL de PowerBI no es accesible o requiere autenticación.

**Solución:**
- Verificar que la URL sea pública (compartida con "cualquiera con el enlace")
- Revisar que no haya firewall bloqueando Playwright
- Probar la URL manualmente en un navegador

### Error: "Error al conectar con el LLM: 401"

**Causa:** API key de OpenAI inválida o sin fondos.

**Solución:**
```bash
# Verificar API key en .env
LLM_API_KEY=sk-proj-...  # Debe empezar con sk-proj- o sk-

# Verificar fondos en: https://platform.openai.com/account/billing
```

### El análisis es demasiado genérico

**Causa:** El modelo no tiene suficiente contexto.

**Solución:**
```
# Hacer preguntas más específicas
❌ "Analiza el reporte"
✅ "¿Cuál es el valor del KPI de ventas en marzo y cómo se compara con el objetivo?"

# O mejorar la descripción del reporte en PowerBI
```

---

## 📊 Métricas y Rendimiento

### Tiempos Estimados

| Operación | Tiempo Promedio |
|-----------|-----------------|
| Captura de screenshot | 10-15 segundos |
| Análisis con GPT-5.1 (low) | 5-8 segundos |
| Análisis con GPT-4o | 3-5 segundos |
| **Total por consulta** | **15-23 segundos** |

### Costos Estimados (OpenAI)

| Modelo | Costo por Imagen | Costo por 100 Consultas |
|--------|------------------|-------------------------|
| GPT-5.1 (low reasoning) | ~$0.015 | ~$1.50 |
| GPT-4o | ~$0.01 | ~$1.00 |
| GPT-4-turbo | ~$0.02 | ~$2.00 |

---

## 🔐 Seguridad y Privacidad

### ✅ Buenas Prácticas

- Screenshots se generan **on-demand** (no se almacenan)
- Solo usuarios autenticados pueden usar la funcionalidad
- Respeta permisos de visualización de reportes
- URLs de PowerBI deben ser compartidas (no privadas)
- Logs no incluyen imágenes (solo metadatos)

### ⚠️ Consideraciones

- Las imágenes se envían a OpenAI API (revisar términos de uso)
- No usar con datos ultra sensibles sin encriptación adicional
- Configurar rate limiting si es necesario

---

## 🚀 Próximas Mejoras

- [ ] Soporte para múltiples páginas de un reporte
- [ ] Exportar análisis a PDF
- [ ] Cache de screenshots para reportes estáticos
- [ ] Comparación automática entre períodos
- [ ] Alertas proactivas sobre anomalías
- [ ] Soporte para Claude 3.5 Sonnet (alternativa a GPT)

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `tail -f logs/chatbot.log`
2. Verifica la configuración en `.env`
3. Prueba con el endpoint directo: `GET /kpis/screenshot/<report_id>`
4. Abre un issue en el repositorio

---

## 📝 Changelog

### v1.0.0 (2025-01-XX)
- ✅ Implementación inicial con GPT-5.1
- ✅ Captura de screenshots con Playwright
- ✅ Optimización automática de imágenes
- ✅ Herramientas de chatbot integradas
- ✅ Documentación completa

---

**¡Disfruta del análisis inteligente de tus reportes PowerBI! 🚀📊**
