"""
Generador de Checklist de Inspección · Control de Calidad
Aplicación Streamlit · Google Gemini API · Diseño claro y minimalista
"""

import streamlit as st
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from checklist_generator import generate_checklist_from_pdfs
from export_utils import generate_html_checklist

# ─────────────────────────── PAGE CONFIG ───────────────────────────
st.set_page_config(
    page_title="Checklist · Control de Calidad · Vehículos Especiales",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────── CSS ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg:        #f8f9fb;
  --surface:   #ffffff;
  --surface2:  #f1f3f7;
  --border:    #dde1ea;
  --border2:   #c8cdd8;
  --accent:    #2554c7;
  --accent-lt: #eef2fc;
  --text:      #1a1d2e;
  --text-2:    #4a5068;
  --text-3:    #8890a8;
  --success:   #15803d;
  --success-lt:#dcfce7;
  --danger:    #b91c1c;
  --danger-lt: #fee2e2;
  --warn-lt:   #fef9ec;
  --warn:      #92400e;
  --mono:      'JetBrains Mono', monospace;
  --sans:      'Inter', sans-serif;
}

/* ── Reset global ── */
html, body, [class*="css"] {
  font-family: var(--sans) !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

/* ── Header ── */
.app-header {
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
  border-radius: 6px;
  padding: 20px 28px;
  margin-bottom: 24px;
}
.app-header h1 {
  font-family: var(--sans) !important;
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  margin: 0 0 4px 0 !important;
  letter-spacing: -0.01em !important;
}
.app-header p {
  color: var(--text-2) !important;
  font-size: 0.85rem !important;
  margin: 0 !important;
}
.badge {
  display: inline-block;
  background: var(--accent-lt);
  color: var(--accent);
  border: 1px solid #c7d7f8;
  border-radius: 4px;
  font-family: var(--mono);
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 8px;
  margin-right: 6px;
  margin-top: 10px;
}

/* ── Panel labels ── */
.panel-title {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: var(--text-3) !important;
  margin-bottom: 12px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 2px dashed var(--border2) !important;
  border-radius: 8px !important;
  transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
}

/* ── Primary button ── */
.stButton > button {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 6px !important;
  font-family: var(--sans) !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  padding: 10px 20px !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  background: #1d44a8 !important;
  box-shadow: 0 2px 8px rgba(37,84,199,0.25) !important;
}
.stButton > button:disabled {
  background: var(--border2) !important;
  color: var(--text-3) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
  background: var(--surface) !important;
  color: var(--accent) !important;
  border: 1.5px solid var(--accent) !important;
  border-radius: 6px !important;
  font-family: var(--sans) !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  padding: 8px 16px !important;
  transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
  background: var(--accent-lt) !important;
}

/* ── Status messages ── */
.status-ok  { background:var(--success-lt); border:1px solid #86efac; border-radius:5px; padding:9px 14px; color:var(--success);  font-size:0.82rem; margin-bottom:10px; }
.status-err { background:var(--danger-lt);  border:1px solid #fca5a5; border-radius:5px; padding:9px 14px; color:var(--danger);   font-size:0.82rem; margin-bottom:10px; }
.status-warn{ background:var(--warn-lt);    border:1px solid #fcd34d; border-radius:5px; padding:9px 14px; color:var(--warn);     font-size:0.82rem; margin-bottom:10px; }

/* ── Info pill ── */
.info-pill {
  display: inline-flex;
  align-items: center;
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text-2);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 0.75rem;
  margin-right: 6px;
  margin-top: 4px;
}

/* ── Metric values ── */
[data-testid="stMetricValue"] { color: var(--accent) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  background: var(--surface) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 16px 0 !important; }

/* ══════════════════════════════════════════════
   CHECKLIST PREVIEW
══════════════════════════════════════════════ */
.cl-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

/* Encabezado de sección */
.cl-sec {
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  padding: 7px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 0;
}
.cl-sec-num {
  background: var(--accent);
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}
.cl-sec-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-2);
}

/* Bloque de datos equipo */
.eq-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}
.eq-cell {
  padding: 10px 16px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.eq-cell:nth-child(even) { border-right: none; }
.eq-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-3);
  margin-bottom: 2px;
  font-weight: 600;
}
.eq-value {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text);
}

