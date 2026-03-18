"""
checklist_generator.py
Extracción híbrida de PDFs + generación de checklist vía Google Gemini.

Estrategia de extracción (en orden de velocidad):
  1. pdfplumber  → extrae texto digital en <1 segundo (PDFs con texto)
  2. Gemini Files API → OCR nativo para páginas sin texto detectable (escaneadas)

Determinismo implementado mediante tres palancas:
  1. temperature=0     → elimina aleatoriedad en la elección de tokens
  2. response_schema   → fuerza estructura JSON estricta (forma, no contenido)
  3. Few-shot en prompt → calibra verbosidad y granularidad del output
"""

import os
import io
import time
import json
import pdfplumber
from typing import List
from pydantic import BaseModel
from google import genai


# ─────────────────────────── UMBRAL DE TEXTO ───────────────────────
# Mínimo de caracteres por página para considerar que pdfplumber tuvo éxito.
MIN_CHARS_PER_PAGE = 80


# ─────────────────────── RESPONSE SCHEMA (Palanca 2) ───────────────
# Define FORMA del output, no contenido.
# Las listas no tienen longitud mínima/máxima: si el PDF no menciona
# un accesorio, la lista estará vacía. Si menciona 20 ítems, habrá 20.
# Ningún campo de contenido tiene enum ni restricción de valor.

class DatosEquipo(BaseModel):
    entidad_destino: str
    tipo_vehiculo: str
    marca_chasis: str
    nombre_carrocero: str

class ItemVerificacion(BaseModel):
    categoria: str       # String libre — no enum, para no sesgar categorías
    item: str
    especificacion: str

class Accesorio(BaseModel):
    item: str
    descripcion: str

class PruebaFuncionamiento(BaseModel):
    prueba: str
    unidad: str
    valor_referencia: str

class ChecklistQC(BaseModel):
    tipo_maquina: str
    datos_equipo: DatosEquipo
    verificacion_fisica: List[ItemVerificacion]
    accesorios_adicionales: List[Accesorio]
    pruebas_funcionamiento: List[PruebaFuncionamiento]


# ─────────────────────── SYSTEM PROMPT + FEW-SHOT (Palancas 2 y 3) ─
# Los ejemplos few-shot calibran EXCLUSIVAMENTE:
#   - Longitud y tono de tipo_maquina (conciso, no descriptivo)
#   - Formato de especificacion (valor + unidad + norma si aplica)
#   - Concisión de item (sustantivo + adjetivo necesario, max 8 palabras)
#   - Que la cantidad de ítems es variable y depende 100% del documento
#
# Los ejemplos NO contienen categorías ni valores que puedan repetirse
# como plantilla — usan equipos y datos distintos entre sí a propósito.

