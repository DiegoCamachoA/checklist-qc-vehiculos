"""
export_utils.py
Generación del checklist en HTML optimizado para impresión.
Diseño tipo "portapapeles de taller": limpio, robusto, funcional.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def generate_html_checklist(data: dict, generated_at: str = "") -> str:
    """
    Genera un archivo HTML completo, autocontenido y optimizado para impresión.
    El usuario puede abrir este archivo en cualquier navegador y usar Ctrl+P para imprimir.

    Args:
        data: Diccionario con la estructura del checklist generado por el LLM.
        generated_at: Timestamp de generación para incluir en el documento.

    Returns:
        String con el HTML completo listo para descargar.
    """
    eq = data.get("datos_equipo", {})
    tipo = data.get("tipo_maquina", "Vehículo Especial")
    verificacion = data.get("verificacion_fisica", [])
    accesorios = data.get("accesorios_adicionales", [])
    pruebas = data.get("pruebas_funcionamiento", [])
    if not generated_at:
        generated_at = datetime.now(ZoneInfo("America/Lima")).strftime("%d/%m/%Y")

    # ── SECCIÓN 2: Verificación Física (agrupada por categoría) ──────
    cats: dict = {}
    for item in verificacion:
        cat = item.get("categoria", "General")
        cats.setdefault(cat, []).append(item)

    sec2_rows = ""
    row_num = 1
    for cat, items in cats.items():
        sec2_rows += f"""
        <tr class="cat-header">
          <td colspan="4" class="cat-title">▸ {cat.upper()}</td>
        </tr>"""
        for item in items:
            sec2_rows += f"""
        <tr>
          <td class="num">{row_num}</td>
          <td class="item-name">{item.get('item', '')}</td>
          <td class="spec">{item.get('especificacion', '')}</td>
          <td class="check-cell">
            <span class="check-box"></span> Sí
            <span class="check-box"></span> No
            <span class="obs-line"></span>
          </td>
        </tr>"""
        row_num += 1

    if not sec2_rows:
        sec2_rows = '<tr><td colspan="4" class="empty-row">No se identificaron ítems de verificación física.</td></tr>'

    # ── SECCIÓN 3: Accesorios ─────────────────────────────────────────
    sec3_rows = ""
    for i, acc in enumerate(accesorios, 1):
        sec3_rows += f"""
        <tr>
          <td class="num">{i}</td>
          <td class="item-name">{acc.get('item', '')}</td>
          <td class="spec">{acc.get('descripcion', '')}</td>
          <td class="check-cell check-center">
            <span class="check-box"></span> Presente
            <span class="check-box"></span> Faltante
          </td>
        </tr>"""
    if not sec3_rows:
        sec3_rows = '<tr><td colspan="4" class="empty-row">No se identificaron accesorios adicionales.</td></tr>'

    # ── SECCIÓN 4: Pruebas de Funcionamiento ─────────────────────────
    sec4_html = ""
    for i, p in enumerate(pruebas, 1):
        ref = p.get("valor_referencia", "")
        ref_text = f'<span class="ref-val">Ref: {ref}</span>' if ref else ""
        sec4_html += f"""
      <div class="test-row">
        <div class="test-num">{i:02d}</div>
        <div class="test-body">
          <div class="test-name">{p.get('prueba', '')} {ref_text}</div>
          <div class="test-fill">
            Resultado ({p.get('unidad', 'valor')}): <span class="fill-line"></span>
          </div>
          <div class="test-obs">Observaciones: <span class="fill-line long"></span></div>
        </div>
        <div class="test-result">
          <span class="check-box"></span> CONFORME<br>
          <span class="check-box"></span> NO CONFORME
        </div>
      </div>"""

    if not sec4_html:
        sec4_html = '<p class="empty-msg">No se identificaron pruebas de funcionamiento.</p>'

    # ── HTML COMPLETO ─────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Checklist de Control de Calidad · {tipo}</title>
  <style>
    /* ── Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;600&display=swap');

    /* ── Reset ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Roboto', sans-serif;
      font-size: 9.5pt;
      color: #1a1a1a;
      background: #f0f0f0;
      line-height: 1.4;
    }}

    /* ── Page wrapper ── */
    .page {{
      max-width: 210mm;
      margin: 0 auto;
      background: white;
      padding: 12mm 14mm;
    }}

    /* ── HEADER ── */
    .doc-header {{
      border: 2px solid #1a1a1a;
      margin-bottom: 10px;
      display: grid;
      grid-template-columns: auto 1fr auto;
    }}
    .header-logo {{
      padding: 10px 14px;
      border-right: 2px solid #1a1a1a;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .logo-icon {{
      font-size: 28px;
      line-height: 1;
    }}
    .header-title {{
      padding: 8px 14px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .doc-title {{
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 14pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #1a1a1a;
    }}
    .doc-subtitle {{
      font-size: 8pt;
      color: #444;
      margin-top: 2px;
      font-family: 'Roboto Mono', monospace;
    }}
    .header-meta {{
      padding: 8px 12px;
      border-left: 2px solid #1a1a1a;
      font-family: 'Roboto Mono', monospace;
      font-size: 7.5pt;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 3px;
      min-width: 120px;
      background: #f8f8f8;
    }}
    .meta-label {{ color: #888; text-transform: uppercase; font-size: 6.5pt; }}
    .meta-value {{ color: #1a1a1a; font-weight: 600; }}

    /* ── Machine type banner ── */
    .machine-banner {{
      background: #1e3a8a;
      color: white;
      padding: 5px 14px;
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 10pt;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .machine-banner .tag {{
      background: #1e3a8a;
      color: white;
      padding: 1px 8px;
      font-size: 7.5pt;
      border-radius: 2px;
    }}

    /* ── Section titles ── */
    .section {{
      margin-bottom: 12px;
      page-break-inside: avoid;
    }}
    .section-header {{
      background: #1e3a8a;
      color: white;
      padding: 4px 10px;
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 8.5pt;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 0;
    }}
    .section-num {{
      background: white;
      color: #1e3a8a;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 8pt;
      font-weight: 700;
      flex-shrink: 0;
    }}

    /* ── Section 1: Datos del equipo ── */
    .data-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      border: 1px solid #ccc;
      border-top: none;
    }}
    .data-cell {{
      padding: 5px 10px;
      border-right: 1px solid #ddd;
      border-bottom: 1px solid #ddd;
    }}
    .data-cell:nth-child(even) {{ border-right: none; }}
    .data-label {{
      font-size: 6.5pt;
      text-transform: uppercase;
      color: #888;
      font-family: 'Roboto Mono', monospace;
      letter-spacing: 0.05em;
      margin-bottom: 2px;
    }}
    .data-value {{
      font-size: 9pt;
      font-weight: 700;
      color: #1a1a1a;
      min-height: 14px;
    }}
    .data-line {{
      border-bottom: 1px solid #aaa;
      min-width: 120px;
      display: inline-block;
      min-height: 14px;
    }}

    /* ── Tables (sec 2 & 3) ── */
    .check-table {{
      width: 100%;
      border-collapse: collapse;
      border: 1px solid #ccc;
      border-top: none;
      font-size: 8.5pt;
    }}
    .check-table th {{
      background: #e8e8e8;
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 7.5pt;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 4px 8px;
      border: 1px solid #ccc;
      text-align: left;
    }}
    .check-table td {{
      padding: 4px 8px;
      border: 1px solid #e0e0e0;
      vertical-align: middle;
    }}
    .check-table tr:nth-child(even) td {{ background: #fafafa; }}
    .check-table tr:hover td {{ background: #f5f8ff; }}

    .cat-header td {{ background: none !important; }}
    .cat-title {{
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 7.5pt;
      font-weight: 700;
      text-transform: uppercase;
      color: #2864c8;
      letter-spacing: 0.08em;
      padding: 4px 8px !important;
      border-top: 1px solid #ddd !important;
      background: #f0f5ff !important;
    }}
    .num {{
      text-align: center;
      width: 24px;
      font-family: 'Roboto Mono', monospace;
      font-size: 7.5pt;
      color: #888;
    }}
    .item-name {{
      font-weight: 700;
      width: 28%;
      font-size: 8.5pt;
    }}
    .spec {{
      color: #333;
      width: 38%;
      font-size: 8pt;
    }}
    .check-cell {{
      width: 18%;
      font-size: 8pt;
      white-space: nowrap;
    }}
    .check-center {{ text-align: center; }}
    .check-box {{
      display: inline-block;
      width: 11px;
      height: 11px;
      border: 1.5px solid #555;
      border-radius: 1px;
      vertical-align: middle;
      margin-right: 2px;
    }}
    .obs-line {{
      display: inline-block;
      width: 60px;
      border-bottom: 1px solid #aaa;
      vertical-align: bottom;
      margin-left: 4px;
    }}
    .empty-row {{
      text-align: center;
      color: #aaa;
      font-style: italic;
      padding: 10px !important;
    }}

    /* ── Section 4: Pruebas ── */
    .tests-container {{
      border: 1px solid #ccc;
      border-top: none;
    }}
    .test-row {{
      display: flex;
      align-items: stretch;
      border-bottom: 1px solid #e0e0e0;
      min-height: 44px;
    }}
    .test-row:last-child {{ border-bottom: none; }}
    .test-row:nth-child(even) {{ background: #fafafa; }}
    .test-num {{
      width: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Roboto Mono', monospace;
      font-size: 7.5pt;
      color: #888;
      border-right: 1px solid #e0e0e0;
      flex-shrink: 0;
    }}
    .test-body {{
      flex: 1;
      padding: 6px 10px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .test-name {{
      font-size: 8.5pt;
      font-weight: 700;
      color: #1a1a1a;
    }}
    .ref-val {{
      font-family: 'Roboto Mono', monospace;
      font-size: 7pt;
      color: #2864c8;
      background: #f0f5ff;
      padding: 1px 5px;
      border-radius: 2px;
      margin-left: 6px;
    }}
    .test-fill {{
      font-size: 8pt;
      color: #444;
    }}
    .test-obs {{
      font-size: 7.5pt;
      color: #888;
    }}
    .fill-line {{
      display: inline-block;
      width: 120px;
      border-bottom: 1px solid #aaa;
      vertical-align: bottom;
      margin-left: 4px;
    }}
    .fill-line.long {{ width: 200px; }}
    .test-result {{
      width: 110px;
      padding: 6px 10px;
      border-left: 1px solid #e0e0e0;
      font-size: 7.5pt;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 5px;
      flex-shrink: 0;
      color: #333;
    }}
    .empty-msg {{
      padding: 12px;
      color: #aaa;
      font-style: italic;
      text-align: center;
      font-size: 8.5pt;
      border: 1px solid #ccc;
      border-top: none;
    }}

    /* ── Section 5: Firmas ── */
    .signatures {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      padding: 16px 10px 8px;
      border: 1px solid #ccc;
      border-top: none;
    }}
    .sig-block {{ text-align: center; }}
    .sig-space {{
      height: 50px;
      border-bottom: 1.5px solid #1a1a1a;
      margin-bottom: 6px;
    }}
    .sig-name {{
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 7.5pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #1a1a1a;
    }}
    .sig-role {{
      font-size: 7pt;
      color: #666;
      margin-top: 2px;
    }}
    .sig-cip {{
      font-family: 'Roboto Mono', monospace;
      font-size: 7pt;
      color: #aaa;
      margin-top: 3px;
    }}

    /* ── Footer ── */
    .doc-footer {{
      margin-top: 10px;
      border-top: 1px solid #e0e0e0;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
      font-family: 'Roboto Mono', monospace;
      font-size: 6.5pt;
      color: #bbb;
    }}

    /* ── PRINT STYLES ── */
    @media print {{
      body {{ background: white; font-size: 9pt; }}
      .page {{ max-width: none; padding: 8mm 10mm; margin: 0; box-shadow: none; }}
      .section {{ page-break-inside: avoid; }}
      .no-print {{ display: none !important; }}
      a {{ color: inherit; text-decoration: none; }}

      /* Ensure checkboxes print visibly */
      .check-box {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
      .machine-banner, .section-header {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
    }}

    @page {{
      size: A4 portrait;
      margin: 10mm 12mm;
    }}

    /* ── Print button (only on screen) ── */
    .print-bar {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background: #1e3a8a;
      color: white;
      padding: 10px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 1000;
      font-family: 'Roboto Mono', monospace;
      font-size: 8.5pt;
    }}
    .print-btn {{
      background: #1e3a8a;
      color: white;
      border: none;
      padding: 7px 20px;
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 9pt;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      cursor: pointer;
      border-radius: 3px;
      transition: background 0.15s;
    }}
    .print-btn:hover {{ background: #2554c7; }}
    @media print {{ .print-bar {{ display: none; }} }}
    body {{ padding-top: 40px; }}
    @media print {{ body {{ padding-top: 0; }} }}
  </style>
</head>
<body>

<!-- Print bar (only visible on screen) -->
<div class="print-bar no-print">
  <span>⚙ CHECKLIST DE CONTROL DE CALIDAD · {tipo} &nbsp;·&nbsp; Generado: {generated_at}</span>
  <button class="print-btn" onclick="window.print()">🖨 Imprimir / Guardar PDF</button>
</div>

<div class="page">

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- HEADER                                              -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="doc-header">
    <div class="header-logo">
      <img src="data:image/png;base64,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" alt="J&J Trading Corporation S.A.C." style="height:52px;width:auto;display:block;">
    </div>
    <div class="header-title">
      <div class="doc-title">Checklist de Inspección · Control de Calidad</div>
      <div class="doc-subtitle">Supervisión Pre-entrega de Integración Chasis–Carrocería</div>
    </div>
    <div class="header-meta">
      <div>
        <div class="meta-label">Código</div>
        <div class="meta-value">CHK-IA-001</div>
      </div>
      <div>
        <div class="meta-label">Fecha</div>
        <div class="meta-value">{generated_at}</div>
      </div>
    </div>
  </div>

  <div class="machine-banner">
    <span>Tipo de Equipo:</span>
    <span class="tag">▸ {tipo}</span>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- SECCIÓN 1: DATOS DEL EQUIPO                        -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">1</span>
      Datos del Equipo
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <div class="data-label">Entidad Destino (Cliente Final)</div>
        <div class="data-value">{eq.get('entidad_destino') or '<span class="data-line"></span>'}</div>
      </div>
      <div class="data-cell">
        <div class="data-label">Tipo de Vehículo / Equipo</div>
        <div class="data-value">{eq.get('tipo_vehiculo') or '<span class="data-line"></span>'}</div>
      </div>
      <div class="data-cell">
        <div class="data-label">Marca y Modelo del Chasis</div>
        <div class="data-value">{eq.get('marca_chasis') or '<span class="data-line"></span>'}</div>
      </div>
      <div class="data-cell">
        <div class="data-label">Empresa Carrocera</div>
        <div class="data-value">{eq.get('nombre_carrocero') or '<span class="data-line"></span>'}</div>
      </div>
      <div class="data-cell">
        <div class="data-label">Número de Serie / Placa</div>
        <div class="data-value"><span class="data-line" style="width:180px"></span></div>
      </div>
      <div class="data-cell">
        <div class="data-label">Fecha de Inspección</div>
        <div class="data-value"><span class="data-line" style="width:180px"></span></div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- SECCIÓN 2: VERIFICACIÓN FÍSICA Y DIMENSIONAL       -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">2</span>
      Verificación Física y Dimensional
      <span style="margin-left:auto; font-size:7pt; font-weight:400; letter-spacing:0.02em; opacity:0.7;">{len(verificacion)} ítems · Marcar: Sí / No / Observaciones</span>
    </div>
    <table class="check-table">
      <thead>
        <tr>
          <th class="num">#</th>
          <th style="width:28%">Ítem a Verificar</th>
          <th style="width:38%">Especificación Técnica Requerida</th>
          <th style="width:18%">Resultado / Obs.</th>
        </tr>
      </thead>
      <tbody>
        {sec2_rows}
      </tbody>
    </table>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- SECCIÓN 3: ACCESORIOS ADICIONALES OFERTADOS        -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">3</span>
      Accesorios Adicionales Ofertados
      <span style="margin-left:auto; font-size:7pt; font-weight:400; letter-spacing:0.02em; opacity:0.7;">{len(accesorios)} accesorios · Verificar presencia física</span>
    </div>
    <table class="check-table">
      <thead>
        <tr>
          <th class="num">#</th>
          <th style="width:28%">Accesorio / Ítem</th>
          <th style="width:46%">Descripción / Especificación</th>
          <th style="width:12%">Estado</th>
        </tr>
      </thead>
      <tbody>
        {sec3_rows}
      </tbody>
    </table>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- SECCIÓN 4: PRUEBAS DE FUNCIONAMIENTO               -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">4</span>
      Pruebas de Funcionamiento
      <span style="margin-left:auto; font-size:7pt; font-weight:400; letter-spacing:0.02em; opacity:0.7;">{len(pruebas)} pruebas · Registrar valores medidos</span>
    </div>
    <div class="tests-container">
      {sec4_html}
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- SECCIÓN 5: FIRMAS Y APROBACIÓN                     -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="section">
    <div class="section-header">
      <span class="section-num">5</span>
      Firmas y Aprobación Final
    </div>
    <div class="signatures">
      <div class="sig-block">
        <div class="sig-space"></div>
        <div class="sig-name">Ingeniero Inspector</div>
        <div class="sig-role">Empresa Contratista · Responsable de Control de Calidad</div>
        <div class="sig-cip">Nombre: _________________ · DNI: ________</div>
      </div>
      <div class="sig-block">
        <div class="sig-space"></div>
        <div class="sig-name">Jefe de Taller · Carrocero</div>
        <div class="sig-role">Empresa Carrocera · Responsable de Producción</div>
        <div class="sig-cip">Nombre: _________________ · DNI: ________</div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- FOOTER                                              -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="doc-footer">
    <span>Generado con IA el {generated_at} · Basado en Oferta Técnica</span>
    <span>CHK-IA-001</span>
    <span>VERIFICAR ESPECIFICACIONES CON DOCUMENTO ORIGINAL</span>
  </div>

</div>

<script>
  // Checkboxes interactivos en pantalla (no afectan la impresión)
  document.querySelectorAll('.check-box').forEach(box => {{
    box.style.cursor = 'pointer';
    box.addEventListener('click', function() {{
      if (this.style.background === 'rgb(26, 26, 26)') {{
        this.style.background = '';
        this.style.borderColor = '#555';
      }} else {{
        this.style.background = '#1a1a1a';
        this.style.borderColor = '#1a1a1a';
      }}
    }});
  }});
</script>
</body>
</html>"""

    return html