/* Subcategoría */
.cl-cat {
  background: #f0f4ff;
  border-bottom: 1px solid var(--border);
  border-top: 1px solid var(--border);
  padding: 4px 16px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--accent);
}

/* Tabla de ítems — cabecera */
.cl-thead {
  display: grid;
  grid-template-columns: 1fr 1.4fr 44px 44px 1fr;
  background: #f8f9fb;
  border-bottom: 1.5px solid var(--border2);
  padding: 5px 16px;
  gap: 8px;
}
.cl-th {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-3);
  text-align: center;
}
.cl-th:first-child { text-align: left; }
.cl-th:last-child  { text-align: left; }

/* Fila de ítem */
.cl-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr 44px 44px 1fr;
  align-items: center;
  padding: 7px 16px;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}
.cl-row:last-child  { border-bottom: none; }
.cl-row:hover { background: #fafbff; }
.cl-item-name { font-size: 0.83rem; font-weight: 600; color: var(--text); }
.cl-item-spec { font-size: 0.79rem; color: var(--text-2); }
.cl-box-cell  { display: flex; justify-content: center; }
.cl-box {
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--border2);
  border-radius: 3px;
  background: #fff;
  flex-shrink: 0;
}
.cl-obs-line {
  height: 18px;
  border-bottom: 1px solid var(--border2);
  width: 100%;
  display: block;
}

/* Fila prueba funcionamiento */
.cl-test-row {
  display: grid;
  grid-template-columns: 1fr 120px 44px 44px;
  align-items: center;
  padding: 8px 16px;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}
.cl-test-row:last-child { border-bottom: none; }
.cl-test-row:hover { background: #fafbff; }
.cl-test-name { font-size: 0.83rem; font-weight: 600; color: var(--text); }
.cl-test-ref  { font-size: 0.72rem; color: var(--accent); font-family: var(--mono); margin-top: 2px; }
.cl-test-result {
  height: 18px;
  border-bottom: 1px solid var(--border2);
  font-size: 0.72rem;
  color: var(--text-3);
  display: flex;
  align-items: flex-end;
  padding-bottom: 1px;
}
.cl-test-unit {
  font-size: 0.7rem;
  color: var(--text-3);
  font-family: var(--mono);
  text-align: center;
}
.cl-conform-cell { display: flex; justify-content: center; }
.cl-conform-box {
  width: 18px; height: 18px;
  border: 1.5px solid var(--border2);
  border-radius: 3px;
  background: #fff;
}

/* Firmas */
.cl-sigs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 20px 24px 16px;
}
.cl-sig { text-align: center; }
.cl-sig-space {
  height: 48px;
  border-bottom: 1.5px solid var(--text-2);
  margin-bottom: 6px;
}
.cl-sig-name {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
}
.cl-sig-role { font-size: 0.72rem; color: var(--text-3); margin-top: 2px; }

/* Empty state */
.cl-empty {
  padding: 12px 16px;
  font-size: 0.82rem;
  color: var(--text-3);
  font-style: italic;
}

