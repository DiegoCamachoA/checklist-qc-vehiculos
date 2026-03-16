"""
checklist_generator.py
Módulo de generación de checklist vía Google Gemini Files API.

Estrategia: En lugar de extraer texto del PDF (que falla con escaneados),
subimos el PDF directamente a la Files API de Gemini. El modelo lee las
páginas como imágenes con OCR nativo, manejando tanto PDFs con texto
como PDFs escaneados sin ninguna dependencia adicional.
"""

import json
import os
import io
import time
from google import genai


# ─────────────────────────── SYSTEM PROMPT ─────────────────────────
SYSTEM_PROMPT = """Eres un experto senior en ingeniería mecatrónica, vehículos especiales y control de calidad para contratos del Estado peruano (OSCE/SEACE).
Tu especialidad es integrar chasis (Mercedes Benz, Volvo, Scania, etc.) con carrocerías especiales (compactadoras de basura, cisternas, volquetes, barredoras, etc.) fabricadas por terceros.

Tu tarea: analizar documentos técnicos en español (Términos de Referencia - TDR y/o Ofertas Técnicas) — incluyendo tablas escaneadas y texto impreso — y extraer TODA la información técnica relevante para generar un checklist de inspección de control de calidad en campo (taller del carrocero).

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

INSTRUCCIONES DE EXTRACCIÓN — LEE TABLAS Y TEXTO ESCANEADO:

PARA verificacion_fisica (mínimo 15 ítems si el documento lo permite):
- Examina TODAS las páginas incluyendo tablas escaneadas como imágenes
- Extrae TODOS los requerimientos técnicos: espesores de plancha, materiales (ASTM, SAE, DIN), dimensiones, capacidades, presiones, potencias, normas (ISO, NTP, ASTM)
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

IMPORTANTE: Extrae los valores REALES del documento. Solo usa valores genéricos si una especificación realmente no está mencionada en ninguna página del documento."""

USER_PROMPT = """Analiza todos los documentos adjuntos (TDR y/o Oferta Técnica). Examina cada página incluyendo tablas escaneadas.

Genera el checklist de inspección de control de calidad completo.

Responde ÚNICAMENTE con el JSON puro, sin texto adicional antes ni después."""


def generate_checklist_from_pdfs(pdf_files: list, api_key: str) -> dict:
    """
    Sube los PDFs a la Files API de Gemini y genera el checklist.
    Maneja PDFs escaneados nativamente — Gemini lee las imágenes directamente.
    """
    client = genai.Client(api_key=api_key)
    uploaded_file_refs = []

    # ── 1. Subir cada PDF a la Files API ─────────────────────────────
    for uploaded_file in pdf_files:
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)

        file_ref = client.files.upload(
            file=io.BytesIO(file_bytes),
            config=genai.types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=uploaded_file.name,
            ),
        )

        # Esperar a que el archivo esté ACTIVE (máx 30 seg)
        waited = 0
        while file_ref.state.name == "PROCESSING" and waited < 30:
            time.sleep(2)
            waited += 2
            file_ref = client.files.get(name=file_ref.name)

        uploaded_file_refs.append(file_ref)

    # ── 2. Construir contenido: archivos + prompt ─────────────────────
    contents = uploaded_file_refs + [USER_PROMPT]

    # ── 3. Llamar al modelo ───────────────────────────────────────────
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    # ── 4. Limpiar archivos subidos ───────────────────────────────────
    for ref in uploaded_file_refs:
        try:
            client.files.delete(name=ref.name)
        except Exception:
            pass

    # ── 5. Parsear respuesta ──────────────────────────────────────────
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    checklist_data = json.loads(raw_text)

    required_keys = ["tipo_maquina", "datos_equipo", "verificacion_fisica",
                     "accesorios_adicionales", "pruebas_funcionamiento"]
    for key in required_keys:
        if key not in checklist_data:
            checklist_data[key] = [] if key not in ["tipo_maquina", "datos_equipo"] else {}

    return checklist_data
