"""
checklist_generator.py
Módulo de extracción de texto PDF y generación de checklist vía LLM (Anthropic Claude).
"""

import json
import os
import io
import pdfplumber
import anthropic


# ─────────────────────────── SYSTEM PROMPT ─────────────────────────
# Este es el prompt exacto que se envía al LLM.
# Modifícalo si necesitas ajustar el comportamiento de extracción.
SYSTEM_PROMPT = """Eres un experto senior en ingeniería mecatrónica, vehículos especiales y control de calidad para contratos del Estado peruano (OSCE/SEACE).
Tu especialidad es integrar chasis (Mercedes Benz, Volvo, Scania, etc.) con carrocerías especiales (compactadoras de basura, cisternas, volquetes, barredoras, etc.) fabricadas por terceros.

Tu tarea: analizar documentos técnicos en español (Términos de Referencia - TDR y/o Ofertas Técnicas) y extraer TODA la información técnica relevante para generar un checklist de inspección de control de calidad en campo (taller del carrocero).

REGLA CRÍTICA: Responde ÚNICAMENTE con un objeto JSON válido y bien formado. Sin markdown, sin bloques de código, sin explicaciones, sin texto antes o después. Solo el JSON.

El JSON debe seguir EXACTAMENTE esta estructura:

{
  "tipo_maquina": "string — Tipo específico de vehículo/equipo (ej: Compactadora de Basura de Carga Trasera, Cisterna de Agua Potable, Camión Volquete, Barredora Mecánica, Camión Plataforma, etc.)",

  "datos_equipo": {
    "entidad_destino": "string — Nombre completo de la entidad del Estado (Municipalidad, GORE, Ministerio, etc.) que recibirá el equipo. Si no está en el documento, usar 'Por definir'.",
    "tipo_vehiculo": "string — Descripción completa: tipo + uso previsto (ej: 'Compactadora de Basura de Carga Trasera para recolección de residuos sólidos urbanos')",
    "marca_chasis": "string — Marca, modelo y año del chasis (ej: 'Mercedes Benz Atego 1726 2024', 'Volvo FM 440 6x4 2024'). Si no especifica, poner 'Según oferta técnica'.",
    "nombre_carrocero": "string — Empresa fabricante de la carrocería. Si no está en el documento, usar 'Por definir'."
  },

  "verificacion_fisica": [
    {
      "categoria": "string — Categoría técnica. Usar UNO de estos: Estructura / Carrocería, Sistema Hidráulico, Sistema Eléctrico, Chasis y Transmisión, Pintura y Acabados, Sistema de Compactación, Tanque y Cisterna, Seguridad y Señalización, Cabina y Ergonomía, Normativa y Certificaciones",
      "item": "string — Nombre conciso del componente o parámetro a verificar (máx 8 palabras)",
      "especificacion": "string — Especificación técnica EXACTA tal como aparece en el documento: materiales, dimensiones, normas, valores numéricos (ej: 'Plancha de acero ASTM A-36, espesor 4mm mínimo', 'Capacidad neta ≥ 9 m³', 'Presión máxima sistema hidráulico: 3500 PSI')"
    }
  ],

  "accesorios_adicionales": [
    {
      "item": "string — Nombre del accesorio (ej: 'Circulina LED ambar', 'Cámara de retroceso', 'Extintor PQS')",
      "descripcion": "string — Descripción y especificación completa del accesorio según el documento"
    }
  ],

  "pruebas_funcionamiento": [
    {
      "prueba": "string — Nombre de la prueba operativa",
      "unidad": "string — Unidad de medida o tipo de resultado esperado (ej: 'Segundos', 'PSI', 'Bar', 'L/min', 'Aprobado/Rechazado', 'RPM', 'm³/h')",
      "valor_referencia": "string — Valor mínimo/máximo/nominal según documento, o 'Según TDR' si no especifica"
    }
  ]
}

INSTRUCCIONES DE EXTRACCIÓN — LEE ESTO CON ATENCIÓN:

PARA "verificacion_fisica" (sé EXHAUSTIVO — mínimo 15 ítems si el documento lo permite):
• Extrae TODOS los requerimientos con especificaciones técnicas: espesores de plancha, materiales (ASTM, SAE, DIN), dimensiones, capacidades, ángulos, presiones, potencias, normas técnicas (ISO, ASTM, NTP, etc.)
• Incluye: estructura del chasis, carrocería metálica, sistema hidráulico, pinturas (marca, capas, micras), iluminación, señalización, neumáticos, motor, transmisión, PTO, etc.
• Cada ítem debe ser verificable físicamente con una cinta métrica, calibrador o de visu en el taller.

PARA "accesorios_adicionales":
• Lista SOLO los elementos que NO vienen de fábrica estándar con el chasis: accesorios adicionales, mejoras, equipamiento extra ofertado.
• Ejemplos: circulinas, cámaras de retroceso, GPS, extintores, conos de seguridad, herramientas de dotación, lona, escalerilla, botiquín, radio, kit de carretera, etc.

PARA "pruebas_funcionamiento" — DEDUCE según el "tipo_maquina":
• COMPACTADORA: Tiempo de ciclo de compactación, Presión sistema hidráulico, Ratio de compactación, Prueba de eyector, Prueba estanqueidad panel trasero, RPM de PTO, Nivel de ruido.
• CISTERNA: Prueba de estanqueidad (llenado al 100%), Presión de prueba hidrostática, Caudal de descarga (L/min), Presión bomba (Bar o PSI), Tiempo de llenado, Tiempo de descarga.
• VOLQUETE: Ángulo de volcado (grados), Tiempo de levantamiento de tolva (seg), Tiempo de bajada (seg), Presión cilindro hidráulico (Bar), Capacidad de carga (m³).
• BARREDORA: Ancho de barrido (m), Capacidad tolva residuos (m³), Caudal sistema de agua (L/min), RPM cepillos.
• OTROS: Deduce pruebas lógicas según el tipo de equipo.

Si el texto del documento es insuficiente para determinar un campo, usa valores genéricos razonables para el tipo de máquina identificado y márcalos con "(estimado)".
"""


