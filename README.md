# ⚙ Generador de Checklist QC · Integración Chasis–Carrocería

Aplicación web desarrollada en **Python + Streamlit** que genera automáticamente
un **Checklist de Inspección de Control de Calidad** a partir de documentos
técnicos en PDF (Términos de Referencia - TDR y/o Oferta Técnica).

Diseñada para Ingenieros de campo en empresas peruanas contratistas del Estado
que integran chasis (Mercedes Benz, Volvo, Scania) con carrocerías especiales
(compactadoras de basura, cisternas, volquetes).

---

## Estructura del Proyecto

```
qc_checklist_app/
│
├── app.py                  ← Aplicación Streamlit (Frontend + Flujo principal)
├── checklist_generator.py  ← Extracción PDF + llamada al LLM (Anthropic Claude)
├── export_utils.py         ← Generación del HTML optimizado para impresión
├── requirements.txt        ← Dependencias Python
├── .env.example            ← Plantilla de variables de entorno
├── .env                    ← Tu API key (NO subir a Git - crear tú mismo)
└── README.md               ← Este archivo
```

---

## Requisitos Previos

- Python 3.9 o superior
- Una cuenta en [Anthropic Console](https://console.anthropic.com) con créditos
- Tu API Key de Anthropic (`sk-ant-...`)

---

## Instalación y Ejecución

### 1. Clonar / descargar el proyecto

```bash
# Crear carpeta y copiar archivos
mkdir qc_checklist_app && cd qc_checklist_app
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env y colocar tu API key real
# ANTHROPIC_API_KEY=sk-ant-tu-key-real-aqui
```

> **Alternativa sin .env:** Puedes ingresar tu API key directamente en el
> sidebar de la aplicación cuando la ejecutes.

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app se abrirá automáticamente en: `http://localhost:8501`

---

## Flujo de Uso

1. **Subir PDFs** — Arrastra y suelta tus documentos técnicos (TDR y/o Oferta Técnica).
   Puedes subir varios PDFs simultáneamente; la app los concatena y analiza juntos.

2. **Generar Checklist** — Presiona el botón. La IA analiza los documentos y extrae:
   - Datos del equipo y entidad
   - Requerimientos técnicos verificables
   - Accesorios adicionales ofertados
   - Pruebas de funcionamiento apropiadas según el tipo de máquina

3. **Revisar Vista Previa** — Revisa el checklist generado en pantalla.

4. **Exportar** — Descarga el HTML y ábrelo en tu navegador.
   Usa `Ctrl+P` (o Cmd+P en Mac) para imprimir o guardar como PDF.

---

## Estructura del Checklist Generado

| Sección | Contenido |
|---------|-----------|
| **§1 Datos del Equipo** | Entidad, tipo de vehículo, marca chasis, carrocero |
| **§2 Verificación Física** | Ítems técnicos con casillas Sí/No/Observaciones |
| **§3 Accesorios Adicionales** | Lista de extras ofertados con casillas de presencia |
| **§4 Pruebas de Funcionamiento** | Líneas para anotar tiempos, presiones, medidas |
| **§5 Firmas** | Ingeniero Inspector + Jefe de Taller |

---

## El Prompt que se envía al LLM

El prompt completo se encuentra en `checklist_generator.py`, variable `SYSTEM_PROMPT`.
Puedes modificarlo para ajustar el comportamiento de extracción según tus necesidades.

**Resumen del prompt:**
- Rol: Experto en ingeniería mecatrónica y contratos OSCE/SEACE Perú
- Tarea: Extraer información técnica de TDR/Oferta y devolver JSON estructurado
- Para §2: Extrae TODOS los requerimientos con especificaciones numéricas y materiales
- Para §3: Lista accesorios que no son estándar de fábrica del chasis
- Para §4: Deduce pruebas operativas según el tipo de máquina identificado
- Formato: JSON estricto, sin markdown, directamente parseable

---

## Tipos de Máquina Soportados

La IA deduce automáticamente las pruebas de funcionamiento según el tipo:
- 🗑 **Compactadoras de Basura** — ciclos, presión hidráulica, eyector, PTO
- 💧 **Cisternas** — estanqueidad, presión hidrostática, caudal de bomba
- 🏗 **Volquetes** — ángulo de volcado, tiempos de levantamiento, presión hidráulica
- 🧹 **Barredoras** — ancho de barrido, caudal de agua, RPM cepillos
- ➕ Cualquier otro equipo especial deducido del documento

---

## Notas Técnicas

- El texto del PDF se extrae con `pdfplumber` (mejor que PyMuPDF para textos con tablas)
- Se procesan hasta 60,000 caracteres por llamada al LLM (suficiente para un TDR típico)
- Si el PDF es un **escaneado** (imagen sin OCR), la extracción de texto fallará.
  En ese caso, primero aplica OCR con Adobe Acrobat, ABBYY FineReader o similar.
- El checklist HTML generado es autocontenido: funciona offline sin internet.
- Los checkboxes en la vista HTML son interactivos en pantalla (clic para marcar).

---

## Dependencias Principales

| Paquete | Versión mínima | Uso |
|---------|---------------|-----|
| `streamlit` | 1.35.0 | Framework web |
| `pdfplumber` | 0.11.0 | Extracción de texto PDF |
| `anthropic` | 0.28.0 | Cliente API Claude |
| `python-dotenv` | 1.0.0 | Variables de entorno |

---

## Licencia

Uso interno. Desarrollado para ingeniería de campo.
