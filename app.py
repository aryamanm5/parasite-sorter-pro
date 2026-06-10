import os
import zipfile
import base64
import shutil
import uuid
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from flask import Flask, render_template_string, jsonify, request, send_file, session
from werkzeug.utils import secure_filename
import tempfile
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# =========================================================================
#  CONFIGURATION
# =========================================================================
# Use /tmp for cloud deployments or create local folder
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
    UPLOAD_FOLDER = '/tmp/parasite_sorter'
else:
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix='parasite_sorter_')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
SESSION_TIMEOUT_HOURS = 2

# -------------------------------------------------------------------------
#  BUILT-IN VISUAL GUIDE
# -------------------------------------------------------------------------
# Put your visual guide file in your GitHub repo, then set the filename here.
#
# Examples:
#   TOP_VISUAL_GUIDE_FILE = "visual_guide.png"
#   TOP_VISUAL_GUIDE_FILE = "assets/visual_guide.jpg"
#   TOP_VISUAL_GUIDE_FILE = "static/visual_guide.pdf"
#
# Supported display types: png, jpg, jpeg, gif, bmp, webp, pdf
#
# If you leave this blank or the file does not exist, the app will show
# a placeholder message.
TOP_VISUAL_GUIDE_FILE = "visual_guide.png"

# Store session data in memory
sessions_data = {}
sessions_lock = threading.Lock()

CLASS_MAPPING = {
    '1': '1-ER',
    '2': '2-MR',
    '3': '3-LR',
    '4': '4-Troph',
    '5': '5-Schizont',
    '6': '6-Gametocyte',
    '7': '7-Merozoite',
    '8': '8-Indeterminate',
    '9': '9-Uninfected'
}

# =========================================================================
#  SESSION MANAGEMENT
# =========================================================================
def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_session_data():
    session_id = get_session_id()

    with sessions_lock:
        if session_id not in sessions_data:
            session_dir = os.path.join(UPLOAD_FOLDER, session_id)
            os.makedirs(session_dir, exist_ok=True)

            sessions_data[session_id] = {
                'created': datetime.now(),
                'last_access': datetime.now(),
                'session_dir': session_dir,
                'unsorted_dir': os.path.join(session_dir, 'unsorted'),
                'sorted_dir': os.path.join(session_dir, 'sorted'),
                'docx_content': [],
                'guide_type': None,
                'guide_pdf_path': None,
                'history': [],
                'upload_complete': False
            }

            os.makedirs(sessions_data[session_id]['unsorted_dir'], exist_ok=True)
            os.makedirs(sessions_data[session_id]['sorted_dir'], exist_ok=True)

            for class_name in CLASS_MAPPING.values():
                os.makedirs(os.path.join(sessions_data[session_id]['sorted_dir'], class_name), exist_ok=True)

        sessions_data[session_id]['last_access'] = datetime.now()
        return sessions_data[session_id]


def cleanup_old_sessions():
    cutoff = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)

    with sessions_lock:
        expired = [sid for sid, data in sessions_data.items() if data['last_access'] < cutoff]

        for sid in expired:
            try:
                shutil.rmtree(sessions_data[sid]['session_dir'], ignore_errors=True)
                del sessions_data[sid]
                print(f"Cleaned up session: {sid}")
            except Exception as e:
                print(f"Error cleaning session {sid}: {e}")


# =========================================================================
#  WORD DOCUMENT PARSING
# =========================================================================
def get_mime_type(img_data):
    if img_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif img_data.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif img_data.startswith(b'GIF87a') or img_data.startswith(b'GIF89a'):
        return 'image/gif'
    return 'image/jpeg'


def is_heading(text):
    clean = text.strip().lower()
    headings = [
        "early ring",
        "middle ring",
        "late ring",
        "trophozoites",
        "schizonts",
        "gametocytes",
        "merozoites",
        "hemozoin",
        "plasmodium falciparum staging"
    ]
    return any(clean == h or clean.startswith(h) for h in headings)


def extract_docx_content(docx_path):
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'v': 'urn:schemas-microsoft-com:vml'
    }

    if not os.path.exists(docx_path):
        return []

    try:
        with zipfile.ZipFile(docx_path) as docx:
            rels_text = docx.read('word/_rels/document.xml.rels')
            rels_root = ET.fromstring(rels_text)

            rels = {}
            for rel in rels_root:
                id_attr = rel.get('Id')
                target_attr = rel.get('Target')
                if id_attr and target_attr:
                    rels[id_attr] = target_attr

            doc_text = docx.read('word/document.xml')
            doc_root = ET.fromstring(doc_text)

            elements = []
            body = doc_root.find('w:body', namespaces)

            if body is None:
                return []

            for p in body.findall('.//w:p', namespaces):
                text_pieces = []

                for t in p.findall('.//w:t', namespaces):
                    if t.text:
                        text_pieces.append(t.text)

                p_text = "".join(text_pieces).strip()
                p_images = []

                for blip in p.findall('.//a:blip', namespaces):
                    embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

                    if embed_id and embed_id in rels:
                        img_path = rels[embed_id]
                        full_img_path = img_path if img_path.startswith('word/') else 'word/' + img_path

                        try:
                            img_data = docx.read(full_img_path)
                            mime = get_mime_type(img_data)
                            b64_str = base64.b64encode(img_data).decode('utf-8')
                            p_images.append(f"data:{mime};base64,{b64_str}")
                        except KeyError:
                            pass

                for img_data_elem in p.findall('.//v:imagedata', namespaces):
                    rel_id = img_data_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')

                    if rel_id and rel_id in rels:
                        img_path = rels[rel_id]
                        full_img_path = img_path if img_path.startswith('word/') else 'word/' + img_path

                        try:
                            img_data = docx.read(full_img_path)
                            mime = get_mime_type(img_data)
                            b64_str = base64.b64encode(img_data).decode('utf-8')
                            p_images.append(f"data:{mime};base64,{b64_str}")
                        except KeyError:
                            pass

                if p_text or p_images:
                    elements.append({
                        'text': p_text,
                        'is_heading': is_heading(p_text),
                        'images': p_images
                    })

            return elements

    except Exception as e:
        print(f"Error reading docx: {e}")
        return []


