def get_html_template(visual_guide=None):
    """Return the main HTML template."""
    
    if visual_guide is None:
        visual_guide = {'exists': False, 'url': None, 'type': None}
    
    visual_guide_html = ''
    if visual_guide.get('exists'):
        if visual_guide.get('type') == 'image':
            visual_guide_html = f'<img class="guide-image" src="{visual_guide["url"]}" alt="Visual Guide" onclick="openLightbox(this.src)">'
        elif visual_guide.get('type') == 'pdf':
            visual_guide_html = f'<iframe class="guide-pdf" src="{visual_guide["url"]}"></iframe>'
    else:
        visual_guide_html = '<div class="guide-placeholder"><span>🔬</span><p>Add visual_guide.png to your project folder</p></div>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parasite Classifier</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔬</text></svg>">
    <style>
        /* ─── Design Tokens ──────────────────────────────────────────────── */
        :root {{
            /* Surface */
            --bg-app:       #eef0f3;
            --bg-surface:   #f8f9fa;
            --bg-raised:    #ffffff;
            --bg-inset:     #e8eaed;
            --bg-hover:     #e2e5e9;

            /* Text */
            --text-hi:      #1a1d21;
            --text-mid:     #5c6370;
            --text-lo:      #9ba3ae;

            /* Accent — cool slate-blue, restrained */
            --accent:       #5b7fa6;
            --accent-soft:  #dce6f0;
            --accent-hover: #4a6d92;

            /* Stage badge colors — muted, distinguishable */
            --stage-ring:   #c9d8e8;
            --stage-other:  #dde3ea;

            /* Status */
            --ok-bg:        #d4eadb;
            --ok-text:      #2d5c3a;
            --ok-hover:     #c3decc;
            --warn-bg:      #f0e6c8;
            --warn-text:    #5c4a1a;
            --warn-hover:   #e8dbb8;
            --bad-bg:       #ead8d8;
            --bad-text:     #5c2e2e;
            --bad-hover:    #dfc8c8;

            /* Structure */
            --border:       #d4d8de;
            --border-lo:    #e8eaed;
            --radius-s:     6px;
            --radius-m:     10px;
            --radius-l:     14px;
            --shadow-s:     0 1px 3px rgba(0,0,0,.06);
            --shadow-m:     0 3px 10px rgba(0,0,0,.08);

            /* Type */
            --font-ui:      -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif;
            --font-mono:    'SF Mono', 'Fira Code', monospace;
            --ease:         cubic-bezier(.4,0,.2,1);
        }}

        /* ─── Reset & Base ───────────────────────────────────────────────── */
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: var(--font-ui);
            font-size: 13px;
            line-height: 1.5;
            background: var(--bg-app);
            color: var(--text-hi);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
        }}

        /* ─── Header ─────────────────────────────────────────────────────── */
        .header {{
            background: var(--bg-raised);
            border-bottom: 1px solid var(--border-lo);
            height: 52px;
            padding: 0 16px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-shrink: 0;
            z-index: 100;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 7px;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: -0.3px;
            color: var(--text-hi);
            white-space: nowrap;
        }}

        .logo-icon {{
            font-size: 18px;
            line-height: 1;
        }}

        .header-divider {{
            width: 1px;
            height: 20px;
            background: var(--border);
            flex-shrink: 0;
        }}

        /* Progress pill */
        .progress-pill {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 12px;
            background: var(--bg-inset);
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }}

        .progress-pill.hidden {{ display: none; }}

        .progress-nums {{
            display: flex;
            gap: 4px;
            align-items: baseline;
        }}

        .progress-nums strong {{
            font-size: 13px;
            font-weight: 700;
            color: var(--text-hi);
        }}

        .progress-nums span {{
            color: var(--text-lo);
            font-size: 11px;
        }}

        .progress-track {{
            width: 72px;
            height: 3px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: var(--accent);
            transition: width .4s var(--ease);
        }}

        /* Spacer */
        .header-spacer {{ flex: 1; }}

        /* Header action buttons */
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .header-actions.hidden {{ display: none; }}

        input[type="file"] {{ display: none; }}

        /* ─── Buttons ────────────────────────────────────────────────────── */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            font-family: var(--font-ui);
            font-size: 12px;
            font-weight: 500;
            border: 1px solid transparent;
            border-radius: var(--radius-s);
            cursor: pointer;
            transition: background .15s var(--ease), opacity .15s;
            white-space: nowrap;
            letter-spacing: -0.1px;
        }}

        .btn:disabled {{ opacity: .35; cursor: not-allowed; pointer-events: none; }}

        .btn-ghost {{
            background: transparent;
            border-color: var(--border);
            color: var(--text-mid);
        }}
        .btn-ghost:hover:not(:disabled) {{
            background: var(--bg-inset);
            color: var(--text-hi);
        }}

        .btn-primary {{
            background: var(--accent-soft);
            color: var(--accent);
            border-color: transparent;
        }}
        .btn-primary:hover:not(:disabled) {{
            background: #cddaeb;
        }}

        .btn-success {{
            background: var(--ok-bg);
            color: var(--ok-text);
        }}
        .btn-success:hover:not(:disabled) {{ background: var(--ok-hover); }}

        .btn-danger-ghost {{
            background: transparent;
            border-color: var(--border);
            color: var(--text-lo);
        }}
        .btn-danger-ghost:hover:not(:disabled) {{
            background: var(--bad-bg);
            color: var(--bad-text);
            border-color: transparent;
        }}

        .btn-icon {{ padding: 6px 8px; }}

        /* ─── Layout ─────────────────────────────────────────────────────── */
        .layout {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}

        /* ─── Sidebar ────────────────────────────────────────────────────── */
        .sidebar {{
            width: 300px;
            min-width: 200px;
            max-width: 440px;
            background: var(--bg-raised);
            border-right: 1px solid var(--border-lo);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            transition: width .22s var(--ease);
            flex-shrink: 0;
        }}

        .sidebar.collapsed {{ width: 0 !important; min-width: 0; }}

        .sidebar-resize {{
            position: absolute;
            right: 0;
            top: 0;
            width: 4px;
            height: 100%;
            cursor: ew-resize;
            z-index: 10;
        }}
        .sidebar-resize:hover {{ background: var(--accent-soft); }}

        .sidebar-toggle {{
            position: absolute;
            left: 300px;
            top: 50%;
            transform: translateY(-50%);
            width: 14px;
            height: 36px;
            background: var(--bg-raised);
            border: 1px solid var(--border-lo);
            border-left: none;
            border-radius: 0 5px 5px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 50;
            color: var(--text-lo);
            font-size: 9px;
            transition: color .15s;
        }}
        .sidebar.collapsed ~ .sidebar-toggle {{ left: 0; }}
        .sidebar-toggle:hover {{ color: var(--text-mid); background: var(--bg-inset); }}

        .sidebar-body {{
            flex: 1;
            overflow-y: auto;
            padding: 16px 14px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Sidebar section */
        .sb-section {{ display: flex; flex-direction: column; gap: 8px; }}

        .sb-label {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .8px;
            color: var(--text-lo);
        }}

        /* Guide */
        .guide-image {{
            width: 100%;
            border-radius: var(--radius-m);
            cursor: zoom-in;
            border: 1px solid var(--border-lo);
            display: block;
        }}

        .guide-pdf {{
            width: 100%;
            height: 240px;
            border: 1px solid var(--border-lo);
            border-radius: var(--radius-m);
        }}

        .guide-placeholder {{
            padding: 20px;
            text-align: center;
            background: var(--bg-inset);
            border-radius: var(--radius-m);
            border: 1px dashed var(--border);
            color: var(--text-lo);
        }}
        .guide-placeholder span {{ font-size: 22px; display: block; margin-bottom: 6px; }}
        .guide-placeholder p {{ font-size: 11px; line-height: 1.4; }}

        /* ─── Cue Table ──────────────────────────────────────────────────── */
        .cue-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            border: 1px solid var(--border-lo);
            border-radius: var(--radius-s);
            overflow: hidden;
        }}

        .cue-table th {{
            background: var(--bg-inset);
            color: var(--text-mid);
            font-weight: 600;
            padding: 7px 8px;
            text-align: center;
            border-bottom: 1px solid var(--border);
            letter-spacing: .3px;
        }}

        .cue-table th:first-child {{ text-align: left; padding-left: 10px; }}

        .cue-table td {{
            padding: 6px 8px;
            border-bottom: 1px solid var(--border-lo);
            color: var(--text-hi);
            vertical-align: middle;
        }}

        .cue-table td:first-child {{ padding-left: 10px; color: var(--text-mid); }}

        .cue-table td:not(:first-child) {{
            text-align: center;
            font-weight: 600;
            font-size: 12px;
        }}

        .cue-table tbody tr:last-child td {{ border-bottom: none; }}

        .cue-table tbody tr:hover td {{ background: var(--bg-surface); }}

        /* Presence indicators */
        .cue-pos {{ color: var(--ok-text); }}
        .cue-neg {{ color: var(--text-lo); }}
        .cue-mid {{ color: var(--warn-text); }}

        /* ─── Decision Flow ──────────────────────────────────────────────── */
        .flow-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .flow-item {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 8px 10px;
            border-radius: var(--radius-s);
            border: 1px solid var(--border-lo);
            background: var(--bg-surface);
        }}

        .flow-item:hover {{ background: var(--bg-inset); }}

        .flow-cue {{
            font-size: 11px;
            color: var(--text-hi);
            font-weight: 500;
            line-height: 1.4;
        }}

        .flow-result {{
            font-size: 10px;
            font-weight: 700;
            color: var(--accent);
            letter-spacing: .3px;
        }}

        /* ─── Workspace ──────────────────────────────────────────────────── */
        .workspace {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            min-width: 0;
        }}

        /* Image stage */
        .image-stage {{
            flex: 1;
            margin: 12px 12px 8px;
            background: var(--bg-raised);
            border: 1px solid var(--border-lo);
            border-radius: var(--radius-l);
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .image-scroll {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: auto;
            padding: 20px;
        }}

        #current-image {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: var(--radius-s);
            box-shadow: var(--shadow-m);
            transition: transform .12s var(--ease);
            display: block;
        }}

        /* Placeholder */
        .placeholder {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            color: var(--text-lo);
            padding: 40px;
            text-align: center;
        }}

        .placeholder-icon {{ font-size: 36px; opacity: .7; }}
        .placeholder-title {{ font-size: 14px; font-weight: 500; color: var(--text-mid); }}
        .placeholder-sub {{ font-size: 12px; color: var(--text-lo); }}

        /* Filename bar — bottom of stage */
        .filename-bar {{
            position: absolute;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(26,29,33,.75);
            color: rgba(255,255,255,.9);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            max-width: 70%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: none;
        }}

        /* Zoom controls — top right of stage */
        .zoom-controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            display: none;
            align-items: center;
            gap: 1px;
            background: var(--bg-raised);
            border: 1px solid var(--border-lo);
            border-radius: var(--radius-s);
            padding: 3px;
            box-shadow: var(--shadow-s);
        }}

        .zoom-btn {{
            width: 26px;
            height: 26px;
            border: none;
            background: transparent;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-mid);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background .12s;
        }}
        .zoom-btn:hover {{ background: var(--bg-inset); color: var(--text-hi); }}

        .zoom-pct {{
            min-width: 40px;
            text-align: center;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-mid);
            font-variant-numeric: tabular-nums;
            font-family: var(--font-mono);
        }}

        /* ─── Classification Bar ─────────────────────────────────────────── */
        .classbar {{
            flex-shrink: 0;
            background: var(--bg-raised);
            border-top: 1px solid var(--border-lo);
            padding: 10px 12px 12px;
            display: none;
        }}

        .classbar.visible {{ display: block; }}

        /* Selection strip */
        .selection-strip {{
            display: none;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            background: var(--bg-inset);
            border-radius: var(--radius-s);
            margin-bottom: 8px;
            font-size: 11px;
            color: var(--text-mid);
        }}

        .selection-strip.visible {{ display: flex; }}

        .sel-tag {{
            display: inline-flex;
            align-items: center;
            padding: 2px 9px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        }}

        .sel-tag.primary {{ background: var(--stage-ring); color: var(--accent-hover); }}
        .sel-tag.secondary {{ background: var(--warn-bg); color: var(--warn-text); }}

        .sel-clear {{
            margin-left: auto;
            font-size: 11px;
            color: var(--text-lo);
            cursor: pointer;
            padding: 1px 6px;
            border-radius: 4px;
            transition: background .12s;
        }}
        .sel-clear:hover {{ background: var(--bad-bg); color: var(--bad-text); }}

        /* Button groups */
        .btn-groups {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .btn-group-label {{
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .7px;
            color: var(--text-lo);
            margin-bottom: 2px;
        }}

        .btn-row {{
            display: flex;
            gap: 5px;
        }}

        .class-btn {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
            padding: 9px 6px 8px;
            background: var(--bg-surface);
            border: 1.5px solid var(--border-lo);
            border-radius: var(--radius-m);
            cursor: pointer;
            transition: border-color .12s var(--ease), background .12s var(--ease);
            font-family: var(--font-ui);
            position: relative;
        }}

        .class-btn:hover:not(:disabled) {{
            border-color: var(--accent);
            background: var(--accent-soft);
        }}

        .class-btn:disabled {{
            opacity: .22;
            cursor: not-allowed;
        }}

        .class-btn.selected {{
            background: var(--accent-soft);
            border-color: var(--accent);
        }}

        .class-btn.adj {{
            border-color: var(--warn-bg);
            background: #fdf8ef;
        }}
        .class-btn.adj:hover:not(:disabled) {{
            background: var(--warn-bg);
            border-color: #c8aa70;
        }}

        .class-btn-name {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-hi);
            text-align: center;
            line-height: 1.2;
            white-space: nowrap;
        }}

        .class-btn:disabled .class-btn-name {{ color: var(--text-lo); }}
        .class-btn.selected .class-btn-name {{ color: var(--accent-hover); }}

        .class-btn-key {{
            font-size: 9px;
            font-weight: 600;
            font-family: var(--font-mono);
            color: var(--text-lo);
            background: var(--bg-inset);
            padding: 1px 5px;
            border-radius: 3px;
            letter-spacing: .5px;
        }}

        .class-btn.selected .class-btn-key {{
            background: rgba(91,127,166,.15);
            color: var(--accent);
        }}

        .class-btn-count {{
            font-size: 10px;
            font-weight: 700;
            font-family: var(--font-mono);
            color: var(--text-lo);
            min-height: 14px;
        }}

        .class-btn-count.nonzero {{ color: var(--ok-text); }}

        /* ─── Status Panel ───────────────────────────────────────────────── */
        /* Moved: now lives right of the btn-groups, inline in the classbar */
        .classbar-inner {{
            display: flex;
            gap: 10px;
            align-items: stretch;
        }}

        .btn-groups {{ flex: 1; min-width: 0; }}

        .status-panel {{
            display: none;
            flex-direction: column;
            gap: 5px;
            justify-content: center;
            flex-shrink: 0;
            width: 100px;
        }}

        .status-panel.visible {{ display: flex; }}

        .status-btn {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2px;
            padding: 8px 6px;
            border: 1.5px solid transparent;
            border-radius: var(--radius-m);
            font-family: var(--font-ui);
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: filter .12s;
            letter-spacing: -0.1px;
        }}

        .status-btn:disabled {{ opacity: .3; cursor: not-allowed; pointer-events: none; }}
        .status-btn:not(:disabled):hover {{ filter: brightness(.93); }}

        .status-btn.ok  {{ background: var(--ok-bg);   color: var(--ok-text); }}
        .status-btn.lim {{ background: var(--warn-bg);  color: var(--warn-text); }}
        .status-btn.bad {{ background: var(--bad-bg);   color: var(--bad-text); }}

        .status-key {{
            font-size: 9px;
            font-weight: 600;
            font-family: var(--font-mono);
            opacity: .65;
            background: rgba(0,0,0,.06);
            padding: 1px 5px;
            border-radius: 3px;
        }}

        /* ─── Toast ──────────────────────────────────────────────────────── */
        .toast {{
            position: fixed;
            bottom: 90px;
            left: 50%;
            transform: translateX(-50%) translateY(12px);
            background: var(--text-hi);
            color: #fff;
            padding: 8px 18px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            opacity: 0;
            pointer-events: none;
            transition: opacity .25s var(--ease), transform .25s var(--ease);
            z-index: 2000;
            white-space: nowrap;
        }}

        .toast.show {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
        .toast.err  {{ background: var(--bad-text); }}

        /* ─── Lightbox ───────────────────────────────────────────────────── */
        .lightbox {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,.82);
            z-index: 3000;
            align-items: center;
            justify-content: center;
            cursor: zoom-out;
        }}
        .lightbox.open {{ display: flex; }}
        .lightbox img {{
            max-width: 92%;
            max-height: 92%;
            border-radius: var(--radius-m);
            box-shadow: 0 20px 60px rgba(0,0,0,.5);
        }}

        /* ─── Upload section ─────────────────────────────────────────────── */
        #upload-section {{ margin-left: auto; }}
    </style>
