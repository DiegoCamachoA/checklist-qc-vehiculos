"""
export_utils.py
Generación del checklist en HTML optimizado para impresión.
Diseño tipo "portapapeles de taller": limpio, robusto, funcional.
"""

from datetime import datetime


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
        generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

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
  <title>Checklist QC · {tipo}</title>
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
      color: #1a1a1a;
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
      background: #1e3a8a;
      color: #1a1a1a;
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
      color: #1a1a1a;
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
  <span>⚙ CHECKLIST QC · {tipo} &nbsp;·&nbsp; Generado: {generated_at}</span>
  <button class="print-btn" onclick="window.print()">🖨 Imprimir / Guardar PDF</button>
</div>

<div class="page">

  <!-- ═══════════════════════════════════════════════════ -->
  <!-- HEADER                                              -->
  <!-- ═══════════════════════════════════════════════════ -->
  <div class="doc-header">
    <div class="header-logo">
      <div class="logo-icon">⚙</div>
    </div>
    <div class="header-title">
      <div class="doc-title">Checklist de Inspección · Control de Calidad</div>
      <div class="doc-subtitle">Integración Chasis–Carrocería · Vehículos Especiales · Contratos Estado Peruano</div>
    </div>
    <div class="header-meta">
      <div>
        <div class="meta-label">Código</div>
        <div class="meta-value">CHK-QC-001</div>
      </div>
      <div>
        <div class="meta-label">Fecha</div>
        <div class="meta-value">{generated_at[:10]}</div>
      </div>
      <div>
        <div class="meta-label">Versión</div>
        <div class="meta-value">IA-GEN v1.0</div>
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
        <div class="sig-role">Empresa Contratista · Responsable QC</div>
        <div class="sig-cip">Nombre: _________________ · CIP: ________</div>
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
    <span>Generado con IA el {generated_at} · Basado en TDR/Oferta Técnica</span>
    <span>CHK-QC-001 · Rev. 0 · Página 1 de 1</span>
    <span>VERIFICAR ESPECIFICACIONES CONTRA DOCUMENTO ORIGINAL</span>
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
