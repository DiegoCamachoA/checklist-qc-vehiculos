"""
Generador de Checklist de Inspección QC
Aplicación Streamlit · Google Gemini API (gratuito)
"""

import streamlit as st
import json
import os
from datetime import datetime
from checklist_generator import extract_pdf_text, generate_checklist_with_llm
from export_utils import generate_html_checklist

# ─────────────────────────── PAGE CONFIG ───────────────────────────
st.set_page_config(
    page_title="Checklist QC · Integración Vehículos Especiales",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────── CUSTOM CSS ────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
  :root {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a; --border: #2e334a;
    --accent: #f0a500; --accent2: #3a8eff; --text: #e8eaf0; --muted: #7a8099;
    --danger: #e05252; --success: #3ecf8e;
    --mono: 'IBM Plex Mono', monospace; --sans: 'IBM Plex Sans', sans-serif;
  }
  html, body, [class*="css"] { font-family: var(--sans) !important; background-color: var(--bg) !important; color: var(--text) !important; }
  .app-header { background: linear-gradient(135deg, #0f1117 0%, #1a1d27 50%, #0f1117 100%); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 4px; padding: 24px 32px; margin-bottom: 28px; position: relative; overflow: hidden; }
  .app-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(240,165,0,0.06) 0%, transparent 70%); pointer-events: none; }
  .app-header h1 { font-family: var(--mono) !important; font-size: 1.6rem !important; font-weight: 600 !important; color: var(--accent) !important; margin: 0 0 6px 0 !important; letter-spacing: 0.02em !important; }
  .app-header p { color: var(--muted) !important; font-size: 0.88rem !important; margin: 0 !important; }
  .badge { display: inline-block; background: rgba(240,165,0,0.12); color: var(--accent); border: 1px solid rgba(240,165,0,0.3); border-radius: 3px; font-family: var(--mono); font-size: 0.7rem; padding: 2px 8px; margin-right: 8px; margin-top: 10px; }
  .panel-title { font-family: var(--mono) !important; font-size: 0.75rem !important; font-weight: 600 !important; color: var(--accent) !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; margin-bottom: 14px !important; border-bottom: 1px solid var(--border) !important; padding-bottom: 10px !important; }
  [data-testid="stFileUploader"] { background: var(--surface) !important; border: 2px dashed var(--border) !important; border-radius: 8px !important; transition: border-color 0.2s !important; }
  [data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
  .stButton > button { background: var(--accent) !important; color: #0f1117 !important; border: none !important; border-radius: 4px !important; font-family: var(--mono) !important; font-weight: 600 !important; font-size: 0.85rem !important; letter-spacing: 0.05em !important; padding: 10px 24px !important; transition: all 0.2s !important; text-transform: uppercase !important; }
  .stButton > button:hover { background: #ffc72c !important; transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(240,165,0,0.3) !important; }
  .stDownloadButton > button { background: var(--surface2) !important; color: var(--accent2) !important; border: 1px solid var(--accent2) !important; border-radius: 4px !important; font-family: var(--mono) !important; font-weight: 600 !important; font-size: 0.82rem !important; letter-spacing: 0.04em !important; padding: 8px 20px !important; transition: all 0.2s !important; text-transform: uppercase !important; }
  .status-ok { background: rgba(62,207,142,0.08); border: 1px solid rgba(62,207,142,0.3); border-radius: 4px; padding: 10px 14px; color: var(--success); font-family: var(--mono); font-size: 0.82rem; margin-bottom: 12px; }
  .status-warn { background: rgba(240,165,0,0.08); border: 1px solid rgba(240,165,0,0.3); border-radius: 4px; padding: 10px 14px; color: var(--accent); font-family: var(--mono); font-size: 0.82rem; margin-bottom: 12px; }
  .status-err { background: rgba(224,82,82,0.08); border: 1px solid rgba(224,82,82,0.3); border-radius: 4px; padding: 10px 14px; color: var(--danger); font-family: var(--mono); font-size: 0.82rem; margin-bottom: 12px; }
  .checklist-preview { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 24px; }
  .cl-section-title { font-family: var(--mono) !important; font-size: 0.72rem !important; font-weight: 600 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; color: var(--accent) !important; background: rgba(240,165,0,0.08) !important; border-left: 3px solid var(--accent) !important; padding: 6px 12px !important; margin: 18px 0 10px 0 !important; }
  .cl-item { display: flex; align-items: flex-start; gap: 10px; padding: 7px 8px; border-bottom: 1px solid rgba(46,51,74,0.6); font-size: 0.85rem; color: var(--text); }
  .cl-item:hover { background: rgba(255,255,255,0.02); }
  .cl-check { width: 16px; height: 16px; border: 1.5px solid var(--border); border-radius: 2px; flex-shrink: 0; margin-top: 2px; }
  .cl-label { font-weight: 600; min-width: 180px; font-size: 0.83rem; }
  .cl-spec { color: var(--muted); font-size: 0.8rem; }
  .cl-test { padding: 8px 10px; border-bottom: 1px solid rgba(46,51,74,0.6); font-size: 0.84rem; }
  .cl-test-name { font-weight: 600; }
  .cl-test-line { color: var(--muted); font-family: var(--mono); font-size: 0.78rem; }
  .data-row { display: flex; gap: 16px; margin-bottom: 8px; }
  .data-field { flex: 1; }
  .data-label { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); text-transform: uppercase; margin-bottom: 2px; }
  .data-value { font-size: 0.88rem; font-weight: 600; color: var(--text); }
  .info-pill { display: inline-flex; align-items: center; gap: 6px; background: rgba(58,142,255,0.1); border: 1px solid rgba(58,142,255,0.25); color: var(--accent2); border-radius: 20px; padding: 4px 12px; font-size: 0.76rem; font-family: var(--mono); margin-right: 8px; }
  .stTextInput > div > div > input, .stSelectbox > div > div { background: var(--surface2) !important; border-color: var(--border) !important; color: var(--text) !important; }
  [data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 6px !important; background: var(--surface) !important; }
  [data-testid="stMetricValue"] { color: var(--accent) !important; }
  hr { border-color: var(--border) !important; margin: 20px 0 !important; }
  ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: var(--bg); } ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── HEADER ────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>⚙ GENERADOR DE CHECKLIST QC</h1>
  <p>Inspección de Control de Calidad · Integración Chasis–Carrocería · Contratos Estado Peruano</p>
  <div>
    <span class="badge">v1.0</span>
    <span class="badge">IA · Gemini 2.5 Flash</span>
    <span class="badge">PDF · TDR / OFERTA TÉCNICA</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────── SIDEBAR ───────────────────────────────
with st.sidebar:
    st.markdown("### ⚙ Configuración")
    api_key_input = st.text_input(
        "GEMINI_API_KEY",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Obtén tu key gratuita en aistudio.google.com",
        placeholder="AIza..."
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input

    st.markdown("---")
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    1. **Sube** tus PDFs (TDR y/o Oferta Técnica)
    2. Haz clic en **Generar Checklist**
    3. **Revisa** la vista previa
    4. **Descarga** el HTML y abre en el navegador
    5. Usa **Ctrl+P** para imprimir o guardar PDF
    """)
    st.markdown("---")
    st.caption("Desarrollado para ingeniería de campo · Uso con portapapeles en taller")

# ─────────────────────────── MAIN LAYOUT ───────────────────────────
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown('<div class="panel-title">📁 CARGA DE DOCUMENTOS</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        label="Arrastra y suelta tus PDFs aquí",
        type=["pdf"],
        accept_multiple_files=True,
        help="Puedes subir las Bases Técnicas (TDR) y/o la Oferta Técnica en PDF.",
    )
    if uploaded_files:
        st.markdown(f'<div class="status-ok">✓ {len(uploaded_files)} archivo(s) cargado(s)</div>', unsafe_allow_html=True)
        for f in uploaded_files:
            st.markdown(f'<span class="info-pill">📄 {f.name} · {round(f.size/1024,1)} KB</span>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warn">⚠ Ningún archivo cargado</div>', unsafe_allow_html=True)

    st.markdown("---")
    api_ready = bool(os.getenv("GEMINI_API_KEY"))
    files_ready = bool(uploaded_files)
    if not api_ready:
        st.markdown('<div class="status-err">✗ Falta GEMINI_API_KEY · Configura en el sidebar</div>', unsafe_allow_html=True)

    generate_btn = st.button(
        "🔍 GENERAR CHECKLIST",
        disabled=(not files_ready or not api_ready),
        use_container_width=True,
    )

    if "checklist_data" in st.session_state and st.session_state.checklist_data:
        data = st.session_state.checklist_data
        st.markdown("---")
        st.markdown('<div class="panel-title">📊 RESUMEN</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Ítems Físicos", len(data.get("verificacion_fisica", [])))
        c2.metric("Accesorios", len(data.get("accesorios_adicionales", [])))
        c3, c4 = st.columns(2)
        c3.metric("Pruebas", len(data.get("pruebas_funcionamiento", [])))
        c4.metric("Tipo", data.get("tipo_maquina", "—")[:12])

# ─────────────────────────── GENERATION LOGIC ──────────────────────
if generate_btn and uploaded_files:
    with col_right:
        with st.spinner("Extrayendo texto de PDFs..."):
            try:
                pdf_text = extract_pdf_text(uploaded_files)
                st.markdown(f'<div class="status-ok">✓ Texto extraído · {len(pdf_text):,} caracteres</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="status-err">✗ Error leyendo PDFs: {e}</div>', unsafe_allow_html=True)
                st.stop()

        with st.spinner("Analizando con IA · Gemini 2.0 Flash..."):
            try:
                checklist_data = generate_checklist_with_llm(pdf_text)
                st.session_state.checklist_data = checklist_data
                st.session_state.generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.markdown('<div class="status-ok">✓ Checklist generado exitosamente</div>', unsafe_allow_html=True)
            except json.JSONDecodeError as e:
                st.markdown(f'<div class="status-err">✗ Error parseando respuesta del LLM: {e}</div>', unsafe_allow_html=True)
                st.stop()
            except Exception as e:
                st.markdown(f'<div class="status-err">✗ Error en API: {e}</div>', unsafe_allow_html=True)
                st.stop()
        st.rerun()

# ─────────────────────────── CHECKLIST PREVIEW ─────────────────────
with col_right:
    if "checklist_data" in st.session_state and st.session_state.checklist_data:
        data = st.session_state.checklist_data
        gen_at = st.session_state.get("generated_at", "—")

        st.markdown('<div class="panel-title">📤 EXPORTAR</div>', unsafe_allow_html=True)
        ex_col1, ex_col2 = st.columns(2)
        html_content = generate_html_checklist(data, gen_at)

        with ex_col1:
            st.download_button(
                label="⬇ DESCARGAR HTML (IMPRIMIR)",
                data=html_content,
                file_name=f"checklist_qc_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
                use_container_width=True,
                help="Abre en el navegador y usa Ctrl+P para imprimir en PDF"
            )
        with ex_col2:
            st.download_button(
                label="⬇ DESCARGAR JSON",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"checklist_qc_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown('<div class="panel-title">👁 VISTA PREVIA DEL CHECKLIST</div>', unsafe_allow_html=True)
        st.markdown('<div class="checklist-preview">', unsafe_allow_html=True)

        # SECCIÓN 1
        st.markdown('<div class="cl-section-title">§ 1 · DATOS DEL EQUIPO</div>', unsafe_allow_html=True)
        eq = data.get("datos_equipo", {})
        st.markdown(f"""
        <div class="data-row">
          <div class="data-field"><div class="data-label">Entidad Destino</div><div class="data-value">{eq.get('entidad_destino','—')}</div></div>
          <div class="data-field"><div class="data-label">Tipo de Vehículo</div><div class="data-value">{eq.get('tipo_vehiculo','—')}</div></div>
        </div>
        <div class="data-row">
          <div class="data-field"><div class="data-label">Marca / Modelo Chasis</div><div class="data-value">{eq.get('marca_chasis','—')}</div></div>
          <div class="data-field"><div class="data-label">Carrocero</div><div class="data-value">{eq.get('nombre_carrocero','—')}</div></div>
        </div>
        <div class="data-row">
          <div class="data-field"><div class="data-label">Tipo de Máquina</div><div class="data-value">{data.get('tipo_maquina','—')}</div></div>
          <div class="data-field"><div class="data-label">Fecha Generación</div><div class="data-value">{gen_at}</div></div>
        </div>""", unsafe_allow_html=True)

        # SECCIÓN 2
        st.markdown('<div class="cl-section-title">§ 2 · VERIFICACIÓN FÍSICA Y DIMENSIONAL</div>', unsafe_allow_html=True)
        cats = {}
        for item in data.get("verificacion_fisica", []):
            cats.setdefault(item.get("categoria", "General"), []).append(item)
        for cat, items in cats.items():
            st.markdown(f'<div style="padding:4px 8px;font-family:var(--mono);font-size:0.7rem;color:var(--accent2);margin-top:8px;">▸ {cat.upper()}</div>', unsafe_allow_html=True)
            for item in items:
                st.markdown(f"""<div class="cl-item"><div class="cl-check"></div><div style="flex:1"><span class="cl-label">{item.get('item','')}</span><span class="cl-spec"> — {item.get('especificacion','')}</span></div><div style="width:80px;text-align:center;font-family:var(--mono);font-size:0.7rem;color:var(--muted)">SÍ / NO / OBS</div></div>""", unsafe_allow_html=True)

        # SECCIÓN 3
        st.markdown('<div class="cl-section-title">§ 3 · ACCESORIOS ADICIONALES OFERTADOS</div>', unsafe_allow_html=True)
        for acc in data.get("accesorios_adicionales", []):
            st.markdown(f"""<div class="cl-item"><div class="cl-check"></div><div style="flex:1"><span class="cl-label">{acc.get('item','')}</span><span class="cl-spec"> — {acc.get('descripcion','')}</span></div><div style="width:50px;text-align:center;font-family:var(--mono);font-size:0.7rem;color:var(--muted)">✓ / ✗</div></div>""", unsafe_allow_html=True)

        # SECCIÓN 4
        st.markdown('<div class="cl-section-title">§ 4 · PRUEBAS DE FUNCIONAMIENTO</div>', unsafe_allow_html=True)
        for p in data.get("pruebas_funcionamiento", []):
            ref = p.get("valor_referencia", "")
            ref_text = f" <span style='color:var(--accent2);font-size:0.75rem'>[Ref: {ref}]</span>" if ref else ""
            st.markdown(f"""<div class="cl-test"><div class="cl-test-name">{p.get('prueba','')}{ref_text}</div><div class="cl-test-line">Resultado ({p.get('unidad','')}): _________________________________</div></div>""", unsafe_allow_html=True)

        # SECCIÓN 5
        st.markdown('<div class="cl-section-title">§ 5 · FIRMAS Y APROBACIÓN</div>', unsafe_allow_html=True)
        st.markdown("""<div style="display:flex;gap:32px;padding:16px 8px;"><div style="flex:1;text-align:center;"><div style="border-top:1px solid var(--border);padding-top:8px;margin-top:48px;"></div><div style="font-family:var(--mono);font-size:0.78rem;color:var(--muted);">INGENIERO INSPECTOR</div><div style="font-size:0.8rem;color:var(--text);margin-top:4px;">Nombre / CIP</div></div><div style="flex:1;text-align:center;"><div style="border-top:1px solid var(--border);padding-top:8px;margin-top:48px;"></div><div style="font-family:var(--mono);font-size:0.78rem;color:var(--muted);">JEFE DE TALLER · CARROCERO</div><div style="font-size:0.8rem;color:var(--text);margin-top:4px;">Nombre / DNI</div></div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("🔬 Ver JSON completo generado por IA"):
            st.json(data)

    else:
        st.markdown("""<div style="text-align:center;padding:80px 40px;color:#7a8099;border:2px dashed #2e334a;border-radius:8px;background:#1a1d27;"><div style="font-size:3rem;margin-bottom:16px;">📋</div><div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;margin-bottom:8px;color:#e8eaf0;">Checklist pendiente de generación</div><div style="font-size:0.82rem;">Sube tus PDFs (TDR / Oferta Técnica) y presiona <strong>Generar Checklist</strong></div></div>""", unsafe_allow_html=True)