def extract_pdf_text(pdf_files) -> str:
    """
    Extrae y concatena el texto de uno o más archivos PDF cargados en Streamlit.

    Args:
        pdf_files: Lista de UploadedFile de Streamlit (tipo BytesIO).

    Returns:
        String con todo el texto extraído, separado por separadores de página.
    """
    all_text = []

    for uploaded_file in pdf_files:
        file_bytes = uploaded_file.read()
        # Resetear el puntero para uso posterior si es necesario
        uploaded_file.seek(0)

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            doc_texts = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    doc_texts.append(f"[Página {i+1}]\n{page_text.strip()}")

            if doc_texts:
                section_header = f"\n{'='*60}\n📄 DOCUMENTO: {uploaded_file.name}\n{'='*60}\n"
                all_text.append(section_header + "\n\n".join(doc_texts))

    if not all_text:
        raise ValueError(
            "No se pudo extraer texto de ningún PDF. "
            "Verifica que los archivos no estén escaneados sin OCR."
        )

    full_text = "\n\n".join(all_text)
    return full_text


def generate_checklist_with_llm(pdf_text: str) -> dict:
    """
    Envía el texto extraído al LLM (Anthropic Claude) y devuelve el checklist
    estructurado como diccionario Python.

    Args:
        pdf_text: Texto completo extraído de los PDFs.

    Returns:
        Diccionario con la estructura del checklist.

    Raises:
        ValueError: Si no se encuentra la API key.
        json.JSONDecodeError: Si el LLM no devuelve JSON válido.
        anthropic.APIError: Si hay un error en la llamada a la API.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "No se encontró ANTHROPIC_API_KEY. "
            "Configúrala en el archivo .env o en el sidebar de la aplicación."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Limitar texto a ~50k caracteres para no exceder el contexto
    # (~15,000 tokens aprox.). Un TDR típico peruano tiene 5,000-20,000 chars.
    max_chars = 60_000
    truncated_text = pdf_text[:max_chars]
    if len(pdf_text) > max_chars:
        truncated_text += f"\n\n[NOTA: Texto truncado. Se procesaron {max_chars:,} de {len(pdf_text):,} caracteres totales.]"

    user_message = f"""Analiza el siguiente documento técnico (TDR y/o Oferta Técnica) y genera el checklist de inspección de control de calidad completo en formato JSON:

{truncated_text}

IMPORTANTE: Responde ÚNICAMENTE con el JSON. Ningún texto adicional antes ni después."""

    # ── Llamada a la API ──
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    raw_text = response.content[0].text.strip()

    # ── Limpieza defensiva de posibles bloques markdown ──
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        # Quitar primera y última línea si son ``` o ```json
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    # ── Parse JSON ──
    checklist_data = json.loads(raw_text)

    # ── Validación mínima de estructura ──
    required_keys = ["tipo_maquina", "datos_equipo", "verificacion_fisica",
                     "accesorios_adicionales", "pruebas_funcionamiento"]
    for key in required_keys:
        if key not in checklist_data:
            checklist_data[key] = [] if key not in ["tipo_maquina", "datos_equipo"] else {}

    return checklist_data