</head>
<body>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
    <img id="lightbox-img" src="" alt="Preview">
</div>

<!-- ── Header ─────────────────────────────────────────────────────────────── -->
<header class="header">
    <div class="logo">
        <span class="logo-icon">🔬</span>
        Parasite Classifier
    </div>

    <div class="header-divider"></div>

    <div class="progress-pill hidden" id="progress-display">
        <div class="progress-nums">
            <strong id="sorted-count">0</strong>
            <span>done</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" id="progress-fill"></div>
        </div>
        <div class="progress-nums">
            <strong id="remaining-count">0</strong>
            <span>left</span>
        </div>
    </div>

    <div class="header-spacer"></div>

    <div class="header-actions hidden" id="header-actions">
        <button class="btn btn-ghost" id="undo-btn" disabled onclick="executeUndo()">↩ Undo</button>
        <button class="btn btn-ghost" id="save-btn" disabled onclick="saveProgress()">💾 Save</button>
        <input type="file" id="progress-input" accept=".csv">
        <button class="btn btn-ghost" id="load-btn" disabled onclick="document.getElementById('progress-input').click()">📤 Load</button>
        <button class="btn btn-success" id="download-btn" disabled onclick="downloadSorted()">📥 Download</button>
        <button class="btn btn-danger-ghost btn-icon" onclick="resetSession()" title="Reset session">⟳</button>
    </div>

    <div id="upload-section">
        <input type="file" id="dataset-input" accept=".zip">
        <button class="btn btn-primary" onclick="document.getElementById('dataset-input').click()">📦 Upload Dataset</button>
    </div>