SYSTEM_PROMPT = """Eres un experto senior en ingeniería mecatrónica y control de calidad para contratos del Estado peruano (OSCE/SEACE), especializado en vehículos especiales: compactadoras, cisternas, volquetes, barredoras, camiones plataforma, entre otros.

Tu tarea: analizar documentos técnicos (TDR y/o Ofertas Técnicas) y extraer ÚNICAMENTE la información técnica que aparece explícitamente en el documento para generar un checklist de inspección de control de calidad en campo.

━━━ REGLAS DE EXTRACCIÓN ━━━

1. EXTRAE SOLO LO QUE ESTÁ EN EL DOCUMENTO.
   Si el documento no menciona el tipo de pintura, no incluyas ningún ítem de pintura.
   Si menciona 6 requerimientos hidráulicos, incluye exactamente 6 — ni más, ni menos.

2. FORMATO DE CAMPOS:
   • tipo_maquina: nombre técnico conciso del equipo (5-8 palabras máximo)
   • item: sustantivo técnico, máximo 8 palabras, sin verbos
   • especificacion: valor exacto del documento + unidad + norma si se indica
     Bien:  "Plancha ASTM A-36, espesor mínimo 4mm"
     Bien:  "Capacidad neta 9 m³"
     Bien:  "Presión máxima 3,500 PSI"
     Mal:   "De acero de buena calidad"
     Mal:   "Según normativa aplicable"
   • categoria: usa la categoría técnica más apropiada en texto libre
   • marca_chasis: SIEMPRE incluir marca + modelo completo + año si aparece en el documento
     Bien: "Mercedes Benz Atego 1726 2024"  |  Bien: "Volvo FM 440 6x4 2024"
     Mal:  "Mercedes Benz"  |  Mal: "Volvo"  ← nunca solo la marca sin el modelo

3. ACCESORIOS: solo elementos que no vienen de fábrica estándar con el chasis.

4. SEPARACIÓN ESTRICTA entre verificacion_fisica y pruebas_funcionamiento — REGLA CRÍTICA:
   • verificacion_fisica → parámetros verificables con la máquina APAGADA y estática:
     dimensiones, espesores, materiales, existencia de componentes, acabados, pintura,
     conexiones, instalación de accesorios. Se verifica con cinta métrica, calibrador o de visu.
   • pruebas_funcionamiento → parámetros que SOLO se pueden medir con la máquina OPERANDO:
     tiempos de ciclo, presiones en operación, caudales, RPM, ángulos bajo carga, temperaturas,
     pruebas de estanqueidad bajo presión, velocidades de movimiento, consumos.
   UN MISMO PARÁMETRO NO PUEDE APARECER EN AMBAS SECCIONES.
   Si un parámetro requiere operar la máquina para medirlo → va SOLO en pruebas_funcionamiento.
   Si un parámetro se verifica sin operar la máquina → va SOLO en verificacion_fisica.

5. PRUEBAS: dedúcelas según el tipo de equipo identificado, usando valores del
   documento si existen. Si no existen valores de referencia, indica "Según TDR".

6. VALOR NO ENCONTRADO: si una especificación no aparece en el documento,
   escribe "Verificar en TDR" — NUNCA inventes valores numéricos.

━━━ EJEMPLOS DE FORMATO (calibración de verbosidad únicamente) ━━━

Estos dos ejemplos ilustran el nivel de detalle y concisión esperados.
Los campos y cantidad de ítems son FICTICIOS — no los uses como plantilla de contenido.

— EJEMPLO A (equipo con muchas especificaciones en el TDR) —
{
  "tipo_maquina": "Barredora Mecánica de Vía Pública",
  "datos_equipo": {
    "entidad_destino": "Municipalidad Distrital de San Isidro",
    "tipo_vehiculo": "Barredora mecánica autopropulsada para limpieza de vías urbanas",
    "marca_chasis": "Mercedes Benz Atego 1016 2024",
    "nombre_carrocero": "Por definir"
  },
  "verificacion_fisica": [
    {"categoria": "Estructura / Carrocería", "item": "Tolva de residuos", "especificacion": "Capacidad 4 m³, acero ASTM A-36"},
    {"categoria": "Sistema de Barrido", "item": "Cepillos laterales", "especificacion": "2 unidades, diámetro 900mm, cerda metálica"},
    {"categoria": "Sistema Hidráulico", "item": "Presión de trabajo bomba", "especificacion": "180 Bar nominal"},
    {"categoria": "Sistema Eléctrico", "item": "Tensión de operación", "especificacion": "24V DC, compatible con chasis"},
    {"categoria": "Pintura y Acabados", "item": "Acabado exterior tolva", "especificacion": "Anticorrosivo epóxico + esmalte PU, 80 micras mínimo"}
  ],
  "accesorios_adicionales": [
    {"item": "Cámara de retroceso", "descripcion": "Monitor 7 pulgadas, visión nocturna"},
    {"item": "Circulinas LED", "descripcion": "2 unidades color ámbar, montaje en cabina"}
  ],
  "pruebas_funcionamiento": [
    {"prueba": "Ancho de barrido efectivo", "unidad": "metros", "valor_referencia": "≥ 2.5 m"},
    {"prueba": "RPM cepillos en operación", "unidad": "RPM", "valor_referencia": "Según TDR"},
    {"prueba": "Caudal sistema de agua", "unidad": "L/min", "valor_referencia": "≥ 120 L/min"}
  ]
}

— EJEMPLO B (equipo con pocas especificaciones en el TDR) —
{
  "tipo_maquina": "Camión Plataforma con Grúa Articulada",
  "datos_equipo": {
    "entidad_destino": "Por definir",
    "tipo_vehiculo": "Camión plataforma para transporte de carga con grúa articulada",
    "marca_chasis": "Según oferta técnica",
    "nombre_carrocero": "Por definir"
  },
  "verificacion_fisica": [
    {"categoria": "Estructura / Carrocería", "item": "Plataforma de carga", "especificacion": "Longitud 6.20 m, ancho 2.40 m, acero SAE 1020"},
    {"categoria": "Sistema de Elevación", "item": "Capacidad de carga grúa", "especificacion": "5 toneladas a 3 metros de radio"}
  ],
  "accesorios_adicionales": [
    {"item": "Extintor PQS", "descripcion": "6 kg, ubicado en cabina"}
  ],
  "pruebas_funcionamiento": [
    {"prueba": "Carga máxima verificada grúa", "unidad": "Toneladas", "valor_referencia": "5 t"},
    {"prueba": "Estabilidad con carga lateral", "unidad": "Aprobado/Rechazado", "valor_referencia": "Según TDR"}
  ]
}
━━━ FIN DE EJEMPLOS ━━━

El número de ítems en tu respuesta debe reflejar exclusivamente lo que contiene el documento analizado."""


USER_PROMPT_TEXT = """Analiza el siguiente texto extraído del documento técnico (TDR y/o Oferta Técnica) y genera el checklist de inspección de control de calidad.

{text}

Recuerda: extrae SOLO lo que aparece en el documento. No añadas ítems que no estén mencionados."""

USER_PROMPT_FILES = """Analiza todos los documentos adjuntos (TDR y/o Oferta Técnica).
Examina cada página incluyendo tablas escaneadas e imágenes.
Genera el checklist de inspección de control de calidad extrayendo SOLO lo que aparece en los documentos."""


