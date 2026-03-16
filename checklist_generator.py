"""
checklist_generator.py
Módulo de extracción de texto PDF y generación de checklist vía Google Gemini API.
"""

import json
import os
import io
import pdfplumber
import google.generativeai as genai


# ─────────────────────────── SYSTEM PROMPT ─────────────────────────
SYSTEM_PROMPT = """Eres un experto senior en ingeniería mecatrónica, vehículos especiales y control de calidad para contratos del Estado peruano (OSCE/SEACE).
Tu especialidad es integrar chasis (Mercedes Benz, Volvo, Scania, etc.) con carrocerías especiales (compactadoras de basura, cisternas, volquetes, barredoras, etc.) fabricadas por terceros.

Tu tarea: analizar documentos técnicos en español (Términos de Referencia - TDR y/o Ofertas Técnicas) y extraer TODA la información técnica relevante para generar un checklist de inspección de control de calidad en campo (taller del carrocero).

REGLA CRÍTICA: Responde ÚNICAMENTE con un objeto JSON válido y bien formado. Sin markdown, sin bloques de código, sin explicaciones, sin texto antes o después. Solo el JSON puro.

El JSON debe seguir EXACTAMENTE esta estructura:

{
  "tipo_maquina": "string — Tipo específico de vehículo/equipo (ej: Compactadora de Basura de Carga Trasera, Cisterna de Agua Potable, Camión Volquete, Barredora Mecánica, etc.)",

  "datos_equipo": {
    "entidad_destino": "string — Nombre completo de la entidad del Estado que recibirá el equipo. Si no está, usar 'Por definir'.",
    "tipo_vehiculo": "string — Descripción completa: tipo + uso previsto",
    "marca_chasis": "string — Marca, modelo y año del chasis. Si no especifica, 'Según oferta técnica'.",
    "nombre_carrocero": "string — Empresa fabricante de la carrocería. Si no está, 'Por definir'."
  },

  "verificacion_fisica": [
    {
      "categoria": "string — UNO de estos: Estructura / Carrocería, Sistema Hidráulico, Sistema Eléctrico, Chasis y Transmisión, Pintura y Acabados, Sistema de Compactación, Tanque y Cisterna, Seguridad y Señalización, Cabina y Ergonomía, Normativa y Certificaciones",
      "item": "string — Nombre conciso del componente a verificar (máx 8 palabras)",
      "especificacion": "string — Especificación técnica EXACTA del documento: materiales, dimensiones, normas, valores numéricos"
    }
  ],

  "accesorios_adicionales": [
    {
      "item": "string — Nombre del accesorio",
      "descripcion": "string — Descripción y especificación completa"
    }
  ],

  "pruebas_funcionamiento": [
    {
      "prueba": "string — Nombre de la prueba operativa",
      "unidad": "string — Unidad de medida (ej: Segundos, PSI, Bar, L/min, Aprobado/Rechazado)",
      "valor_referencia": "string — Valor mínimo/máximo según documento, o 'Según TDR' si no especifica"
    }
  ]
}

INSTRUCCIONES DE EXTRACCIÓN:

PARA verificacion_fisica (mínimo 15 ítems si el documento lo permite):
- Extrae TODOS los requerimientos técnicos: espesores de plancha, materiales (ASTM, SAE), dimensiones, capacidades, presiones, potencias, normas (ISO, NTP, ASTM)
- Cada ítem debe ser verificable físicamente en el taller

PARA accesorios_adicionales:
- Solo elementos que NO vienen de fábrica estándar con el chasis
- Ejemplos: circulinas, cámaras de retroceso, GPS, extintores, conos, herramientas, botiquín

PARA pruebas_funcionamiento — DEDUCE según tipo_maquina:
- COMPACTADORA: Tiempo ciclo compactación, Presión hidráulica, Prueba eyector, RPM PTO, Estanqueidad panel trasero
- CISTERNA: Estanqueidad al 100%, Presión hidrostática, Caudal descarga, Presión bomba, Tiempo llenado/descarga
- VOLQUETE: Ángulo volcado, Tiempo levantamiento/bajada tolva, Presión cilindro hidráulico
- BARREDORA: Ancho barrido, Caudal sistema agua, RPM cepillos
- Para otros equipos: deduce pruebas lógicas según el tipo identificado

Si el texto es insuficiente para un campo, usa valores genéricos razonables y márcalos con (estimado)."""


def extract_pdf_text(pdf_files) -> str:
    """
    Extrae y concatena el texto de uno o más archivos PDF cargados en Streamlit.
    """
    all_text = []

    for uploaded_file in pdf_files:
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            doc_texts = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    doc_texts.append(f"[Página {i+1}]\n{page_text.strip()}")

            if doc_texts:
                section_header = f"\n{'='*60}\nDOCUMENTO: {uploaded_file.name}\n{'='*60}\n"
                all_text.append(section_header + "\n\n".join(doc_texts))

    if not all_text:
        raise ValueError(
            "No se pudo extraer texto de ningún PDF. "
            "Verifica que los archivos no estén escaneados sin OCR."
        )

    return "\n\n".join(all_text)


def generate_checklist_with_llm(pdf_text: str) -> dict:
    """
    Envía el texto extraído a Google Gemini y devuelve el checklist como diccionario.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "No se encontró GEMINI_API_KEY. "
            "Configúrala en los Secrets de Streamlit Cloud o en el sidebar."
        )

    # Configurar cliente Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=SYSTEM_PROMPT,
    )

    # Limitar texto a ~50k caracteres
    max_chars = 50_000
    truncated_text = pdf_text[:max_chars]
    if len(pdf_text) > max_chars:
        truncated_text += f"\n\n[NOTA: Texto truncado. Se procesaron {max_chars:,} de {len(pdf_text):,} caracteres totales.]"

    user_message = f"""Analiza el siguiente documento técnico (TDR y/o Oferta Técnica) y genera el checklist de inspección de control de calidad completo en formato JSON:

{truncated_text}

IMPORTANTE: Responde ÚNICAMENTE con el JSON puro. Ningún texto, ningún bloque markdown antes ni después."""

    response = model.generate_content(user_message)
    raw_text = response.text.strip()

    # Limpieza defensiva de posibles bloques markdown
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    checklist_data = json.loads(raw_text)

    # Validación mínima de estructura
    required_keys = ["tipo_maquina", "datos_equipo", "verificacion_fisica",
                     "accesorios_adicionales", "pruebas_funcionamiento"]
    for key in required_keys:
        if key not in checklist_data:
            checklist_data[key] = [] if key not in ["tipo_maquina", "datos_equipo"] else {}

    return checklist_data