</header>

<!-- ── Layout ─────────────────────────────────────────────────────────────── -->
<div class="layout">

    <!-- Sidebar -->
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-resize" id="sidebar-resize"></div>
        <div class="sidebar-body">

            <div class="sb-section">
                <div class="sb-label">Visual Guide</div>
                {visual_guide_html}
            </div>

            <div class="sb-section">
                <div class="sb-label">Stage Cues</div>
                <table class="cue-table">
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>ER</th>
                            <th>MR</th>
                            <th>LR</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Cytoplasm : nucleus</td>    <td class="cue-neg">≤0.5</td> <td class="cue-mid">0.5–1</td> <td class="cue-pos">≥1</td></tr>
                        <tr><td>Appliqué / accolé</td>      <td class="cue-pos">+++</td>  <td class="cue-mid">+</td>     <td class="cue-neg">–</td></tr>
                        <tr><td>Double-dot chromatin</td>   <td class="cue-pos">++</td>   <td class="cue-mid">+</td>     <td class="cue-neg">–</td></tr>
                        <tr><td>Crescent / comma</td>       <td class="cue-pos">+++</td>  <td class="cue-neg">–</td>     <td class="cue-neg">–</td></tr>
                        <tr><td>Circular ring</td>          <td class="cue-mid">±</td>    <td class="cue-pos">+++</td>   <td class="cue-mid">+</td></tr>
                        <tr><td>Amoeboid cytoplasm</td>     <td class="cue-neg">–</td>    <td class="cue-mid">±</td>     <td class="cue-mid">+</td></tr>
                        <tr><td>Maurer's clefts</td>        <td class="cue-neg">–</td>    <td class="cue-mid">±</td>     <td class="cue-pos">++</td></tr>
                        <tr><td>Hemozoin pigment</td>       <td class="cue-neg">–</td>    <td class="cue-mid">±</td>     <td class="cue-mid">+</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="sb-section">
                <div class="sb-label">Decision Flow</div>
                <ol class="flow-list">
                    <li class="flow-item">
                        <span class="flow-cue">Cytoplasm band vs nucleus diameter?</span>
                        <span class="flow-result">→ ER / MR / LR</span>
                    </li>
                    <li class="flow-item">
                        <span class="flow-cue">Pigment granules or Maurer's clefts present?</span>
                        <span class="flow-result">→ MR or LR</span>
                    </li>
                    <li class="flow-item">
                        <span class="flow-cue">Minimal cytoplasm, comma shape, appliqué, or double-dot?</span>
                        <span class="flow-result">→ ER</span>
                    </li>
                    <li class="flow-item">
                        <span class="flow-cue">Clean, textbook circular ring?</span>
                        <span class="flow-result">→ MR</span>
                    </li>
                    <li class="flow-item">
                        <span class="flow-cue">Dense stippling, hemozoin, or amoeboid shape?</span>
                        <span class="flow-result">→ LR</span>
                    </li>
                </ol>
            </div>

        </div>
    </aside>

    <!-- Sidebar toggle -->
    <button class="sidebar-toggle" id="sidebar-toggle" onclick="toggleSidebar()">
        <span id="toggle-icon">‹</span>
    </button>

    <!-- Workspace -->
    <main class="workspace">

        <!-- Image stage -->
        <div class="image-stage" id="image-stage">

            <div class="placeholder" id="placeholder">
                <div class="placeholder-icon">📦</div>
                <div class="placeholder-title">Upload a ZIP to begin</div>
                <div class="placeholder-sub">PNG, JPG, GIF, BMP, TIFF, WebP</div>
            </div>

            <div class="image-scroll" id="image-scroll" style="display:none">
                <img id="current-image" src="" alt="Current parasite image">
            </div>

            <div class="zoom-controls" id="zoom-controls">
                <button class="zoom-btn" onclick="zoomOut()" title="Zoom out">−</button>
                <span class="zoom-pct" id="zoom-label">100%</span>
                <button class="zoom-btn" onclick="zoomIn()" title="Zoom in">+</button>
                <button class="zoom-btn" onclick="resetZoom()" title="Reset zoom" style="font-size:12px;">↺</button>
            </div>

            <div class="filename-bar" id="filename-bar"></div>

        </div>

        <!-- Classification bar -->
        <div class="classbar" id="classbar">

            <!-- Selection strip -->
            <div class="selection-strip" id="selection-strip">
                <span style="color:var(--text-lo)">Selected:</span>
                <span class="sel-tag primary" id="sel-first"></span>
                <span class="sel-tag secondary" id="sel-second" style="display:none"></span>
                <span class="sel-clear" onclick="clearSelection()">Clear ✕</span>
            </div>

            <div class="classbar-inner">
                <div class="btn-groups">
                    <!-- Row 1: Asexual ring stages -->
                    <div class="btn-group-label">Asexual Ring Stages</div>
                    <div class="btn-row">
                        <button class="class-btn" data-key="1" onclick="selectLabel('1')">
                            <span class="class-btn-name">Early Ring</span>
                            <span class="class-btn-key">1</span>
                            <span class="class-btn-count" id="count-1">0</span>
                        </button>
                        <button class="class-btn" data-key="2" onclick="selectLabel('2')">
                            <span class="class-btn-name">Mid Ring</span>
                            <span class="class-btn-key">2</span>
                            <span class="class-btn-count" id="count-2">0</span>
                        </button>
                        <button class="class-btn" data-key="3" onclick="selectLabel('3')">
                            <span class="class-btn-name">Late Ring</span>
                            <span class="class-btn-key">3</span>
                            <span class="class-btn-count" id="count-3">0</span>
                        </button>
                        <button class="class-btn" data-key="4" onclick="selectLabel('4')">
                            <span class="class-btn-name">Trophozoite</span>
                            <span class="class-btn-key">4</span>
                            <span class="class-btn-count" id="count-4">0</span>
                        </button>
                        <button class="class-btn" data-key="5" onclick="selectLabel('5')">
                            <span class="class-btn-name">Schizont</span>
                            <span class="class-btn-key">5</span>
                            <span class="class-btn-count" id="count-5">0</span>
                        </button>
                    </div>

                    <!-- Row 2: Other classes -->
                    <div class="btn-group-label" style="margin-top:4px">Other Classes</div>
                    <div class="btn-row">
                        <button class="class-btn" data-key="6" onclick="selectLabel('6')">
                            <span class="class-btn-name">Gametocyte</span>
                            <span class="class-btn-key">6</span>
                            <span class="class-btn-count" id="count-6">0</span>
                        </button>
                        <button class="class-btn" data-key="7" onclick="selectLabel('7')">
                            <span class="class-btn-name">Merozoite</span>
                            <span class="class-btn-key">7</span>
                            <span class="class-btn-count" id="count-7">0</span>
                        </button>
                        <button class="class-btn" data-key="8" onclick="selectLabel('8')">
                            <span class="class-btn-name">Artefact</span>
                            <span class="class-btn-key">8</span>
                            <span class="class-btn-count" id="count-8">0</span>
                        </button>
                        <button class="class-btn" data-key="9" onclick="selectLabel('9')">
                            <span class="class-btn-name">Platelet</span>
                            <span class="class-btn-key">9</span>
                            <span class="class-btn-count" id="count-9">0</span>
                        </button>
                        <button class="class-btn" data-key="0" onclick="selectLabel('0')">
                            <span class="class-btn-name">Uninfected</span>
                            <span class="class-btn-key">0</span>
                            <span class="class-btn-count" id="count-0">0</span>
                        </button>
                        <button class="class-btn" data-key="-" onclick="selectLabel('-')">
                            <span class="class-btn-name">Can't Determine</span>
                            <span class="class-btn-key">−</span>
                            <span class="class-btn-count" id="count--">0</span>
                        </button>
                    </div>
                </div>

                <!-- Status panel — right column -->
                <div class="status-panel" id="status-panel">
                    <button class="status-btn ok"  id="status-usable"   onclick="finalizeWithStatus('Usable')"   disabled>
                        Usable
                        <span class="status-key">↵</span>
                    </button>
                    <button class="status-btn lim" id="status-limited"  onclick="finalizeWithStatus('Limited')"  disabled>
                        Limited
                        <span class="status-key">'</span>
                    </button>
                    <button class="status-btn bad" id="status-unusable" onclick="finalizeWithStatus('Unusable')" disabled>
                        Unusable
                        <span class="status-key">⇧</span>
                    </button>
                </div>
            </div>

        </div>
    </main>