# ─────────────────────── CONFIG COMPARTIDA ─────────────────────────
# temperature=0 (Palanca 1): elimina aleatoriedad en la selección de tokens.
# response_mime_type + response_schema (Palanca 2): fuerza estructura exacta.
# El modelo no puede devolver campos extra, renombrar llaves ni cambiar tipos.

def _get_llm_config() -> genai.types.GenerateContentConfig:
    return genai.types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0,
        response_mime_type="application/json",
        response_schema=ChecklistQC,
    )


# ─────────────────────────── EXTRACCIÓN HÍBRIDA ────────────────────

def _try_pdfplumber(file_bytes: bytes, filename: str) -> tuple[str, int, int]:
    """Intenta extraer texto con pdfplumber."""
    text_parts = []
    pages_with_text = 0
    total_pages = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            if len(page_text.strip()) >= MIN_CHARS_PER_PAGE:
                pages_with_text += 1
                text_parts.append(f"[Pág {i+1}]\n{page_text.strip()}")

    full_text = (
        f"\n{'='*50}\nDOCUMENTO: {filename}\n{'='*50}\n"
        + "\n\n".join(text_parts)
    )
    return full_text, pages_with_text, total_pages


def extract_content(pdf_files) -> tuple[str | None, list, dict]:
    """
    Extracción híbrida: pdfplumber primero, Files API para escaneados.
    Devuelve: (texto, archivos_escaneados, stats)
    """
    all_texts = []
    scanned_files = []
    stats = {"text_pages": 0, "scanned_pages": 0, "total_pages": 0}

    for uf in pdf_files:
        file_bytes = uf.read()
        uf.seek(0)

        text, pages_ok, total = _try_pdfplumber(file_bytes, uf.name)
        stats["total_pages"] += total
        stats["text_pages"] += pages_ok
        stats["scanned_pages"] += (total - pages_ok)

        coverage = pages_ok / total if total > 0 else 0
        if coverage >= 0.4:
            all_texts.append(text)
        else:
            scanned_files.append((file_bytes, uf.name))
            if pages_ok > 0:
                all_texts.append(text)

    text_content = "\n\n".join(all_texts) if all_texts else None
    return text_content, scanned_files, stats


# ─────────────────────────── PARSEO ────────────────────────────────

def _parse_response(response) -> dict:
    """
    Con response_schema activo, Gemini garantiza JSON válido con la estructura
    correcta. `response.parsed` devuelve el objeto Pydantic directamente.
    Convertimos a dict para compatibilidad con el resto de la app.
    """
    if response.parsed is not None:
        data = response.parsed.model_dump()
    else:
        # Fallback defensivo: parsear texto si .parsed no está disponible
        raw = response.text.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].strip() == "```" else lines
            raw = "\n".join(lines).strip()
        data = json.loads(raw)

    # Siempre forzar el carrocero correcto (no depender de la IA para esto)
    if isinstance(data.get("datos_equipo"), dict):
        data["datos_equipo"]["nombre_carrocero"] = "Grupo iMetales S.A.C."

    return data


# ─────────────────────────── FUNCIÓN PRINCIPAL ─────────────────────

def generate_checklist_from_pdfs(pdf_files: list, api_key: str) -> tuple[dict, dict]:
    """
    Orquesta extracción híbrida + llamada al LLM con las tres palancas activas.
    Devuelve: (checklist_data, stats)
    """
    client = genai.Client(api_key=api_key)

    # ── Paso 1: Extracción híbrida ──────────────────────────────────
    text_content, scanned_files, stats = extract_content(pdf_files)

    # ── Paso 2: Llamada al LLM ──────────────────────────────────────
    if not scanned_files:
        # PDFs con texto — ruta rápida
        stats["method"] = "texto"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=USER_PROMPT_TEXT.format(text=text_content[:50_000]),
            config=_get_llm_config(),
        )

    else:
        # PDFs escaneados — Files API
        stats["method"] = "ocr"
        uploaded_refs = []

        for file_bytes, filename in scanned_files:
            ref = client.files.upload(
                file=io.BytesIO(file_bytes),
                config=genai.types.UploadFileConfig(
                    mime_type="application/pdf",
                    display_name=filename,
                ),
            )
            waited = 0
            while ref.state.name == "PROCESSING" and waited < 30:
                time.sleep(2)
                waited += 2
                ref = client.files.get(name=ref.name)
            uploaded_refs.append(ref)

        contents = []
        if text_content:
            contents.append(
                f"TEXTO DE PÁGINAS LEGIBLES:\n{text_content[:25_000]}\n\n"
                f"PÁGINAS ESCANEADAS (ver archivos adjuntos):"
            )
        contents += uploaded_refs
        contents.append(USER_PROMPT_FILES)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=_get_llm_config(),
        )

        for ref in uploaded_refs:
            try:
                client.files.delete(name=ref.name)
            except Exception:
                pass

    # ── Paso 3: Parsear y devolver ──────────────────────────────────
    checklist_data = _parse_response(response)
    return checklist_data, stats