# =========================================================================
#  FILE UTILITIES
# =========================================================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def allowed_reference_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'docx', 'pdf'}


def get_images_list(directory):
    if not directory or not os.path.exists(directory):
        return []

    try:
        files = [f for f in os.listdir(directory) if allowed_file(f)]
        return sorted(files)
    except Exception:
        return []


def get_sorted_counts(sorted_dir):
    counts = {}

    for class_name in CLASS_MAPPING.values():
        class_dir = os.path.join(sorted_dir, class_name)

        if os.path.exists(class_dir):
            counts[class_name] = len(get_images_list(class_dir))
        else:
            counts[class_name] = 0

    return counts


def get_builtin_visual_guide_info():
    if not TOP_VISUAL_GUIDE_FILE:
        return {
            'exists': False,
            'url': None,
            'type': None
        }

    full_path = os.path.abspath(TOP_VISUAL_GUIDE_FILE)

    if not os.path.exists(full_path):
        return {
            'exists': False,
            'url': None,
            'type': None
        }

    ext = os.path.splitext(full_path)[1].lower().replace('.', '')

    if ext == 'pdf':
        guide_type = 'pdf'
    elif ext in ALLOWED_IMAGE_EXTENSIONS:
        guide_type = 'image'
    else:
        guide_type = 'unsupported'

    return {
        'exists': guide_type in {'pdf', 'image'},
        'url': '/builtin_visual_guide',
        'type': guide_type
    }


# =========================================================================
#  FLASK ROUTES
# =========================================================================
@app.route('/')
def index():
    cleanup_old_sessions()
    session_data = get_session_data()
    visual_guide = get_builtin_visual_guide_info()

    return render_template_string(
        HTML_TEMPLATE,
        doc_elements=session_data['docx_content'],
        has_docx=bool(session_data['docx_content']),
        guide_type=session_data.get('guide_type'),
        visual_guide=visual_guide
    )


@app.route('/builtin_visual_guide')
def builtin_visual_guide():
    if not TOP_VISUAL_GUIDE_FILE:
        return "No visual guide configured", 404

    full_path = os.path.abspath(TOP_VISUAL_GUIDE_FILE)

    if not os.path.exists(full_path):
        return "Visual guide not found", 404

    return send_file(full_path)


@app.route('/upload_images', methods=['POST'])
def upload_images():
    session_data = get_session_data()

    if 'images_zip' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['images_zip']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not file.filename.lower().endswith('.zip'):
        return jsonify({'success': False, 'message': 'Please upload a ZIP file'}), 400

    try:
        shutil.rmtree(session_data['unsorted_dir'], ignore_errors=True)
        os.makedirs(session_data['unsorted_dir'], exist_ok=True)

        zip_path = os.path.join(session_data['session_dir'], 'upload.zip')
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('/') or member.startswith('__MACOSX') or '/.' in member:
                    continue

                filename = os.path.basename(member)

                if filename and allowed_file(filename):
                    source = zip_ref.open(member)
                    safe_name = secure_filename(filename)
                    target_path = os.path.join(session_data['unsorted_dir'], safe_name)

                    if os.path.exists(target_path):
                        base, ext = os.path.splitext(safe_name)
                        counter = 1

                        while os.path.exists(os.path.join(session_data['unsorted_dir'], f"{base}_{counter}{ext}")):
                            counter += 1

                        target_path = os.path.join(session_data['unsorted_dir'], f"{base}_{counter}{ext}")

                    with open(target_path, 'wb') as f:
                        f.write(source.read())

        os.remove(zip_path)

        session_data['history'] = []
        session_data['upload_complete'] = True

        images = get_images_list(session_data['unsorted_dir'])

        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(images)} images',
            'image_count': len(images)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload error: {str(e)}'}), 500


