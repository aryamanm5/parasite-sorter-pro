def get_html_template(visual_guide=None, default_zoom=4):
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
        visual_guide_html = '<div class="guide-placeholder">Add visual_guide.png to your project folder</div>'

    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parasite Classifier</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔬</text></svg>">
    <style>
        :root {{
            --bg-primary: #f2f2f7;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e5e5ea;
            --bg-card: #fafafa;
            --text-primary: #1c1c1e;
            --text-secondary: #8e8e93;
            --text-tertiary: #aeaeb2;
            --accent: #a8b5c4;
            --accent-hover: #94a3b8;
            
            /* Matte pastel colors */
            --pastel-blue: #b8c5d6;
            --pastel-green: #b8d4c8;
            --pastel-yellow: #e8dcc4;
            --pastel-orange: #e4cbb8;
            --pastel-red: #dfc4c4;
            --pastel-purple: #c9c4d4;
            --pastel-pink: #dcc4d4;
            --pastel-teal: #b8d4d4;
            
            /* Status colors - matte */
            --status-usable: #c8dcc8;
            --status-usable-hover: #b8d0b8;
            --status-usable-text: #4a5d4a;
            --status-limited: #dcd8c4;
            --status-limited-hover: #d0ccb8;
            --status-limited-text: #5d5a4a;
            --status-unusable: #dcc8c8;
            --status-unusable-hover: #d0b8b8;
            --status-unusable-text: #5d4a4a;
            
            /* Alternative button colors */
            --alt-no: #c8d4dc;
            --alt-no-hover: #b8c8d0;
            --alt-yes: #dcd4c8;
            --alt-yes-hover: #d0c8b8;
            
            --border: #d1d1d6;
            --border-light: #e5e5ea;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
            --shadow-md: 0 2px 8px rgba(0,0,0,0.06);
            --shadow-lg: 0 4px 16px rgba(0,0,0,0.08);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: all 0.2s ease;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* Header */
        .header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-light);
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            min-height: 56px;
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .logo {{
            font-size: 17px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: -0.3px;
        }}

        .progress-display {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 6px 14px;
            background: var(--bg-tertiary);
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}

        .progress-display.hidden {{
            display: none;
        }}

        .progress-stat {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .progress-stat-value {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .progress-stat-label {{
            color: var(--text-secondary);
        }}

        .progress-bar-mini {{
            width: 80px;
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }}

        .progress-bar-mini-fill {{
            height: 100%;
            background: var(--pastel-green);
            transition: width 0.3s ease;
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .header-actions.hidden {{
            display: none;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            padding: 7px 14px;
            font-size: 13px;
            font-weight: 500;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            white-space: nowrap;
            letter-spacing: -0.1px;
        }}

        .btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}

        .btn-primary {{
            background: var(--pastel-blue);
            color: var(--text-primary);
        }}

        .btn-primary:hover:not(:disabled) {{
            background: var(--accent-hover);
        }}

        .btn-secondary {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .btn-secondary:hover:not(:disabled) {{
            background: var(--border);
        }}

        .btn-success {{
            background: var(--status-usable);
            color: var(--status-usable-text);
        }}

        .btn-success:hover:not(:disabled) {{
            background: var(--status-usable-hover);
        }}

        .btn-danger {{
            background: var(--status-unusable);
            color: var(--status-unusable-text);
        }}

        .btn-danger:hover:not(:disabled) {{
            background: var(--status-unusable-hover);
        }}

        .btn-icon {{
            padding: 7px 10px;
        }}

        /* Main Layout */
        .main-container {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}

        /* Sidebar */
        .sidebar {{
            width: 320px;
            min-width: 0;
            max-width: 450px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-light);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            transition: width 0.25s ease;
        }}

        .sidebar.collapsed {{
            width: 0;
            min-width: 0;
        }}

        .sidebar-resize {{
            position: absolute;
            right: 0;
            top: 0;
            width: 4px;
            height: 100%;
            cursor: ew-resize;
            background: transparent;
            z-index: 10;
        }}

        .sidebar-resize:hover {{
            background: var(--pastel-blue);
        }}

        .sidebar-toggle {{
            position: absolute;
            left: 320px;
            top: 50%;
            transform: translateY(-50%);
            width: 16px;
            height: 40px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-light);
            border-left: none;
            border-radius: 0 6px 6px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 50;
            transition: var(--transition);
            color: var(--text-tertiary);
            font-size: 10px;
        }}

        .sidebar.collapsed ~ .sidebar-toggle {{
            left: 0;
        }}

        .sidebar-toggle:hover {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}

        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }}

        .sidebar-section {{
            margin-bottom: 20px;
        }}

        .sidebar-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            margin-bottom: 10px;
        }}

        /* Guide styles */
        .guide-image {{
            width: 100%;
            border-radius: var(--radius-md);
            cursor: zoom-in;
            border: 1px solid var(--border-light);
        }}

        .guide-pdf {{
            width: 100%;
            height: 250px;
            border: 1px solid var(--border-light);
            border-radius: var(--radius-md);
        }}

        .guide-placeholder {{
            padding: 24px;
            text-align: center;
            color: var(--text-tertiary);
            font-size: 12px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
        }}

        /* Cue Table */
        .cue-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            background: var(--bg-secondary);
            border-radius: var(--radius-sm);
            overflow: hidden;
            border: 1px solid var(--border-light);
        }}

        .cue-table th {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            padding: 8px 6px;
            font-weight: 600;
            text-align: center;
            border-bottom: 1px solid var(--border-light);
        }}

        .cue-table th:first-child {{
            text-align: left;
        }}

        .cue-table td {{
            padding: 6px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-primary);
        }}

        .cue-table td:not(:first-child) {{
            text-align: center;
            font-weight: 500;
        }}

        .cue-table tr:last-child td {{
            border-bottom: none;
        }}

        .cue-table tr:hover {{
            background: var(--bg-card);
        }}

        /* Decision Flow */
        .decision-flow {{
            margin: 0;
            padding-left: 18px;
            font-size: 12px;
            line-height: 1.5;
            color: var(--text-secondary);
        }}

        .decision-flow li {{
            margin-bottom: 10px;
        }}

        .decision-flow b {{
            display: block;
            color: var(--text-primary);
            font-weight: 500;
        }}

        .decision-flow .result {{
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 11px;
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 3px;
        }}

        /* Workspace */
        .workspace {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }}

        .workspace-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 16px;
            overflow: hidden;
        }}

        /* Image Viewer */
        .image-viewer {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-light);
            overflow: hidden;
            position: relative;
            min-height: 300px;
        }}

        .image-container {{
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
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-md);
            transition: transform 0.15s ease;
        }}

        .image-info {{
            position: absolute;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(28,28,30,0.8);
            color: white;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 11px;
            font-weight: 500;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}

        .zoom-controls {{
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            gap: 2px;
            background: var(--bg-secondary);
            padding: 4px;
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-light);
        }}

        .zoom-btn {{
            width: 28px;
            height: 28px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
            transition: var(--transition);
        }}

        .zoom-btn:hover {{
            background: var(--bg-tertiary);
        }}

        .zoom-label {{
            min-width: 44px;
            text-align: center;
            font-size: 11px;
            font-weight: 500;
            line-height: 28px;
            color: var(--text-secondary);
        }}

        .placeholder {{
            text-align: center;
            color: var(--text-secondary);
            padding: 40px;
        }}

        .placeholder-icon {{
            font-size: 40px;
            margin-bottom: 12px;
            opacity: 0.8;
        }}

        .placeholder-text {{
            font-size: 14px;
            line-height: 1.5;
        }}

        .placeholder-text small {{
            color: var(--text-tertiary);
        }}

        /* Right Panel for Alternative and Status */
        .right-panel {{
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 10;
        }}

        .right-panel.hidden {{
            display: none;
        }}

        /* Alternative Buttons */
        .alternative-panel {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .alternative-panel.hidden {{
            display: none;
        }}

        .alt-btn {{
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 600;
            border: 2px solid transparent;
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: var(--transition);
            min-width: 120px;
            text-align: center;
            letter-spacing: -0.1px;
        }}

        .alt-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}

        .alt-btn.no-alt {{
            background: var(--alt-no);
            color: var(--text-primary);
            border-color: var(--alt-no);
        }}

        .alt-btn.no-alt:hover:not(:disabled) {{
            background: var(--alt-no-hover);
            border-color: var(--alt-no-hover);
        }}

        .alt-btn.yes-alt {{
            background: var(--alt-yes);
            color: var(--text-primary);
            border-color: var(--alt-yes);
        }}

        .alt-btn.yes-alt:hover:not(:disabled) {{
            background: var(--alt-yes-hover);
            border-color: var(--alt-yes-hover);
        }}

        .alt-hint {{
            font-size: 9px;
            font-weight: 500;
            opacity: 0.7;
            margin-top: 2px;
        }}

        /* Status Panel */
        .status-panel {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .status-panel.hidden {{
            display: none;
        }}

        .status-btn {{
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 600;
            border: 2px solid transparent;
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: var(--transition);
            min-width: 100px;
            text-align: center;
            letter-spacing: -0.1px;
        }}

        .status-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}

        .status-btn.usable {{
            background: var(--status-usable);
            color: var(--status-usable-text);
            border-color: var(--status-usable);
        }}

        .status-btn.usable:hover:not(:disabled) {{
            background: var(--status-usable-hover);
            border-color: var(--status-usable-hover);
        }}

        .status-btn.limited {{
            background: var(--status-limited);
            color: var(--status-limited-text);
            border-color: var(--status-limited);
        }}

        .status-btn.limited:hover:not(:disabled) {{
            background: var(--status-limited-hover);
            border-color: var(--status-limited-hover);
        }}

        .status-btn.unusable {{
            background: var(--status-unusable);
            color: var(--status-unusable-text);
            border-color: var(--status-unusable);
        }}

        .status-btn.unusable:hover:not(:disabled) {{
            background: var(--status-unusable-hover);
            border-color: var(--status-unusable-hover);
        }}

        .status-hint {{
            font-size: 9px;
            font-weight: 500;
            opacity: 0.7;
            margin-top: 2px;
        }}

        /* Classification Bar */
        .classification-bar {{
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-light);
            padding: 14px 16px;
        }}

        .classification-bar.hidden {{
            display: none;
        }}

        .selection-indicator {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 8px 12px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-sm);
            margin-bottom: 12px;
            font-size: 12px;
        }}

        .selection-indicator.hidden {{
            display: none;
        }}

        .selection-tag {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            background: var(--pastel-blue);
            color: var(--text-primary);
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        }}

        .selection-tag.alternative {{
            background: var(--pastel-orange);
        }}

        .step-indicator {{
            font-size: 10px;
            color: var(--text-tertiary);
            font-weight: 500;
        }}

        .clear-btn {{
            font-size: 11px;
            color: var(--text-tertiary);
            cursor: pointer;
            padding: 2px 8px;
            border-radius: 4px;
            transition: var(--transition);
        }}

        .clear-btn:hover {{
            background: var(--status-unusable);
            color: var(--status-unusable-text);
        }}

        .button-row {{
            display: flex;
            gap: 6px;
            justify-content: center;
            margin-bottom: 8px;
        }}

        .button-row:last-child {{
            margin-bottom: 0;
        }}

        .class-btn {{
            flex: 1;
            max-width: 130px;
            padding: 12px 8px;
            font-size: 11px;
            font-weight: 600;
            border: 2px solid var(--border);
            border-radius: var(--radius-md);
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            transition: var(--transition);
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            letter-spacing: -0.1px;
        }}

        .class-btn:hover:not(:disabled) {{
            border-color: var(--pastel-blue);
            background: var(--bg-card);
        }}

        .class-btn:disabled {{
            opacity: 0.25;
            cursor: not-allowed;
        }}

        .class-btn.selected {{
            background: var(--pastel-blue);
            border-color: var(--accent-hover);
        }}

        .class-btn .key-hint {{
            font-size: 9px;
            color: var(--text-tertiary);
            font-weight: 500;
            background: var(--bg-tertiary);
            padding: 1px 5px;
            border-radius: 3px;
        }}

        .class-btn.selected .key-hint {{
            background: rgba(0,0,0,0.1);
            color: var(--text-primary);
        }}

        .class-btn .count-badge {{
            font-size: 10px;
            font-weight: 600;
            color: var(--text-tertiary);
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 8px;
            min-width: 20px;
        }}

        .class-btn .count-badge.has-items {{
            background: var(--pastel-green);
            color: var(--status-usable-text);
        }}

        .class-btn.selected .count-badge {{
            background: rgba(0,0,0,0.1);
            color: var(--text-primary);
        }}

        /* Toast */
        .toast {{
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: var(--text-primary);
            color: var(--bg-secondary);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
            pointer-events: none;
        }}

        .toast.visible {{
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }}

        .toast.error {{
            background: var(--status-unusable-text);
        }}

        /* Lightbox */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.85);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            cursor: zoom-out;
        }}

        .lightbox.visible {{
            display: flex;
        }}

        .lightbox img {{
            max-width: 90%;
            max-height: 90%;
            border-radius: var(--radius-md);
        }}

        /* Unsaved Changes Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }}

        .modal-overlay.visible {{
            display: flex;
        }}

        .modal {{
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: var(--shadow-lg);
        }}

        .modal-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}

        .modal-message {{
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 20px;
            line-height: 1.5;
        }}

        .modal-actions {{
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }}

        /* File Input Hidden */
        input[type="file"] {{
            display: none;
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .sidebar {{
                width: 280px;
            }}

            .class-btn {{
                padding: 10px 6px;
                font-size: 10px;
                max-width: 110px;
            }}

            .right-panel {{
                position: static;
                transform: none;
                flex-direction: row;
                justify-content: center;
                padding: 10px;
                background: var(--bg-secondary);
                border-bottom: 1px solid var(--border-light);
            }}
        }}
    </style>