</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// ── Config ──────────────────────────────────────────────────────────────────
const CLASS_MAP = {{
    '1': 'Early Ring',
    '2': 'Middle Ring',
    '3': 'Late Ring',
    '4': 'Trophozoite',
    '5': 'Schizont',
    '6': 'Gametocyte',
    '7': 'Merozoite',
    '8': 'Other Artefact',
    '9': 'Platelet',
    '0': 'Uninfected',
    '-': 'Cannot Determine'
}};

const FIRST_ROW  = ['1','2','3','4','5'];
const SECOND_ROW = ['6','7','8','9','0','-'];
const AUTO_ADVANCE = ['0','-'];

const ADJACENCY = {{
    '1': ['2'],
    '2': ['1','3'],
    '3': ['2','4'],
    '4': ['3','5'],
    '5': ['4']
}};

// ── State ───────────────────────────────────────────────────────────────────
let state = {{
    uploadComplete: false,
    currentImage: null,
    remainingCount: 0,
    historyCount: 0,
    sortedCounts: {{}},
    totalSorted: 0,
    currentSelection: {{ first_label: null, second_label: null }}
}};

let zoom = 1;
let sidebarWidth = 300;

// ── Toast ────────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg, isErr = false) {{
    const t = document.getElementById('toast');
    clearTimeout(toastTimer);
    t.textContent = msg;
    t.className = 'toast' + (isErr ? ' err' : '');
    requestAnimationFrame(() => t.classList.add('show'));
    toastTimer = setTimeout(() => t.className = 'toast', 2600);
}}

