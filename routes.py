import io
import os
from flask import jsonify, render_template, request, send_file, send_from_directory

from config import CLASS_MAPPING, JS_CONFIG, STATUSES
from session_manager import get_session_data, cleanup_old_sessions, reset_session
from utils import get_images_list, get_sorted_counts, float_or_none
from file_handler import (
    extract_images_from_zip,
    current_image,
    classify_image,
    undo_classification,
    redo_classification,
    flag_current_image,
    create_progress_csv,
    load_progress_csv,
)


def _state_payload(session_data):
    """Common state fields returned by every action that changes the queue."""
    images = get_images_list(session_data['unsorted_dir'])
    counts = get_sorted_counts(session_data['sorted_dir'])
    times = [e['time_spent'] for e in session_data['history'] if e['time_spent']]

    return {
        'current_image': images[0] if images else None,
        'remaining_count': len(images),
        'history_count': len(session_data['history']),
        'redo_count': len(session_data['redo_stack']),
        'sorted_counts': counts,
        'total_sorted': sum(counts.values()),
        'last_time': times[-1] if times else 0,
        'avg_time': sum(times) / len(times) if times else 0,
        'total_time': sum(times),
    }


def register_routes(app):
    """Register all routes with the Flask app."""

    @app.route('/')
    def index():
        cleanup_old_sessions()
        get_session_data()  # Initialize session
        return render_template('index.html', cfg=JS_CONFIG)

    @app.route('/upload_dataset', methods=['POST'])
    def upload_dataset():
        session_data = get_session_data()

        if 'dataset_zip' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400

        file = request.files['dataset_zip']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if not file.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'message': 'Please upload a ZIP file'}), 400

        try:
            count = extract_images_from_zip(
                file,
                session_data['unsorted_dir'],
                session_data['session_dir']
            )

            # Remember the dataset name to default the download/save filenames.
            session_data['dataset_name'] = os.path.splitext(os.path.basename(file.filename))[0]
            session_data['history'] = []
            session_data['redo_stack'] = []
            session_data['upload_complete'] = True

            return jsonify({
                'success': True,
                'message': f'Uploaded {count} images',
                'image_count': count
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'Upload error: {str(e)}'}), 500

    @app.route('/state', methods=['GET'])
    def get_state():
        session_data = get_session_data()
        return jsonify({
            'upload_complete': session_data['upload_complete'],
            **_state_payload(session_data)
        })

    @app.route('/serve_image/<filename>')
    def serve_image(filename):
        session_data = get_session_data()
        return send_from_directory(session_data['unsorted_dir'], filename)

    @app.route('/classify', methods=['POST'])
    def classify():
        """Classify the front image.

        The browser owns the class -> alternative -> status flow; this endpoint only
        ever sees the finished triple. Mirroring those steps server-side bought
        nothing but round-trips and a second copy of the class tables.
        """
        session_data = get_session_data()
        data = request.get_json(silent=True) or {}

        if not session_data['upload_complete']:
            return jsonify({'success': False, 'message': 'Upload dataset first'}), 400

        first = data.get('first')
        second = data.get('second')
        status = data.get('status')

        if first not in CLASS_MAPPING:
            return jsonify({'success': False, 'message': 'Invalid label'}), 400

        if second is not None and second not in CLASS_MAPPING:
            return jsonify({'success': False, 'message': 'Invalid alternative'}), 400

        if status not in STATUSES:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400

        img_name = current_image(session_data)
        if not img_name:
            return jsonify({'success': False, 'message': 'No images left'}), 400

        success, message = classify_image(
            session_data, img_name, first, second, status,
            time_spent=float_or_none(data.get('time_spent'))
        )

        if not success:
            return jsonify({'success': False, 'message': message}), 500

        return jsonify({'success': True, 'message': message, **_state_payload(session_data)})

    @app.route('/undo', methods=['POST'])
    def undo():
        session_data = get_session_data()
        success, message = undo_classification(session_data)

        return jsonify({'success': success, 'message': message, **_state_payload(session_data)})

    @app.route('/redo', methods=['POST'])
    def redo():
        session_data = get_session_data()
        success, message = redo_classification(session_data)

        return jsonify({'success': success, 'message': message, **_state_payload(session_data)})

    @app.route('/flag', methods=['POST'])
    def flag():
        session_data = get_session_data()
        success, message = flag_current_image(session_data)

        return jsonify({'success': success, 'message': message, **_state_payload(session_data)})

    @app.route('/save_progress', methods=['GET'])
    def save_progress():
        session_data = get_session_data()

        if not session_data['history']:
            return "No progress to save", 400

        try:
            csv_bytes = io.BytesIO(create_progress_csv(session_data).encode('utf-8'))
            name = session_data['dataset_name'] or 'classification'
            return send_file(
                csv_bytes,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{name}_progress.csv'
            )
        except Exception as e:
            return f"Error: {str(e)}", 500

    @app.route('/upload_progress', methods=['POST'])
    def upload_progress():
        session_data = get_session_data()

        if not session_data['upload_complete']:
            return jsonify({'success': False, 'message': 'Upload dataset first'}), 400

        if 'progress_csv' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400

        file = request.files['progress_csv']

        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'message': 'Please upload a CSV file'}), 400

        success, message, _ = load_progress_csv(session_data, file)

        if not success:
            return jsonify({'success': False, 'message': message}), 400

        return jsonify({'success': True, 'message': message, **_state_payload(session_data)})

    @app.route('/reset', methods=['POST'])
    def reset():
        reset_session()
        return jsonify({'success': True, 'message': 'Session reset'})

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