/* ── Empty state general ── */
.empty-state {
  text-align: center;
  padding: 64px 40px;
  color: var(--text-3);
  border: 2px dashed var(--border2);
  border-radius: 8px;
  background: var(--surface);
}
.empty-state .icon { font-size: 2.5rem; margin-bottom: 12px; }
.empty-state .title { font-size: 0.95rem; font-weight: 600; color: var(--text-2); margin-bottom: 6px; }
.empty-state .sub   { font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── HEADER ────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🔧 Generador de Checklist de Inspección · Control de Calidad</h1>
  <p>Control de Calidad · Integración Chasis–Carrocería · Contratos Estado Peruano</p>
  <div>
    <span class="badge">v1.1</span>
    <span class="badge">Gemini 2.5 Flash</span>
    <span class="badge">TDR / Oferta Técnica</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────── SIDEBAR ───────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    1. **Sube** tus PDFs (TDR y/o Oferta Técnica)
    2. Haz clic en **Generar Checklist**
    3. **Revisa** la vista previa
    4. **Descarga** el HTML y ábrelo en Chrome/Edge
    5. Usa **Ctrl+P** para imprimir o guardar como PDF
    """)
    st.markdown("---")
    st.caption("Desarrollado para ingeniería de campo · iMetales")


# ─────────────────────────── LAYOUT ────────────────────────────────
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown('<div class="panel-title">📁 Carga de Documentos</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        label="Arrastra y suelta tus PDFs aquí",
        type=["pdf"],
        accept_multiple_files=True,
        help="Puedes subir las Bases Técnicas (TDR) y/o la Oferta Técnica. Se aceptan PDFs escaneados.",
    )

    if uploaded_files:
        st.markdown(
            f'<div class="status-ok">✓ {len(uploaded_files)} archivo(s) cargado(s)</div>',
            unsafe_allow_html=True
        )
        for f in uploaded_files:
            st.markdown(
                f'<span class="info-pill">📄 {f.name} · {round(f.size/1024,1)} KB</span>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<div class="status-warn">Ningún archivo cargado aún.</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    api_ready   = bool(os.getenv("GEMINI_API_KEY"))
    files_ready = bool(uploaded_files)

    if not api_ready:
        st.markdown(
            '<div class="status-err">✗ Falta GEMINI_API_KEY · Configúrala en Streamlit Cloud → Settings → Secrets</div>',
            unsafe_allow_html=True
        )

    generate_btn = st.button(
        "🔍 Generar Checklist",
        disabled=(not files_ready or not api_ready),
        use_container_width=True,
    )

    if "checklist_data" in st.session_state and st.session_state.checklist_data:
        data = st.session_state.checklist_data
        st.markdown("---")
        st.markdown('<div class="panel-title">📊 Resumen</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Ítems Físicos",  len(data.get("verificacion_fisica", [])))
        c2.metric("Accesorios",     len(data.get("accesorios_adicionales", [])))
        c3, c4 = st.columns(2)
        c3.metric("Pruebas",        len(data.get("pruebas_funcionamiento", [])))
        c4.metric("Tipo",           data.get("tipo_maquina", "—")[:14])


# ─────────────────────────── GENERACIÓN ────────────────────────────
if generate_btn and uploaded_files:
    with col_right:
        with st.spinner("Analizando documentos con Gemini 2.5 Flash…"):
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                checklist_data, proc_stats = generate_checklist_from_pdfs(uploaded_files, api_key)
                method = proc_stats.get("method", "texto")
                tp = proc_stats.get("text_pages", 0)
                sp = proc_stats.get("scanned_pages", 0)
                label = "texto digital" if method == "texto" else "OCR · páginas escaneadas"
                st.markdown(
                    f'<div class="status-ok">✓ {tp} págs. con texto · {sp} págs. escaneadas · Método: {label}</div>',
                    unsafe_allow_html=True
                )
                st.session_state.checklist_data  = checklist_data
                st.session_state.generated_at    = datetime.now(ZoneInfo("America/Lima")).strftime("%d/%m/%Y")
            except json.JSONDecodeError as e:
                st.markdown(f'<div class="status-err">✗ Error al parsear respuesta de Gemini: {e}</div>', unsafe_allow_html=True)
                st.stop()
            except Exception as e:
                st.markdown(f'<div class="status-err">✗ Error: {e}</div>', unsafe_allow_html=True)
                st.stop()
        st.rerun()


# ─────────────────────────── VISTA PREVIA ──────────────────────────
with col_right:
    if "checklist_data" in st.session_state and st.session_state.checklist_data:
        data   = st.session_state.checklist_data
        gen_at = st.session_state.get("generated_at", "—")

        # ── Botones de exportación ──────────────────────────────────
        st.markdown('<div class="panel-title">📤 Exportar</div>', unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        html_content = generate_html_checklist(data, gen_at)

        with ex1:
            st.download_button(
                label="⬇ Descargar HTML (imprimir)",
                data=html_content,
                file_name=f"checklist_qc_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
                use_container_width=True,
                help="Abre en Chrome/Edge y usa Ctrl+P para imprimir o guardar como PDF",
            )
        with ex2:
            st.download_button(
                label="⬇ Descargar JSON",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"checklist_qc_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown('<div class="panel-title">👁 Vista Previa</div>', unsafe_allow_html=True)

        eq = data.get("datos_equipo", {})

        st.markdown('<div class="cl-wrap">', unsafe_allow_html=True)

        # ── SECCIÓN 1: DATOS DEL EQUIPO ─────────────────────────────
        st.markdown("""
        <div class="cl-sec">
          <span class="cl-sec-num">1</span>
          <span class="cl-sec-label">Datos del Equipo</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="eq-grid">
          <div class="eq-cell">
            <div class="eq-label">Entidad Destino</div>
            <div class="eq-value">{eq.get('entidad_destino','—')}</div>
          </div>
          <div class="eq-cell">
            <div class="eq-label">Tipo de Vehículo</div>
            <div class="eq-value">{eq.get('tipo_vehiculo','—')}</div>
          </div>
          <div class="eq-cell">
            <div class="eq-label">Marca / Modelo Chasis</div>
            <div class="eq-value">{eq.get('marca_chasis','—')}</div>
          </div>
          <div class="eq-cell">
            <div class="eq-label">Carrocero</div>
            <div class="eq-value">{eq.get('nombre_carrocero','—')}</div>
          </div>
          <div class="eq-cell">
            <div class="eq-label">Tipo de Máquina</div>
            <div class="eq-value">{data.get('tipo_maquina','—')}</div>
          </div>
          <div class="eq-cell">
            <div class="eq-label">Fecha de Generación</div>
            <div class="eq-value">{gen_at}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── SECCIÓN 2: VERIFICACIÓN FÍSICA ──────────────────────────
        st.markdown("""
        <div class="cl-sec" style="margin-top:0; border-top:1px solid var(--border);">
          <span class="cl-sec-num">2</span>
          <span class="cl-sec-label">Verificación Física y Dimensional</span>
        </div>
        """, unsafe_allow_html=True)

        verificacion = data.get("verificacion_fisica", [])
        if verificacion:
            # Cabecera de columnas
            st.markdown("""
            <div class="cl-thead">
              <div class="cl-th">Ítem</div>
              <div class="cl-th" style="text-align:left">Especificación Requerida</div>
              <div class="cl-th">Sí</div>
              <div class="cl-th">No</div>
              <div class="cl-th">Observaciones</div>
            </div>
            """, unsafe_allow_html=True)

            cats = {}
            for item in verificacion:
                cats.setdefault(item.get("categoria", "General"), []).append(item)

            for cat, items in cats.items():
                st.markdown(f'<div class="cl-cat">▸ {cat}</div>', unsafe_allow_html=True)
                rows_html = ""
                for item in items:
                    rows_html += f"""
                    <div class="cl-row">
                      <div class="cl-item-name">{item.get('item','')}</div>
                      <div class="cl-item-spec">{item.get('especificacion','')}</div>
                      <div class="cl-box-cell"><div class="cl-box"></div></div>
                      <div class="cl-box-cell"><div class="cl-box"></div></div>
                      <div><span class="cl-obs-line"></span></div>
                    </div>"""
                st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="cl-empty">No se identificaron ítems de verificación física.</div>', unsafe_allow_html=True)

        # ── SECCIÓN 3: ACCESORIOS ────────────────────────────────────
        st.markdown("""
        <div class="cl-sec" style="border-top:1px solid var(--border);">
          <span class="cl-sec-num">3</span>
          <span class="cl-sec-label">Accesorios Adicionales Ofertados</span>
        </div>
        """, unsafe_allow_html=True)

        accesorios = data.get("accesorios_adicionales", [])
        if accesorios:
            st.markdown("""
            <div class="cl-thead" style="grid-template-columns:1fr 2fr 44px 44px;">
              <div class="cl-th">Accesorio</div>
              <div class="cl-th" style="text-align:left">Descripción</div>
              <div class="cl-th">Sí</div>
              <div class="cl-th">No</div>
            </div>
            """, unsafe_allow_html=True)
            rows_html = ""
            for acc in accesorios:
                rows_html += f"""
                <div class="cl-row" style="grid-template-columns:1fr 2fr 44px 44px;">
                  <div class="cl-item-name">{acc.get('item','')}</div>
                  <div class="cl-item-spec">{acc.get('descripcion','')}</div>
                  <div class="cl-box-cell"><div class="cl-box"></div></div>
                  <div class="cl-box-cell"><div class="cl-box"></div></div>
                </div>"""
            st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="cl-empty">No se identificaron accesorios adicionales.</div>', unsafe_allow_html=True)

        # ── SECCIÓN 4: PRUEBAS ───────────────────────────────────────
        st.markdown("""
        <div class="cl-sec" style="border-top:1px solid var(--border);">
          <span class="cl-sec-num">4</span>
          <span class="cl-sec-label">Pruebas de Funcionamiento</span>
        </div>
        """, unsafe_allow_html=True)

        pruebas = data.get("pruebas_funcionamiento", [])
        if pruebas:
            st.markdown("""
            <div class="cl-thead" style="grid-template-columns:1fr 120px 44px 44px;">
              <div class="cl-th">Prueba</div>
              <div class="cl-th">Resultado</div>
              <div class="cl-th">✓</div>
              <div class="cl-th">✗</div>
            </div>
            """, unsafe_allow_html=True)
            rows_html = ""
            for p in pruebas:
                ref  = p.get("valor_referencia", "")
                ref_html = f'<div class="cl-test-ref">Ref: {ref}</div>' if ref else ""
                rows_html += f"""
                <div class="cl-test-row">
                  <div>
                    <div class="cl-test-name">{p.get('prueba','')}</div>
                    {ref_html}
                  </div>
                  <div>
                    <div class="cl-test-result"></div>
                    <div class="cl-test-unit">{p.get('unidad','')}</div>
                  </div>
                  <div class="cl-conform-cell"><div class="cl-conform-box"></div></div>
                  <div class="cl-conform-cell"><div class="cl-conform-box"></div></div>
                </div>"""
            st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="cl-empty">No se identificaron pruebas de funcionamiento.</div>', unsafe_allow_html=True)

        # ── SECCIÓN 5: FIRMAS ────────────────────────────────────────
        st.markdown("""
        <div class="cl-sec" style="border-top:1px solid var(--border);">
          <span class="cl-sec-num">5</span>
          <span class="cl-sec-label">Firmas y Aprobación</span>
        </div>
        <div class="cl-sigs">
          <div class="cl-sig">
            <div class="cl-sig-space"></div>
            <div class="cl-sig-name">Ingeniero Inspector</div>
            <div class="cl-sig-role">Empresa Contratista · Responsable Control de Calidad · DNI: ____________</div>
          </div>
          <div class="cl-sig">
            <div class="cl-sig-space"></div>
            <div class="cl-sig-name">Jefe de Taller · Carrocero</div>
            <div class="cl-sig-role">Empresa Carrocera · Responsable de Producción · DNI: ____________</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # cierra .cl-wrap

        # ── JSON expander ────────────────────────────────────────────
        with st.expander("Ver JSON completo"):
            st.json(data)

    else:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">📋</div>
          <div class="title">Checklist pendiente de generación</div>
          <div class="sub">Sube tus PDFs (TDR / Oferta Técnica) y presiona <strong>Generar Checklist</strong></div>
        </div>
        """, unsafe_allow_html=True)