// ── Lightbox ─────────────────────────────────────────────────────────────────
function openLightbox(src) {{
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox').classList.add('open');
}}
function closeLightbox() {{
    document.getElementById('lightbox').classList.remove('open');
}}

// ── Zoom ─────────────────────────────────────────────────────────────────────
function setZoom(z) {{
    zoom = Math.max(.25, Math.min(4, z));
    const img = document.getElementById('current-image');
    if (img) img.style.transform = `scale(${{zoom}})`;
    document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';
}}
function zoomIn()    {{ setZoom(zoom + .25); }}
function zoomOut()   {{ setZoom(zoom - .25); }}
function resetZoom() {{ setZoom(1); }}

// ── Sidebar ──────────────────────────────────────────────────────────────────
function toggleSidebar() {{
    const sb   = document.getElementById('sidebar');
    const icon = document.getElementById('toggle-icon');
    const tog  = document.getElementById('sidebar-toggle');
    sb.classList.toggle('collapsed');
    if (sb.classList.contains('collapsed')) {{
        icon.textContent = '›';
        tog.style.left = '0';
    }} else {{
        icon.textContent = '‹';
        tog.style.left = sidebarWidth + 'px';
    }}
}}

(function initResize() {{
    const sb   = document.getElementById('sidebar');
    const rsz  = document.getElementById('sidebar-resize');
    const tog  = document.getElementById('sidebar-toggle');
    let dragging = false;
    rsz.addEventListener('mousedown', () => {{
        dragging = true;
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
    }});
    document.addEventListener('mousemove', e => {{
        if (!dragging) return;
        const w = Math.max(0, Math.min(440, e.clientX));
        sidebarWidth = w;
        if (w < 80) {{
            sb.classList.add('collapsed');
            tog.style.left = '0';
            document.getElementById('toggle-icon').textContent = '›';
        }} else {{
            sb.classList.remove('collapsed');
            sb.style.width = w + 'px';
            tog.style.left = w + 'px';
            document.getElementById('toggle-icon').textContent = '‹';
        }}
    }});
    document.addEventListener('mouseup', () => {{
        dragging = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }});
}})();