</head>
<body>
    <!-- Lightbox -->
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <img id="lightbox-img" src="" alt="Preview">
    </div>

    <!-- Unsaved Changes Modal -->
    <div class="modal-overlay" id="unsaved-modal">
        <div class="modal">
            <div class="modal-title">⚠️ Unsaved Changes</div>
            <div class="modal-message">
                You have unsorted images and unsaved progress. Are you sure you want to leave? Your progress will be lost.
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closeUnsavedModal()">Stay</button>
                <button class="btn btn-success" onclick="saveAndLeave()">Save Progress</button>
                <button class="btn btn-danger" onclick="confirmLeave()">Leave Anyway</button>
            </div>
        </div>
    </div>

    <!-- Header -->
    <header class="header">
        <div class="header-left">
            <div class="logo">
                <span>🔬</span>
                <span>Parasite Classifier</span>
            </div>

            <div class="progress-display hidden" id="progress-display">
                <div class="progress-stat">
                    <span class="progress-stat-value" id="remaining-count">0</span>
                    <span class="progress-stat-label">left</span>
                </div>
                <div class="progress-bar-mini">
                    <div class="progress-bar-mini-fill" id="progress-fill"></div>
                </div>
                <div class="progress-stat">
                    <span class="progress-stat-value" id="sorted-count">0</span>
                    <span class="progress-stat-label">done</span>
                </div>
            </div>
        </div>

        <div class="header-actions hidden" id="header-actions">
            <button class="btn btn-secondary" id="undo-btn" disabled onclick="executeUndo()">
                ↩ Undo
            </button>
            <button class="btn btn-secondary" id="save-btn" disabled onclick="saveProgress()">
                💾 Save
            </button>
            <input type="file" id="progress-input" accept=".csv">
            <button class="btn btn-secondary" id="load-btn" disabled onclick="document.getElementById('progress-input').click()">
                📤 Load
            </button>
            <button class="btn btn-success" id="download-btn" disabled onclick="downloadSorted()">
                📥 Download
            </button>
            <button class="btn btn-danger btn-icon" onclick="resetSession()" title="Reset">
                🔄
            </button>
        </div>

        <div id="upload-section">
            <input type="file" id="dataset-input" accept=".zip">
            <button class="btn btn-primary" onclick="document.getElementById('dataset-input').click()">
                📦 Upload Dataset
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-resize" id="sidebar-resize"></div>
            <div class="sidebar-content">
                <!-- Visual Guide -->
                <div class="sidebar-section">
                    <div class="sidebar-title">Visual Guide</div>
                    {visual_guide_html}
                </div>

                <!-- Cue Table -->
                <div class="sidebar-section">
                    <div class="sidebar-title">ER / MR / LR Cues</div>
                    <table class="cue-table">
                        <thead>
                            <tr>
                                <th>Cue</th>
                                <th>ER</th>
                                <th>MR</th>
                                <th>LR</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Cytoplasm:nucleus ratio</td>
                                <td>≤0.5</td>
                                <td>0.5–1</td>
                                <td>≥1</td>
                            </tr>
                            <tr>
                                <td>Appliqué/accolé position</td>
                                <td>+++</td>
                                <td>+</td>
                                <td>–</td>
                            </tr>
                            <tr>
                                <td>Double-dot chromatin</td>
                                <td>++</td>
                                <td>+</td>
                                <td>–</td>
                            </tr>
                            <tr>
                                <td>Crescent/comma cytoplasm</td>
                                <td>+++</td>
                                <td>–</td>
                                <td>–</td>
                            </tr>
                            <tr>
                                <td>Circular ring shape</td>
                                <td>±</td>
                                <td>+++</td>
                                <td>+</td>
                            </tr>
                            <tr>
                                <td>Amoeboid cytoplasm</td>
                                <td>–</td>
                                <td>±</td>
                                <td>+</td>
                            </tr>
                            <tr>
                                <td>Maurer's clefts</td>
                                <td>–</td>
                                <td>±</td>
                                <td>++</td>
                            </tr>
                            <tr>
                                <td>Hemozoin pigment</td>
                                <td>–</td>
                                <td>±</td>
                                <td>+</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Decision Flow -->
                <div class="sidebar-section">
                    <div class="sidebar-title">Quick Decision Flow</div>
                    <ol class="decision-flow">
                        <li>
                            <b>Cytoplasm band vs nucleus diameter</b>
                            <span class="result">→ ER / MR / LR</span>
                        </li>
                        <li>
                            <b>Pigment granules or Maurer's clefts?</b>
                            <span class="result">→ MR or LR</span>
                        </li>
                        <li>
                            <b>Minimal cytoplasm, chromatin-dominant, comma/crescent, appliqué, or double-dot</b>
                            <span class="result">→ ER</span>
                        </li>
                        <li>
                            <b>Perfect "textbook" ring shape</b>
                            <span class="result">→ MR</span>
                        </li>
                        <li>
                            <b>Dense stippling, hemozoin, amoeboid</b>
                            <span class="result">→ LR</span>
                        </li>
                    </ol>
                </div>
            </div>
        </aside>

        <!-- Sidebar Toggle -->
        <button class="sidebar-toggle" id="sidebar-toggle" onclick="toggleSidebar()">
            <span id="toggle-icon">‹</span>
        </button>

        <!-- Workspace -->
        <main class="workspace">
            <div class="workspace-content">
                <!-- Image Viewer -->
                <div class="image-viewer" id="image-viewer">
                    <div class="placeholder" id="placeholder">
                        <div class="placeholder-icon">📦</div>
                        <div class="placeholder-text">
                            Upload a ZIP file to begin<br>
                            <small>PNG, JPG, GIF, BMP, TIFF, WebP supported</small>
                        </div>
                    </div>

                    <div class="image-container" id="image-container" style="display: none;">
                        <img id="current-image" src="" alt="Current image">
                    </div>

                    <div class="zoom-controls" id="zoom-controls" style="display: none;">
                        <button class="zoom-btn" onclick="zoomOut()">−</button>
                        <span class="zoom-label" id="zoom-label">100%</span>
                        <button class="zoom-btn" onclick="zoomIn()">+</button>
                        <button class="zoom-btn" onclick="resetZoom()">↺</button>
                    </div>

                    <div class="image-info" id="image-info" style="display: none;">
                        <span id="filename-display"></span>
                    </div>

                    <!-- Right Panel for Alternative and Status -->
                    <div class="right-panel hidden" id="right-panel">
                        <!-- Alternative Panel -->
                        <div class="alternative-panel hidden" id="alternative-panel">
                            <button class="alt-btn no-alt" onclick="selectAlternative(false)" id="alt-no">
                                No Alternative
                                <div class="alt-hint">Enter</div>
                            </button>
                            <button class="alt-btn yes-alt" onclick="selectAlternative(true)" id="alt-yes">
                                One Alternative
                                <div class="alt-hint">Shift</div>
                            </button>
                        </div>

                        <!-- Status Panel -->
                        <div class="status-panel hidden" id="status-panel">
                            <button class="status-btn usable" onclick="finalizeWithStatus('Usable')" id="status-usable">
                                Usable
                                <div class="status-hint">Enter</div>
                            </button>
                            <button class="status-btn limited" onclick="finalizeWithStatus('Limited')" id="status-limited">
                                Limited
                                <div class="status-hint">'</div>
                            </button>
                            <button class="status-btn unusable" onclick="finalizeWithStatus('Unusable')" id="status-unusable">
                                Unusable
                                <div class="status-hint">Shift</div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Classification Bar -->
            <div class="classification-bar hidden" id="classification-bar">
                <!-- Selection Indicator -->
                <div class="selection-indicator hidden" id="selection-indicator">
                    <span style="color: var(--text-secondary);">Selected:</span>
                    <span class="selection-tag" id="label-tag"></span>
                    <span class="selection-tag alternative" id="alt-tag" style="display: none;"></span>
                    <span class="step-indicator" id="step-indicator"></span>
                    <span class="clear-btn" onclick="clearSelection()">Clear</span>
                </div>

                <!-- Row 1: Asexual Stages -->
                <div class="button-row">
                    <button class="class-btn" data-key="1" onclick="selectLabel('1')">
                        Early Ring
                        <span class="key-hint">1</span>
                        <span class="count-badge" id="count-1">0</span>
                    </button>
                    <button class="class-btn" data-key="2" onclick="selectLabel('2')">
                        Middle Ring
                        <span class="key-hint">2</span>
                        <span class="count-badge" id="count-2">0</span>
                    </button>
                    <button class="class-btn" data-key="3" onclick="selectLabel('3')">
                        Late Ring
                        <span class="key-hint">3</span>
                        <span class="count-badge" id="count-3">0</span>
                    </button>
                    <button class="class-btn" data-key="4" onclick="selectLabel('4')">
                        Trophozoite
                        <span class="key-hint">4</span>
                        <span class="count-badge" id="count-4">0</span>
                    </button>
                    <button class="class-btn" data-key="5" onclick="selectLabel('5')">
                        Schizont
                        <span class="key-hint">5</span>
                        <span class="count-badge" id="count-5">0</span>
                    </button>
                </div>

                <!-- Row 2: Other Classes -->
                <div class="button-row">
                    <button class="class-btn" data-key="6" onclick="selectLabel('6')">
                        Gametocyte
                        <span class="key-hint">6</span>
                        <span class="count-badge" id="count-6">0</span>
                    </button>
                    <button class="class-btn" data-key="7" onclick="selectLabel('7')">
                        Merozoite
                        <span class="key-hint">7</span>
                        <span class="count-badge" id="count-7">0</span>
                    </button>
                    <button class="class-btn" data-key="8" onclick="selectLabel('8')">
                        Other Artefact
                        <span class="key-hint">8</span>
                        <span class="count-badge" id="count-8">0</span>
                    </button>
                    <button class="class-btn" data-key="9" onclick="selectLabel('9')">
                        Platelet
                        <span class="key-hint">9</span>
                        <span class="count-badge" id="count-9">0</span>
                    </button>
                    <button class="class-btn" data-key="0" onclick="selectLabel('0')">
                        Uninfected
                        <span class="key-hint">0</span>
                        <span class="count-badge" id="count-0">0</span>
                    </button>
                    <button class="class-btn" data-key="-" onclick="selectLabel('-')">
                        Cannot Determine
                        <span class="key-hint">-</span>
                        <span class="count-badge" id="count--">0</span>
                    </button>
                </div>
            </div>
        </main>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script>
        // =====================================================================
        // CONFIGURATION
        // =====================================================================
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

        const AUTO_ADVANCE = ['0', '-'];
        const DEFAULT_ZOOM = {default_zoom};

        // =====================================================================
        // STATE
        // =====================================================================
        let state = {{
            uploadComplete: false,
            currentImage: null,
            remainingCount: 0,
            historyCount: 0,
            sortedCounts: {{}},
            totalSorted: 0,
            currentSelection: {{
                label: null,
                has_alternative: null,
                step: 'label'
            }}
        }};

        let zoom = DEFAULT_ZOOM;
        let sidebarWidth = 320;
        let pendingLeave = null;

        // =====================================================================
        // UNSAVED CHANGES HANDLING
        // =====================================================================
        function hasUnsavedChanges() {{
            return state.uploadComplete && state.remainingCount > 0 && state.historyCount > 0;
        }}

        function showUnsavedModal(callback) {{
            pendingLeave = callback;
            document.getElementById('unsaved-modal').classList.add('visible');
        }}

        function closeUnsavedModal() {{
            document.getElementById('unsaved-modal').classList.remove('visible');
            pendingLeave = null;
        }}

        function saveAndLeave() {{
            saveProgress();
            closeUnsavedModal();
            if (pendingLeave) pendingLeave();
        }}

        function confirmLeave() {{
            closeUnsavedModal();
            if (pendingLeave) pendingLeave();
        }}

        // Beforeunload handler
        window.addEventListener('beforeunload', (e) => {{
            if (hasUnsavedChanges()) {{
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }}
        }});

        // =====================================================================
        // UI HELPERS
        // =====================================================================
        function showToast(message, isError = false) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = isError ? 'toast error visible' : 'toast visible';
            setTimeout(() => toast.className = 'toast', 2500);
        }}

        function openLightbox(src) {{
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').classList.add('visible');
        }}

        function closeLightbox() {{
            document.getElementById('lightbox').classList.remove('visible');
        }}

        function updateUI() {{
            const uploadComplete = state.uploadComplete;
            const hasImage = state.currentImage !== null;
            const hasLabel = state.currentSelection.label !== null;
            const hasSorted = state.totalSorted > 0;
            const hasHistory = state.historyCount > 0;
            const currentStep = state.currentSelection.step;

            // Header visibility
            document.getElementById('header-actions').classList.toggle('hidden', !uploadComplete);
            document.getElementById('progress-display').classList.toggle('hidden', !uploadComplete);
            
            // Button states
            document.getElementById('undo-btn').disabled = !hasHistory;
            document.getElementById('save-btn').disabled = !hasSorted;
            document.getElementById('load-btn').disabled = !uploadComplete;
            document.getElementById('download-btn').disabled = !hasSorted;

            // Progress stats
            document.getElementById('remaining-count').textContent = state.remainingCount;
            document.getElementById('sorted-count').textContent = state.totalSorted;

            // Progress bar
            const total = state.remainingCount + state.totalSorted;
            const pct = total > 0 ? Math.round((state.totalSorted / total) * 100) : 0;
            document.getElementById('progress-fill').style.width = pct + '%';

            // Update count badges on buttons
            updateCountBadges();

            // Image viewer
            const placeholder = document.getElementById('placeholder');
            const imageContainer = document.getElementById('image-container');
            const zoomControls = document.getElementById('zoom-controls');
            const imageInfo = document.getElementById('image-info');

            if (!uploadComplete) {{
                placeholder.style.display = 'block';
                imageContainer.style.display = 'none';
                zoomControls.style.display = 'none';
                imageInfo.style.display = 'none';
            }} else if (hasImage) {{
                placeholder.style.display = 'none';
                imageContainer.style.display = 'flex';
                zoomControls.style.display = 'flex';
                imageInfo.style.display = 'block';
                
                const img = document.getElementById('current-image');
                img.src = `/serve_image/${{encodeURIComponent(state.currentImage)}}?t=${{Date.now()}}`;
                document.getElementById('filename-display').textContent = state.currentImage;
            }} else {{
                placeholder.innerHTML = `
                    <div class="placeholder-icon">🎉</div>
                    <div class="placeholder-text">
                        All done!<br>
                        <small>Click Download to get results</small>
                    </div>
                `;
                placeholder.style.display = 'block';
                imageContainer.style.display = 'none';
                zoomControls.style.display = 'none';
                imageInfo.style.display = 'none';
            }}

            // Classification bar
            document.getElementById('classification-bar').classList.toggle('hidden', !uploadComplete || !hasImage);
            
            // Right panel visibility
            const rightPanel = document.getElementById('right-panel');
            const altPanel = document.getElementById('alternative-panel');
            const statusPanel = document.getElementById('status-panel');

            rightPanel.classList.toggle('hidden', !uploadComplete || !hasImage || !hasLabel);
            altPanel.classList.toggle('hidden', currentStep !== 'alternative');
            statusPanel.classList.toggle('hidden', currentStep !== 'status');

            // Update button states
            updateButtonStates();
        }}

        function updateCountBadges() {{
            for (const [key, name] of Object.entries(CLASS_MAP)) {{
                const counts = state.sortedCounts[name] || {{ total: 0 }};
                const count = counts.total || 0;
                const badge = document.getElementById('count-' + key);
                
                if (badge) {{
                    badge.textContent = count;
                    badge.classList.toggle('has-items', count > 0);
                }}
            }}
        }}

        function updateButtonStates() {{
            const label = state.currentSelection.label;
            const hasAlternative = state.currentSelection.has_alternative;
            const currentStep = state.currentSelection.step;
            const hasLabel = label !== null;

            // Update all class buttons
            document.querySelectorAll('.class-btn').forEach(btn => {{
                const key = btn.dataset.key;
                
                btn.classList.remove('selected');
                btn.disabled = false;

                if (!state.currentImage) {{
                    btn.disabled = true;
                    return;
                }}

                if (label === key) {{
                    btn.classList.add('selected');
                }}

                // Disable all buttons if we've moved past label selection
                if (hasLabel && currentStep !== 'label') {{
                    btn.disabled = true;
                }}
            }});

            // Update selection indicator
            const indicator = document.getElementById('selection-indicator');
            const labelTag = document.getElementById('label-tag');
            const altTag = document.getElementById('alt-tag');
            const stepIndicator = document.getElementById('step-indicator');

            if (hasLabel) {{
                indicator.classList.remove('hidden');
                labelTag.textContent = CLASS_MAP[label];
                
                if (hasAlternative !== null) {{
                    altTag.textContent = hasAlternative ? 'Has Alternative' : 'No Alternative';
                    altTag.style.display = 'inline-flex';
                }} else {{
                    altTag.style.display = 'none';
                }}

                // Show step indicator
                if (currentStep === 'alternative') {{
                    stepIndicator.textContent = '→ Select Alternative';
                }} else if (currentStep === 'status') {{
                    stepIndicator.textContent = '→ Select Status';
                }} else {{
                    stepIndicator.textContent = '';
                }}
            }} else {{
                indicator.classList.add('hidden');
            }}
        }}

        // =====================================================================
        // ZOOM
        // =====================================================================
        function setZoom(newZoom) {{
            zoom = Math.max(0.25, Math.min(8, newZoom));
            const img = document.getElementById('current-image');
            if (img) {{
                img.style.transform = `scale(${{zoom}})`;
            }}
            document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';
        }}

        function zoomIn() {{ setZoom(zoom + 0.25); }}
        function zoomOut() {{ setZoom(zoom - 0.25); }}
        function resetZoom() {{ setZoom(DEFAULT_ZOOM); }}

        // =====================================================================
        // SIDEBAR
        // =====================================================================
        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            const toggle = document.getElementById('sidebar-toggle');
            const icon = document.getElementById('toggle-icon');

            sidebar.classList.toggle('collapsed');
            
            if (sidebar.classList.contains('collapsed')) {{
                icon.textContent = '›';
                toggle.style.left = '0';
            }} else {{
                icon.textContent = '‹';
                toggle.style.left = sidebarWidth + 'px';
            }}
        }}

        // Sidebar resize
        (function initSidebarResize() {{
            const sidebar = document.getElementById('sidebar');
            const resizer = document.getElementById('sidebar-resize');
            const toggle = document.getElementById('sidebar-toggle');

            let isResizing = false;

            resizer.addEventListener('mousedown', (e) => {{
                isResizing = true;
                document.body.style.cursor = 'ew-resize';
                document.body.style.userSelect = 'none';
            }});

            document.addEventListener('mousemove', (e) => {{
                if (!isResizing) return;
                
                const newWidth = Math.max(0, Math.min(450, e.clientX));
                sidebarWidth = newWidth;
                
                if (newWidth < 80) {{
                    sidebar.classList.add('collapsed');
                    toggle.style.left = '0';
                    document.getElementById('toggle-icon').textContent = '›';
                }} else {{
                    sidebar.classList.remove('collapsed');
                    sidebar.style.width = newWidth + 'px';
                    toggle.style.left = newWidth + 'px';
                    document.getElementById('toggle-icon').textContent = '‹';
                }}
            }});

            document.addEventListener('mouseup', () => {{
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }});
        }})();

        // =====================================================================
        // API CALLS
        // =====================================================================
        async function fetchState() {{
            try {{
                const res = await fetch('/state');
                const data = await res.json();
                
                state.uploadComplete = data.upload_complete;
                state.currentImage = data.current_image;
                state.remainingCount = data.remaining_count;
                state.historyCount = data.history_count;
                state.sortedCounts = data.sorted_counts;
                state.totalSorted = data.total_sorted;
                state.currentSelection = data.current_selection || {{ label: null, has_alternative: null, step: 'label' }};
                
                // Set initial zoom
                setZoom(DEFAULT_ZOOM);
                updateUI();
            }} catch (e) {{
                console.error('Failed to fetch state:', e);
            }}
        }}

        async function selectLabel(key) {{
            if (!state.currentImage) return;
            if (state.currentSelection.step !== 'label') return;

            try {{
                const res = await fetch('/select_label', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key }})
                }});

                const data = await res.json();

                if (data.success) {{
                    // Check if auto-advanced
                    if (data.auto_advanced) {{
                        showToast(data.message);
                        state.currentImage = data.current_image;
                        state.remainingCount = data.remaining_count;
                        state.historyCount = data.history_count;
                        state.sortedCounts = data.sorted_counts;
                        state.totalSorted = data.total_sorted;
                        state.currentSelection = data.current_selection;
                        setZoom(DEFAULT_ZOOM);
                        updateUI();
                    }} else {{
                        state.currentSelection = data.selection;
                        updateUI();
                    }}
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Error selecting label', true);
            }}
        }}

        async function selectAlternative(hasAlternative) {{
            if (state.currentSelection.step !== 'alternative') return;

            try {{
                const res = await fetch('/select_alternative', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ has_alternative: hasAlternative }})
                }});

                const data = await res.json();

                if (data.success) {{
                    state.currentSelection = data.selection;
                    updateUI();
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Error selecting alternative', true);
            }}
        }}

        async function clearSelection() {{
            try {{
                const res = await fetch('/clear_selection', {{ method: 'POST' }});
                const data = await res.json();

                if (data.success) {{
                    state.currentSelection = data.selection;
                    updateUI();
                }}
            }} catch (e) {{
                showToast('Error clearing selection', true);
            }}
        }}

        async function finalizeWithStatus(status) {{
            if (state.currentSelection.step !== 'status') return;

            try {{
                const res = await fetch('/finalize', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ status }})
                }});

                const data = await res.json();

                if (data.success) {{
                    showToast(data.message);
                    state.currentImage = data.current_image;
                    state.remainingCount = data.remaining_count;
                    state.historyCount = data.history_count;
                    state.sortedCounts = data.sorted_counts;
                    state.totalSorted = data.total_sorted;
                    state.currentSelection = data.current_selection;
                    
                    setZoom(DEFAULT_ZOOM);
                    updateUI();
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Error finalizing', true);
            }}
        }}

        async function executeUndo() {{
            try {{
                const res = await fetch('/undo', {{ method: 'POST' }});
                const data = await res.json();

                if (data.success) {{
                    showToast('Undo successful');
                    state.currentImage = data.current_image;
                    state.remainingCount = data.remaining_count;
                    state.historyCount = data.history_count;
                    state.sortedCounts = data.sorted_counts;
                    state.totalSorted = data.total_sorted;
                    state.currentSelection = data.current_selection;
                    
                    updateUI();
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Error undoing', true);
            }}
        }}

        function downloadSorted() {{
            if (state.totalSorted > 0) {{
                window.location.href = '/download';
            }}
        }}

        function saveProgress() {{
            if (state.totalSorted > 0) {{
                window.location.href = '/save_progress';
            }}
        }}

        async function resetSession() {{
            if (hasUnsavedChanges()) {{
                showUnsavedModal(async () => {{
                    await doReset();
                }});
            }} else {{
                if (!confirm('Reset all data? This cannot be undone.')) return;
                await doReset();
            }}
        }}

        async function doReset() {{
            try {{
                const res = await fetch('/reset', {{ method: 'POST' }});
                const data = await res.json();

                if (data.success) {{
                    showToast('Session reset');
                    await fetchState();
                }}
            }} catch (e) {{
                showToast('Error resetting', true);
            }}
        }}

        // =====================================================================
        // FILE UPLOADS
        // =====================================================================
        document.getElementById('dataset-input').addEventListener('change', async (e) => {{
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('dataset_zip', file);

            showToast('Uploading...');

            try {{
                const res = await fetch('/upload_dataset', {{
                    method: 'POST',
                    body: formData
                }});

                const data = await res.json();

                if (data.success) {{
                    showToast(data.message);
                    await fetchState();
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Upload failed', true);
            }}

            e.target.value = '';
        }});

        document.getElementById('progress-input').addEventListener('change', async (e) => {{
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('progress_csv', file);

            try {{
                const res = await fetch('/upload_progress', {{
                    method: 'POST',
                    body: formData
                }});

                const data = await res.json();

                if (data.success) {{
                    showToast(data.message);
                    state.currentImage = data.current_image;
                    state.remainingCount = data.remaining_count;
                    state.historyCount = data.history_count;
                    state.sortedCounts = data.sorted_counts;
                    state.totalSorted = data.total_sorted;
                    updateUI();
                }} else {{
                    showToast(data.message, true);
                }}
            }} catch (e) {{
                showToast('Progress load failed', true);
            }}

            e.target.value = '';
        }});

        // =====================================================================
        // KEYBOARD SHORTCUTS
        // =====================================================================
        document.addEventListener('keydown', (e) => {{
            // Ignore if typing in an input or modal is open
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (document.getElementById('unsaved-modal').classList.contains('visible')) return;

            const key = e.key;
            const currentStep = state.currentSelection.step;

            // Number keys 0-9 and minus for classification (only in label step)
            if (currentStep === 'label' && (/^[0-9]$/.test(key) || key === '-')) {{
                e.preventDefault();
                selectLabel(key);
                return;
            }}

            // Alternative step shortcuts
            if (currentStep === 'alternative') {{
                if (key === 'Enter') {{
                    e.preventDefault();
                    selectAlternative(false);  // No Alternative
                    return;
                }}
                if (key === 'Shift') {{
                    e.preventDefault();
                    selectAlternative(true);   // One Alternative
                    return;
                }}
            }}

            // Status step shortcuts
            if (currentStep === 'status') {{
                if (key === 'Enter') {{
                    e.preventDefault();
                    finalizeWithStatus('Usable');
                    return;
                }}
                if (key === "'") {{
                    e.preventDefault();
                    finalizeWithStatus('Limited');
                    return;
                }}
                if (key === 'Shift') {{
                    e.preventDefault();
                    finalizeWithStatus('Unusable');
                    return;
                }}
            }}

            // Undo
            if (key === 'z' || key === 'Z' || key === 'Backspace') {{
                e.preventDefault();
                executeUndo();
                return;
            }}

            // Zoom
            if (key === '+' || key === '=') {{
                e.preventDefault();
                zoomIn();
                return;
            }}

            if (key === '_') {{
                e.preventDefault();
                zoomOut();
                return;
            }}

            // Clear selection with Escape
            if (key === 'Escape') {{
                e.preventDefault();
                clearSelection();
                return;
            }}
        }});

        // Zoom with mouse wheel
        document.addEventListener('wheel', (e) => {{
            const container = document.getElementById('image-container');
            if (!container || !container.contains(e.target)) return;

            if (e.ctrlKey || e.metaKey || e.shiftKey) {{
                e.preventDefault();
                if (e.deltaY < 0) zoomIn();
                else zoomOut();
            }}
        }}, {{ passive: false }});

        // =====================================================================
        // INIT
        // =====================================================================
        window.onload = fetchState;
    </script>
</body>
</html>
'''