@app.route('/upload_docx', methods=['POST'])
def upload_docx():
    """
    This route accepts either DOCX or PDF.

    Frontend field name remains:
        docx_file

    Accepted:
        .docx -> parsed and displayed in the left panel
        .pdf  -> embedded directly in the left panel
    """
    session_data = get_session_data()

    if 'docx_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['docx_file']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_reference_file(file.filename):
        return jsonify({'success': False, 'message': 'Please upload a DOCX or PDF file'}), 400

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()

        session_data['docx_content'] = []
        session_data['guide_type'] = ext
        session_data['guide_pdf_path'] = None

        if ext == 'docx':
            docx_path = os.path.join(session_data['session_dir'], 'reference.docx')
            file.save(docx_path)
            session_data['docx_content'] = extract_docx_content(docx_path)

            return jsonify({
                'success': True,
                'message': 'DOCX reference guide uploaded',
                'guide_type': 'docx',
                'has_content': bool(session_data['docx_content'])
            })

        if ext == 'pdf':
            pdf_path = os.path.join(session_data['session_dir'], 'reference.pdf')
            file.save(pdf_path)
            session_data['guide_pdf_path'] = pdf_path

            return jsonify({
                'success': True,
                'message': 'PDF reference guide uploaded',
                'guide_type': 'pdf',
                'pdf_url': '/serve_reference_pdf'
            })

        return jsonify({'success': False, 'message': 'Unsupported reference file'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload error: {str(e)}'}), 500


@app.route('/serve_reference_pdf')
def serve_reference_pdf():
    session_data = get_session_data()
    pdf_path = session_data.get('guide_pdf_path')

    if not pdf_path or not os.path.exists(pdf_path):
        return "No PDF uploaded", 404

    return send_file(pdf_path, mimetype='application/pdf')


@app.route('/state', methods=['GET'])
def get_state():
    session_data = get_session_data()
    images = get_images_list(session_data['unsorted_dir'])
    sorted_counts = get_sorted_counts(session_data['sorted_dir'])

    return jsonify({
        'upload_complete': session_data['upload_complete'],
        'current_image': images[0] if images else None,
        'remaining_count': len(images),
        'history_count': len(session_data['history']),
        'sorted_counts': sorted_counts,
        'total_sorted': sum(sorted_counts.values()),
        'has_docx': bool(session_data['docx_content']),
        'guide_type': session_data.get('guide_type')
    })


@app.route('/get_docx_content', methods=['GET'])
def get_docx_content():
    session_data = get_session_data()

    return jsonify({
        'success': True,
        'content': session_data['docx_content'],
        'guide_type': session_data.get('guide_type'),
        'pdf_url': '/serve_reference_pdf' if session_data.get('guide_type') == 'pdf' else None
    })


@app.route('/serve_active_image/<path:filename>')
def serve_active_image(filename):
    session_data = get_session_data()
    return send_file(os.path.join(session_data['unsorted_dir'], filename))


@app.route('/classify', methods=['POST'])
def classify():
    session_data = get_session_data()
    data = request.get_json()
    key = data.get('key')

    if not session_data['upload_complete']:
        return jsonify({'success': False, 'message': 'Please upload images first.'}), 400

    if key not in CLASS_MAPPING:
        return jsonify({'success': False, 'message': 'Invalid key.'}), 400

    images = get_images_list(session_data['unsorted_dir'])

    if not images:
        return jsonify({'success': False, 'message': 'No images left.'}), 400

    img_name = images[0]
    target_subfolder = CLASS_MAPPING[key]
    target_dir = os.path.join(session_data['sorted_dir'], target_subfolder)

    src_path = os.path.join(session_data['unsorted_dir'], img_name)
    dst_path = os.path.join(target_dir, img_name)

    stored_name = img_name

    if os.path.exists(dst_path):
        base, ext = os.path.splitext(img_name)
        counter = 1

        while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
            counter += 1

        stored_name = f"{base}_{counter}{ext}"
        dst_path = os.path.join(target_dir, stored_name)

    try:
        shutil.move(src_path, dst_path)

        session_data['history'].append({
            'original_filename': img_name,
            'stored_filename': stored_name,
            'src_dir': session_data['unsorted_dir'],
            'dst_dir': target_dir,
            'class_name': target_subfolder
        })

        next_imgs = get_images_list(session_data['unsorted_dir'])
        sorted_counts = get_sorted_counts(session_data['sorted_dir'])

        return jsonify({
            'success': True,
            'message': f'Moved to {target_subfolder}',
            'current_image': next_imgs[0] if next_imgs else None,
            'remaining_count': len(next_imgs),
            'history_count': len(session_data['history']),
            'sorted_counts': sorted_counts,
            'total_sorted': sum(sorted_counts.values())
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/undo', methods=['POST'])
def undo():
    session_data = get_session_data()

    if not session_data['history']:
        return jsonify({'success': False, 'message': 'Nothing to undo.'}), 400

    entry = session_data['history'].pop()
    current_location = os.path.join(entry['dst_dir'], entry['stored_filename'])
    restoration_target = os.path.join(entry['src_dir'], entry['original_filename'])

    if os.path.exists(restoration_target):
        base, ext = os.path.splitext(entry['original_filename'])
        counter = 1

        while os.path.exists(os.path.join(entry['src_dir'], f"{base}_{counter}{ext}")):
            counter += 1

        restoration_target = os.path.join(entry['src_dir'], f"{base}_{counter}{ext}")

    try:
        if os.path.exists(current_location):
            shutil.move(current_location, restoration_target)
            msg = "Undo successful"
        else:
            msg = "File not found"

        next_imgs = get_images_list(session_data['unsorted_dir'])
        sorted_counts = get_sorted_counts(session_data['sorted_dir'])

        return jsonify({
            'success': True,
            'message': msg,
            'current_image': next_imgs[0] if next_imgs else None,
            'remaining_count': len(next_imgs),
            'history_count': len(session_data['history']),
            'sorted_counts': sorted_counts,
            'total_sorted': sum(sorted_counts.values())
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/download_sorted', methods=['GET'])
def download_sorted():
    session_data = get_session_data()
    sorted_dir = session_data['sorted_dir']

    total_sorted = sum(get_sorted_counts(sorted_dir).values())

    if total_sorted == 0:
        return "No sorted images to download", 400

    try:
        zip_path = os.path.join(session_data['session_dir'], 'sorted_images.zip')

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for class_name in CLASS_MAPPING.values():
                class_dir = os.path.join(sorted_dir, class_name)

                if os.path.exists(class_dir):
                    for img_file in os.listdir(class_dir):
                        if allowed_file(img_file):
                            file_path = os.path.join(class_dir, img_file)
                            arcname = os.path.join(class_name, img_file)
                            zipf.write(file_path, arcname)

        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='sorted_parasite_images.zip'
        )

    except Exception as e:
        return f"Download error: {str(e)}", 500


@app.route('/reset_session', methods=['POST'])
def reset_session():
    session_data = get_session_data()

    try:
        shutil.rmtree(session_data['unsorted_dir'], ignore_errors=True)
        shutil.rmtree(session_data['sorted_dir'], ignore_errors=True)

        os.makedirs(session_data['unsorted_dir'], exist_ok=True)
        os.makedirs(session_data['sorted_dir'], exist_ok=True)

        for class_name in CLASS_MAPPING.values():
            os.makedirs(os.path.join(session_data['sorted_dir'], class_name), exist_ok=True)

        session_data['history'] = []
        session_data['upload_complete'] = False
        session_data['docx_content'] = []
        session_data['guide_type'] = None
        session_data['guide_pdf_path'] = None

        return jsonify({'success': True, 'message': 'Session reset.'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


# =========================================================================
#  HTML TEMPLATE
# =========================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parasite Image Sorter</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔬</text></svg>">

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            min-height: 100vh;
            background-color: #f1f5f9;
            color: #1e293b;
        }

        #left-panel {
            width: 410px;
            min-width: 320px;
            height: 100vh;
            overflow-y: auto;
            border-right: 2px solid #cbd5e1;
            background-color: #ffffff;
            padding: 18px;
            flex-shrink: 0;
        }

        #left-panel h1 {
            font-size: 20px;
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }

        input[type="file"] {
            display: none;
        }

        .upload-status {
            margin-top: 6px;
            font-size: 12px;
            color: #64748b;
            word-break: break-word;
        }

        .upload-status.success {
            color: #16a34a;
            font-weight: 500;
        }

        .upload-status.error {
            color: #dc2626;
        }

        .compact-status {
            font-size: 11px;
            min-height: 14px;
            margin-bottom: 5px;
        }

        .doc-paragraph {
            margin-bottom: 8px;
            line-height: 1.5;
            font-size: 13px;
            color: #334155;
        }

        .doc-heading {
            font-size: 15px;
            font-weight: bold;
            color: #1d4ed8;
            margin-top: 18px;
            margin-bottom: 6px;
            text-transform: uppercase;
        }

        .doc-images-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0 12px 0;
        }

        .doc-reference-img {
            width: 70px;
            height: 70px;
            object-fit: cover;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            cursor: zoom-in;
        }

        .doc-reference-img:hover {
            border-color: #2563eb;
            transform: scale(1.05);
        }

        .pdf-guide-frame {
            width: 100%;
            height: calc(100vh - 90px);
            min-height: 600px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background: white;
        }

        .left-guide-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 14px;
        }

        .top-panel-title {
            font-size: 13px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .builtin-guide-img {
            max-width: 100%;
            object-fit: contain;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            cursor: zoom-in;
        }

        .left-builtin-guide-img {
            width: 100%;
            max-height: 270px;
        }

        .builtin-guide-pdf,
        .left-builtin-guide-pdf {
            width: 100%;
            height: 270px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
        }

        .cue-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            background: white;
        }

        .cue-table th {
            background: #0f172a;
            color: white;
            padding: 7px 8px;
            border: 1px solid #334155;
            text-align: center;
        }

        .cue-table th:first-child {
            text-align: left;
        }

        .cue-table td {
            border: 1px solid #cbd5e1;
            padding: 6px 8px;
            vertical-align: middle;
        }

        .cue-table td:not(:first-child) {
            text-align: center;
            font-weight: 700;
        }

        .cue-table tr:nth-child(even) {
            background: #f8fafc;
        }

        .decision-flow {
            margin-left: 18px;
            font-size: 13px;
            line-height: 1.45;
            color: #334155;
        }

        .decision-flow li {
            margin-bottom: 10px;
        }

        .decision-flow b {
            display: block;
            color: #0f172a;
        }

        .decision-flow span {
            display: inline-block;
            margin-top: 2px;
            color: #2563eb;
            font-weight: 800;
        }

        #right-panel {
            flex: 1;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .stats-bar {
            background-color: #ffffff;
            padding: 12px 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            flex-shrink: 0;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-label {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
        }

        .stat-value {
            font-size: 20px;
            font-weight: bold;
            color: #0f172a;
        }

        .stat-value.highlight {
            color: #2563eb;
        }

        .progress-container {
            width: 180px;
        }

        .progress-bar {
            height: 8px;
            background-color: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #2563eb, #16a34a);
            transition: width 0.3s;
        }

        .progress-text {
            font-size: 11px;
            color: #64748b;
            margin-top: 2px;
            text-align: center;
        }

        .workspace-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 15px;
            gap: 15px;
            overflow: hidden;
        }

        .main-workspace-row {
            flex: 1;
            display: flex;
            gap: 15px;
            overflow: hidden;
            min-height: 0;
        }

        .sorting-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .zoom-toolbar {
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            gap: 6px;
            z-index: 10;
            background: rgba(255,255,255,0.95);
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .zoom-btn {
            border: none;
            background: #2563eb;
            color: white;
            font-weight: 800;
            min-width: 32px;
            height: 30px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            padding: 0 8px;
        }

        .zoom-btn:hover {
            background: #1d4ed8;
        }

        .zoom-label {
            min-width: 52px;
            text-align: center;
            font-size: 12px;
            font-weight: 700;
            color: #334155;
            line-height: 30px;
        }

        .image-container {
            width: 100%;
            height: calc(100% - 60px);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: auto;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }

        #current-image {
            max-width: none;
            max-height: none;
            width: auto;
            height: auto;
            object-fit: contain;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform-origin: center center;
            transition: transform 0.12s ease-out;
        }

        .metadata-info {
            text-align: center;
            margin-top: 10px;
            flex-shrink: 0;
        }

        .filename-text {
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            word-break: break-all;
        }

        .count-text {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }

        .sidebar-controls {
            width: 230px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow-y: auto;
            flex-shrink: 0;
        }

        .panel-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
        }

        .panel-card h3 {
            font-size: 12px;
            color: #475569;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 4px;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .badge-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 6px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 4px;
        }

        .badge-left {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .key-cap {
            background-color: #0f172a;
            color: white;
            font-weight: 700;
            width: 18px;
            height: 18px;
            text-align: center;
            line-height: 18px;
            border-radius: 3px;
            font-size: 10px;
        }

        .badge-count {
            background-color: #e2e8f0;
            color: #475569;
            padding: 1px 6px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 600;
        }

        .badge-count.has-items {
            background-color: #dcfce7;
            color: #16a34a;
        }

        .btn {
            border: none;
            width: 100%;
            padding: 10px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-upload-main {
            background-color: #2563eb;
            color: white;
            margin-bottom: 4px;
        }

        .btn-upload-main:hover {
            background-color: #1d4ed8;
        }

        .btn-upload-guide {
            background-color: #64748b;
            color: white;
            margin-top: 8px;
            margin-bottom: 4px;
        }

        .btn-upload-guide:hover {
            background-color: #475569;
        }

        .btn-undo {
            background-color: #f59e0b;
            color: white;
        }

        .btn-undo:hover:not(:disabled) {
            background-color: #d97706;
        }

        .btn-download {
            background-color: #16a34a;
            color: white;
            margin-top: 6px;
        }

        .btn-download:hover:not(:disabled) {
            background-color: #15803d;
        }

        .btn-reset {
            background-color: #ef4444;
            color: white;
            margin-top: 6px;
        }

        .btn-reset:hover {
            background-color: #dc2626;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .placeholder-msg {
            color: #94a3b8;
            font-size: 14px;
            text-align: center;
            padding: 20px;
            line-height: 1.6;
        }

        #toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #0f172a;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 13px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
            pointer-events: none;
        }

        #toast.visible {
            opacity: 1;
        }

        #toast.error {
            background-color: #dc2626;
        }

        #lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15,23,42,0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            cursor: zoom-out;
        }

        #lightbox img {
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
        }

        @media (max-width: 1000px) {
            #left-panel {
                width: 360px;
                min-width: 300px;
            }

            .sidebar-controls {
                width: 200px;
            }

            .cue-table {
                font-size: 11px;
            }
        }

        @media (max-width: 850px) {
            body {
                flex-direction: column;
            }

            #left-panel {
                width: 100%;
                height: auto;
                max-height: 35vh;
            }

            #right-panel {
                height: 65vh;
            }

            .sidebar-controls {
                width: 180px;
            }
        }
    </style>