// ── UI Render ────────────────────────────────────────────────────────────────
function renderUI() {{
    const {{ uploadComplete, currentImage, totalSorted, remainingCount, historyCount, sortedCounts, currentSelection }} = state;
    const hasImage   = !!currentImage;
    const hasSel     = !!currentSelection.first_label;
    const hasSorted  = totalSorted > 0;

    // Header
    document.getElementById('header-actions').classList.toggle('hidden', !uploadComplete);
    document.getElementById('progress-display').classList.toggle('hidden', !uploadComplete);
    document.getElementById('upload-section').style.display = uploadComplete ? 'none' : '';

    // Progress
    document.getElementById('sorted-count').textContent    = totalSorted;
    document.getElementById('remaining-count').textContent = remainingCount;
    const total = remainingCount + totalSorted;
    document.getElementById('progress-fill').style.width =
        total > 0 ? Math.round((totalSorted / total) * 100) + '%' : '0%';

    // Header buttons
    document.getElementById('undo-btn').disabled     = historyCount === 0;
    document.getElementById('save-btn').disabled     = !hasSorted;
    document.getElementById('load-btn').disabled     = !uploadComplete;
    document.getElementById('download-btn').disabled = !hasSorted;

    // Image area
    const placeholder = document.getElementById('placeholder');
    const scroll      = document.getElementById('image-scroll');
    const zoomCtrl    = document.getElementById('zoom-controls');
    const fnBar       = document.getElementById('filename-bar');

    if (!uploadComplete) {{
        placeholder.style.display = '';
        scroll.style.display      = 'none';
        zoomCtrl.style.display    = 'none';
        fnBar.style.display       = 'none';
    }} else if (hasImage) {{
        placeholder.style.display = 'none';
        scroll.style.display      = 'flex';
        zoomCtrl.style.display    = 'flex';
        fnBar.style.display       = 'block';
        document.getElementById('current-image').src =
            `/serve_image/${{encodeURIComponent(currentImage)}}?t=${{Date.now()}}`;
        fnBar.textContent = currentImage;
    }} else {{
        placeholder.innerHTML = `
            <div class="placeholder-icon">🎉</div>
            <div class="placeholder-title">All done!</div>
            <div class="placeholder-sub">Click Download to get your results</div>`;
        placeholder.style.display = '';
        scroll.style.display      = 'none';
        zoomCtrl.style.display    = 'none';
        fnBar.style.display       = 'none';
    }}

    // Classbar visibility
    const classbar = document.getElementById('classbar');
    classbar.classList.toggle('visible', uploadComplete && hasImage);

    // Count badges
    for (const [k, name] of Object.entries(CLASS_MAP)) {{
        const badge = document.getElementById('count-' + k);
        if (!badge) continue;
        const n = (sortedCounts[name] || {{}}).total || 0;
        badge.textContent = n || '';
        badge.classList.toggle('nonzero', n > 0);
    }}

    // Selection strip
    const strip    = document.getElementById('selection-strip');
    const selFirst = document.getElementById('sel-first');
    const selSec   = document.getElementById('sel-second');
    if (hasSel) {{
        strip.classList.add('visible');
        selFirst.textContent = CLASS_MAP[currentSelection.first_label];
        if (currentSelection.second_label) {{
            selSec.textContent  = CLASS_MAP[currentSelection.second_label];
            selSec.style.display = 'inline-flex';
        }} else {{
            selSec.style.display = 'none';
        }}
    }} else {{
        strip.classList.remove('visible');
    }}

    // Class buttons
    const fl = currentSelection.first_label;
    const sl = currentSelection.second_label;
    document.querySelectorAll('.class-btn').forEach(btn => {{
        const k = btn.dataset.key;
        btn.classList.remove('selected','adj');
        btn.disabled = !hasImage;
        if (!hasImage) return;
        if (k === fl || k === sl) {{
            btn.classList.add('selected');
        }} else if (fl) {{
            if (FIRST_ROW.includes(fl)) {{
                const adj = ADJACENCY[fl] || [];
                if (!adj.includes(k)) btn.disabled = true;
                else btn.classList.add('adj');
            }} else {{
                btn.disabled = true;
            }}
        }}
    }});

    // Status buttons
    ['status-usable','status-limited','status-unusable'].forEach(id => {{
        document.getElementById(id).disabled = !hasSel;
    }});

    // Status panel visibility
    document.getElementById('status-panel').classList.toggle('visible', uploadComplete && hasImage);
}}

// ── API ──────────────────────────────────────────────────────────────────────
async function fetchState() {{
    try {{
        const r = await fetch('/state');
        const d = await r.json();
        state.uploadComplete     = d.upload_complete;
        state.currentImage       = d.current_image;
        state.remainingCount     = d.remaining_count;
        state.historyCount       = d.history_count;
        state.sortedCounts       = d.sorted_counts;
        state.totalSorted        = d.total_sorted;
        state.currentSelection   = d.current_selection || {{ first_label: null, second_label: null }};
        renderUI();
    }} catch (e) {{ console.error('fetchState error', e); }}
}}

async function selectLabel(key) {{
    if (!state.currentImage) return;
    try {{
        const r = await fetch('/select_label', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ key }})
        }});
        const d = await r.json();
        if (d.success) {{
            if (d.auto_advanced) {{
                showToast(d.message);
                Object.assign(state, {{
                    currentImage:     d.current_image,
                    remainingCount:   d.remaining_count,
                    historyCount:     d.history_count,
                    sortedCounts:     d.sorted_counts,
                    totalSorted:      d.total_sorted,
                    currentSelection: d.current_selection
                }});
                resetZoom();
            }} else {{
                state.currentSelection = d.selection;
            }}
            renderUI();
        }} else {{
            showToast(d.message, true);
        }}
    }} catch {{ showToast('Error selecting label', true); }}
}}