</head>

<body>
    <div id="lightbox" onclick="this.style.display='none'">
        <img id="lightbox-target" src="" alt="Preview">
    </div>

    <div id="left-panel">
        <h1>🔬 Parasite Image Sorter</h1>

        <div id="left-default-guide" style="{% if guide_type or doc_elements %}display:none;{% endif %}">
            <div class="left-guide-card">
                <div class="top-panel-title">Visual Guide</div>

                {% if visual_guide.exists and visual_guide.type == 'image' %}
                    <img class="builtin-guide-img left-builtin-guide-img" src="{{ visual_guide.url }}" onclick="triggerZoom('{{ visual_guide.url }}')" alt="Visual Guide">
                {% elif visual_guide.exists and visual_guide.type == 'pdf' %}
                    <iframe class="left-builtin-guide-pdf" src="{{ visual_guide.url }}"></iframe>
                {% else %}
                    <div class="placeholder-msg" style="font-size:12px;">
                        Add your visual guide file to GitHub and set
                        <br><b>TOP_VISUAL_GUIDE_FILE</b>
                        <br>near the top of app.py.
                    </div>
                {% endif %}
            </div>

            <div class="left-guide-card">
                <div class="top-panel-title">ER / MR / LR Cue Table</div>

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
                            <td>≤ 0.5</td>
                            <td>0.5–1.0</td>
                            <td>≥ 1.0</td>
                        </tr>
                        <tr>
                            <td>Appliqué/accolé position</td>
                            <td>+++</td>
                            <td>+</td>
                            <td>–</td>
                        </tr>
                        <tr>
                            <td>Headphone double-dot chromatin</td>
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
                            <td>Well-formed circular ring</td>
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
                            <td>Maurer’s clefts</td>
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

            <div class="left-guide-card">
                <div class="top-panel-title">Quick Decision Flow</div>

                <ol class="decision-flow">
                    <li>
                        <b>Pigment granules or Maurer’s clefts?</b>
                        <span>→ MR or LR</span>
                    </li>
                    <li>
                        <b>Cytoplasm band ≥ nucleus diameter?</b>
                        <span>→ LR</span>
                    </li>
                    <li>
                        <b>Cytoplasm band &gt; ½ nucleus diameter?</b>
                        <span>→ MR</span>
                    </li>
                    <li>
                        <b>Cytoplasm minimal, chromatin-dominant, comma/crescent, appliqué, or double-dot?</b>
                        <span>→ ER</span>
                    </li>
                </ol>
            </div>
        </div>

        <div id="docx-content" style="{% if not guide_type and not doc_elements %}display:none;{% endif %}">
            {% if guide_type == 'pdf' %}
                <iframe class="pdf-guide-frame" src="/serve_reference_pdf"></iframe>
            {% elif doc_elements %}
                {% for element in doc_elements %}
                    {% if element.is_heading %}
                        <div class="doc-heading">{{ element.text }}</div>
                    {% elif element.text %}
                        <div class="doc-paragraph">{{ element.text }}</div>
                    {% endif %}

                    {% if element.images %}
                        <div class="doc-images-container">
                            {% for img in element.images %}
                                <img class="doc-reference-img" src="{{ img }}" onclick="triggerZoom('{{ img }}')">
                            {% endfor %}
                        </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
        </div>
    </div>

    <div id="right-panel">
        <div class="stats-bar">
            <div class="stat-item">
                <div>
                    <div class="stat-label">Remaining</div>
                    <div class="stat-value highlight" id="remaining-count">0</div>
                </div>
            </div>

            <div class="stat-item">
                <div>
                    <div class="stat-label">Sorted</div>
                    <div class="stat-value" id="sorted-count">0</div>
                </div>
            </div>

            <div class="stat-item">
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
                    </div>
                    <div class="progress-text" id="progress-text">0%</div>
                </div>
            </div>
        </div>

        <div class="workspace-content">
            <div class="main-workspace-row">
                <div class="sorting-area" id="sorting-viewport">
                    <div class="placeholder-msg">👆 Upload a ZIP file to begin sorting images</div>
                </div>

                <div class="sidebar-controls">
                    <div class="panel-card">
                        <h3>Hotkeys 1-9</h3>

                        <div class="badge-item"><div class="badge-left"><span class="key-cap">1</span> ER</div><span class="badge-count" id="count-1">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">2</span> MR</div><span class="badge-count" id="count-2">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">3</span> LR</div><span class="badge-count" id="count-3">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">4</span> Troph</div><span class="badge-count" id="count-4">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">5</span> Schizont</div><span class="badge-count" id="count-5">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">6</span> Gameto</div><span class="badge-count" id="count-6">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">7</span> Merozoite</div><span class="badge-count" id="count-7">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">8</span> Indeterm</div><span class="badge-count" id="count-8">0</span></div>
                        <div class="badge-item"><div class="badge-left"><span class="key-cap">9</span> Uninfect</div><span class="badge-count" id="count-9">0</span></div>
                    </div>

                    <div class="panel-card">
                        <h3>Upload</h3>

                        <input type="file" id="images-input" accept=".zip">
                        <button class="btn btn-upload-main" onclick="document.getElementById('images-input').click()">
                            📦 Upload Images ZIP
                        </button>
                        <div class="upload-status compact-status" id="images-status"></div>

                        <input type="file" id="docx-input" accept=".docx,.pdf">
                        <button class="btn btn-upload-guide" onclick="document.getElementById('docx-input').click()">
                            📄 Upload Guide DOCX/PDF
                        </button>
                        <div class="upload-status compact-status" id="docx-status"></div>
                    </div>

                    <div class="panel-card">
                        <h3>Actions</h3>
                        <button id="undo-btn" class="btn btn-undo" onclick="executeUndo()" disabled>↩️ Undo Z</button>
                        <button id="download-btn" class="btn btn-download" onclick="downloadSorted()" disabled>📥 Download</button>
                        <button class="btn btn-reset" onclick="resetSession()">🔄 Reset</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="toast"></div>

    <script>
        const CLASS_MAP = {
            '1': '1-ER',
            '2': '2-MR',
            '3': '3-LR',
            '4': '4-Troph',
            '5': '5-Schizont',
            '6': '6-Gametocyte',
            '7': '7-Merozoite',
            '8': '8-Indeterminate',
            '9': '9-Uninfected'
        };

        let state = {
            upload_complete: false,
            current_image: null,
            remaining_count: 0,
            history_count: 0,
            sorted_counts: {},
            total_sorted: 0
        };

        let imageZoom = 1.25;

        const showToast = (msg, err=false) => {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = err ? 'error visible' : 'visible';
            setTimeout(() => t.className = '', 2500);
        };

        const triggerZoom = src => {
            document.getElementById('lightbox-target').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        };

        function setImageZoom(newZoom) {
            imageZoom = Math.max(0.25, Math.min(5, newZoom));

            const img = document.getElementById('current-image');
            const label = document.getElementById('zoom-label');

            if (img) {
                img.style.transform = `scale(${imageZoom})`;
            }

            if (label) {
                label.textContent = Math.round(imageZoom * 100) + '%';
            }
        }

        function zoomIn() {
            setImageZoom(imageZoom + 0.25);
        }

        function zoomOut() {
            setImageZoom(imageZoom - 0.25);
        }

        function resetZoom() {
            setImageZoom(1.25);
        }

        function fitZoom() {
            setImageZoom(1);
        }

        function updateUI() {
            document.getElementById('remaining-count').textContent = state.remaining_count;
            document.getElementById('sorted-count').textContent = state.total_sorted;

            const total = state.remaining_count + state.total_sorted;
            const pct = total > 0 ? Math.round((state.total_sorted / total) * 100) : 0;

            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-text').textContent = pct + '%';

            for (let k in CLASS_MAP) {
                const cnt = state.sorted_counts[CLASS_MAP[k]] || 0;
                const el = document.getElementById('count-' + k);

                if (el) {
                    el.textContent = cnt;
                    el.className = cnt > 0 ? 'badge-count has-items' : 'badge-count';
                }
            }

            const vp = document.getElementById('sorting-viewport');

            if (!state.upload_complete) {
                vp.innerHTML = '<div class="placeholder-msg">👆 Upload a ZIP file to begin</div>';
            } else if (state.current_image) {
                vp.innerHTML = `
                    <div class="zoom-toolbar">
                        <button class="zoom-btn" onclick="zoomOut()" title="Zoom out">−</button>
                        <div class="zoom-label" id="zoom-label">${Math.round(imageZoom * 100)}%</div>
                        <button class="zoom-btn" onclick="zoomIn()" title="Zoom in">+</button>
                        <button class="zoom-btn" onclick="resetZoom()" title="Reset zoom">↺</button>
                        <button class="zoom-btn" onclick="fitZoom()" title="Fit">Fit</button>
                    </div>

                    <div class="image-container">
                        <img
                            id="current-image"
                            src="/serve_active_image/${encodeURIComponent(state.current_image)}?t=${Date.now()}"
                            onload="setImageZoom(imageZoom)"
                            ondblclick="triggerZoom(this.src)"
                            alt="Current parasite image"
                        >
                    </div>

                    <div class="metadata-info">
                        <div class="filename-text">${escapeHtml(state.current_image)}</div>
                        <div class="count-text">Press 1-9 to classify. Use +/− or mouse wheel with Ctrl/Shift to zoom. Double-click image for full preview.</div>
                    </div>
                `;
            } else {
                vp.innerHTML = '<div class="placeholder-msg">🎉 Done! Click Download to get results.</div>';
            }

            document.getElementById('undo-btn').disabled = state.history_count === 0;
            document.getElementById('download-btn').disabled = state.total_sorted === 0;
        }

        async function fetchState() {
            try {
                state = await (await fetch('/state')).json();
                updateUI();
            } catch(e) {
                console.error(e);
            }
        }

        document.getElementById('images-input').addEventListener('change', async function(e) {
            const file = e.target.files[0];

            if (!file) return;

            const status = document.getElementById('images-status');
            status.textContent = 'Uploading...';
            status.className = 'upload-status compact-status';

            const fd = new FormData();
            fd.append('images_zip', file);

            try {
                const res = await fetch('/upload_images', {
                    method: 'POST',
                    body: fd
                });

                const data = await res.json();

                status.textContent = data.message;
                status.className = 'upload-status compact-status ' + (data.success ? 'success' : 'error');

                if (data.success) {
                    showToast(data.message);
                    imageZoom = 1.25;
                    await fetchState();
                }
            } catch(e) {
                status.textContent = 'Failed';
                status.className = 'upload-status compact-status error';
            }

            e.target.value = '';
        });

        document.getElementById('docx-input').addEventListener('change', async function(e) {
            const file = e.target.files[0];

            if (!file) return;

            const status = document.getElementById('docx-status');
            status.textContent = 'Uploading...';
            status.className = 'upload-status compact-status';

            const fd = new FormData();
            fd.append('docx_file', file);

            try {
                const res = await fetch('/upload_docx', {
                    method: 'POST',
                    body: fd
                });

                const data = await res.json();

                status.textContent = data.success ? data.message : data.message;
                status.className = 'upload-status compact-status ' + (data.success ? 'success' : 'error');

                if (data.success) {
                    document.getElementById('left-default-guide').style.display = 'none';
                    document.getElementById('docx-content').style.display = 'block';

                    if (data.guide_type === 'pdf') {
                        renderPdfGuide();
                    } else {
                        const content = await (await fetch('/get_docx_content')).json();

                        if (content.content?.length) {
                            renderDocx(content.content);
                        } else {
                            document.getElementById('docx-content').innerHTML = '<div class="placeholder-msg">DOCX uploaded, but no readable content was found.</div>';
                        }
                    }
                }
            } catch(e) {
                status.textContent = 'Failed';
                status.className = 'upload-status compact-status error';
            }

            e.target.value = '';
        });

        function renderPdfGuide() {
            document.getElementById('left-default-guide').style.display = 'none';
            document.getElementById('docx-content').style.display = 'block';

            document.getElementById('docx-content').innerHTML = `
                <iframe class="pdf-guide-frame" src="/serve_reference_pdf?t=${Date.now()}"></iframe>
            `;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        function renderDocx(elements) {
            document.getElementById('left-default-guide').style.display = 'none';
            document.getElementById('docx-content').style.display = 'block';

            let html = '';

            for (const el of elements) {
                if (el.is_heading) {
                    html += `<div class="doc-heading">${escapeHtml(el.text)}</div>`;
                } else if (el.text) {
                    html += `<div class="doc-paragraph">${escapeHtml(el.text)}</div>`;
                }

                if (el.images?.length) {
                    html += '<div class="doc-images-container">';

                    for (const img of el.images) {
                        html += `<img class="doc-reference-img" src="${img}" onclick="triggerZoom('${img}')">`;
                    }

                    html += '</div>';
                }
            }

            document.getElementById('docx-content').innerHTML = html || '<div class="placeholder-msg">No content</div>';
        }

        async function classify(key) {
            if (!state.upload_complete || !state.current_image) return;

            try {
                const res = await fetch('/classify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key})
                });

                const data = await res.json();

                if (data.success) {
                    showToast(data.message);

                    Object.assign(state, {
                        current_image: data.current_image,
                        remaining_count: data.remaining_count,
                        history_count: data.history_count,
                        sorted_counts: data.sorted_counts,
                        total_sorted: data.total_sorted
                    });

                    updateUI();
                } else {
                    showToast(data.message, true);
                }
            } catch(e) {
                showToast('Error', true);
            }
        }

        async function executeUndo() {
            if (state.history_count === 0) return;

            try {
                const res = await fetch('/undo', {
                    method: 'POST'
                });

                const data = await res.json();

                if (data.success) {
                    showToast(data.message);

                    Object.assign(state, {
                        current_image: data.current_image,
                        remaining_count: data.remaining_count,
                        history_count: data.history_count,
                        sorted_counts: data.sorted_counts,
                        total_sorted: data.total_sorted
                    });

                    updateUI();
                } else {
                    showToast(data.message, true);
                }
            } catch(e) {
                showToast('Error', true);
            }
        }

        function downloadSorted() {
            if (state.total_sorted > 0) {
                window.location.href = '/download_sorted';
            }
        }

        async function resetSession() {
            if (!confirm('Reset all data?')) return;

            try {
                const res = await fetch('/reset_session', {
                    method: 'POST'
                });

                if ((await res.json()).success) {
                    document.getElementById('images-status').textContent = '';
                    document.getElementById('docx-status').textContent = '';

                    document.getElementById('docx-content').innerHTML = '';
                    document.getElementById('docx-content').style.display = 'none';
                    document.getElementById('left-default-guide').style.display = 'block';

                    imageZoom = 1.25;
                    await fetchState();
                }
            } catch(e) {
                showToast('Error', true);
            }
        }

        document.addEventListener('keydown', e => {
            if (e.ctrlKey || e.metaKey || e.altKey) return;
            if (e.target.tagName === 'INPUT') return;

            if (e.key >= '1' && e.key <= '9') {
                e.preventDefault();
                classify(e.key);
            } else if (e.key.toLowerCase() === 'z' || e.key === 'Backspace') {
                e.preventDefault();
                executeUndo();
            } else if (e.key === '+' || e.key === '=') {
                e.preventDefault();
                zoomIn();
            } else if (e.key === '-' || e.key === '_') {
                e.preventDefault();
                zoomOut();
            } else if (e.key.toLowerCase() === 'r') {
                e.preventDefault();
                resetZoom();
            }
        });

        document.addEventListener('wheel', e => {
            const img = document.getElementById('current-image');

            if (!img) return;

            const container = document.querySelector('.image-container');

            if (!container || !container.contains(e.target)) return;

            if (e.ctrlKey || e.metaKey || e.shiftKey) {
                e.preventDefault();

                if (e.deltaY < 0) {
                    zoomIn();
                } else {
                    zoomOut();
                }
            }
        }, { passive: false });

        window.onload = fetchState;
    </script>
</body>
</html>
"""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)