async function clearSelection() {{
    try {{
        const r = await fetch('/clear_selection', {{ method: 'POST' }});
        const d = await r.json();
        if (d.success) {{ state.currentSelection = d.selection; renderUI(); }}
    }} catch {{ showToast('Error clearing', true); }}
}}

async function finalizeWithStatus(status) {{
    if (!state.currentSelection.first_label) return;
    try {{
        const r = await fetch('/finalize', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ status }})
        }});
        const d = await r.json();
        if (d.success) {{
            showToast(d.message);
            Object.assign(state, {{
                currentImage:     d.current_image,
                remainingCount:   d.remaining_count,
                historyCount:     d.history_count,
                sortedCounts:     d.sorted_counts,
                totalSorted:      d.total_sorted,
                currentSelection: d.current_selection
            }});
            resetZoom();
            renderUI();
        }} else {{
            showToast(d.message, true);
        }}
    }} catch {{ showToast('Error finalizing', true); }}
}}

async function executeUndo() {{
    try {{
        const r = await fetch('/undo', {{ method: 'POST' }});
        const d = await r.json();
        if (d.success) {{
            showToast('Undone');
            Object.assign(state, {{
                currentImage:     d.current_image,
                remainingCount:   d.remaining_count,
                historyCount:     d.history_count,
                sortedCounts:     d.sorted_counts,
                totalSorted:      d.total_sorted,
                currentSelection: d.current_selection
            }});
            renderUI();
        }} else {{
            showToast(d.message, true);
        }}
    }} catch {{ showToast('Error undoing', true); }}
}}

function downloadSorted() {{ if (state.totalSorted > 0) window.location.href = '/download'; }}
function saveProgress()   {{ if (state.totalSorted > 0) window.location.href = '/save_progress'; }}

async function resetSession() {{
    if (!confirm('Reset all data? This cannot be undone.')) return;
    try {{
        const r = await fetch('/reset', {{ method: 'POST' }});
        const d = await r.json();
        if (d.success) {{ showToast('Session reset'); await fetchState(); }}
    }} catch {{ showToast('Error resetting', true); }}
}}

// ── File inputs ──────────────────────────────────────────────────────────────
document.getElementById('dataset-input').addEventListener('change', async e => {{
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('dataset_zip', file);
    showToast('Uploading…');
    try {{
        const r = await fetch('/upload_dataset', {{ method: 'POST', body: fd }});
        const d = await r.json();
        showToast(d.message, !d.success);
        if (d.success) await fetchState();
    }} catch {{ showToast('Upload failed', true); }}
    e.target.value = '';
}});

document.getElementById('progress-input').addEventListener('change', async e => {{
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('progress_csv', file);
    try {{
        const r = await fetch('/upload_progress', {{ method: 'POST', body: fd }});
        const d = await r.json();
        showToast(d.message, !d.success);
        if (d.success) {{
            Object.assign(state, {{
                currentImage:   d.current_image,
                remainingCount: d.remaining_count,
                historyCount:   d.history_count,
                sortedCounts:   d.sorted_counts,
                totalSorted:    d.total_sorted
            }});
            renderUI();
        }}
    }} catch {{ showToast('Progress load failed', true); }}
    e.target.value = '';
}});

// ── Keyboard ─────────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    const k = e.key;
    if (/^[0-9]$/.test(k) || k === '-') {{ e.preventDefault(); selectLabel(k); return; }}
    if (k === 'Enter')     {{ e.preventDefault(); if (state.currentSelection.first_label) finalizeWithStatus('Usable');    return; }}
    if (k === "'")         {{ e.preventDefault(); if (state.currentSelection.first_label) finalizeWithStatus('Limited');   return; }}
    if (k === 'Shift')     {{ e.preventDefault(); if (state.currentSelection.first_label) finalizeWithStatus('Unusable'); return; }}
    if (k === 'z' || k === 'Z' || k === 'Backspace') {{ e.preventDefault(); executeUndo(); return; }}
    if (k === '+' || k === '=') {{ e.preventDefault(); zoomIn(); return; }}
    if (k === '_')         {{ e.preventDefault(); zoomOut(); return; }}
    if (k === 'Escape')    {{ e.preventDefault(); clearSelection(); return; }}
}});

document.addEventListener('wheel', e => {{
    const scroll = document.getElementById('image-scroll');
    if (!scroll || !scroll.contains(e.target)) return;
    if (e.ctrlKey || e.metaKey || e.shiftKey) {{
        e.preventDefault();
        e.deltaY < 0 ? zoomIn() : zoomOut();
    }}
}}, {{ passive: false }});

// ── Init ──────────────────────────────────────────────────────────────────────
window.onload = fetchState;
</script>
</body>
</html>'''