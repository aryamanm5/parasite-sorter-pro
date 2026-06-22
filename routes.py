import os
import io
from flask import jsonify, request, send_file

from config import CLASS_MAPPING, AUTO_ADVANCE_CLASSES, TOP_VISUAL_GUIDE_FILE, DEFAULT_ZOOM
from session_manager import (
    get_session_data, 
    cleanup_old_sessions, 
    reset_current_selection,
    clear_session_data
)
from utils import get_images_list, get_sorted_counts, get_total_sorted, get_visual_guide_info
from file_handler import (
    extract_images_from_zip,
    classify_image,
    undo_classification,
    create_download_zip,
    create_progress_csv,
    load_progress_csv
)


def register_routes(app):
    """Register all routes with the Flask app."""

    @app.route('/')
    def index():
        from templates import get_html_template
        cleanup_old_sessions()
        get_session_data()  # Initialize session
        visual_guide = get_visual_guide_info()
        return get_html_template(visual_guide, DEFAULT_ZOOM)

    @app.route('/visual_guide')
    def visual_guide():
        if not TOP_VISUAL_GUIDE_FILE:
            return "No visual guide configured", 404

        full_path = os.path.abspath(TOP_VISUAL_GUIDE_FILE)

        if not os.path.exists(full_path):
            return "Visual guide not found", 404

        return send_file(full_path)

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

            session_data['history'] = []
            session_data['upload_complete'] = True
            reset_current_selection(session_data)

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
        images = get_images_list(session_data['unsorted_dir'])
        sorted_counts = get_sorted_counts(session_data['sorted_dir'])
        total_sorted = get_total_sorted(session_data['sorted_dir'])

        return jsonify({
            'upload_complete': session_data['upload_complete'],
            'current_image': images[0] if images else None,
            'remaining_count': len(images),
            'history_count': len(session_data['history']),
            'sorted_counts': sorted_counts,
            'total_sorted': total_sorted,
            'current_selection': session_data['current_selection'],
            'default_zoom': DEFAULT_ZOOM
        })

    @app.route('/serve_image/<path:filename>')
    def serve_image(filename):
        session_data = get_session_data()
        return send_file(os.path.join(session_data['unsorted_dir'], filename))

    @app.route('/select_label', methods=['POST'])
    def select_label():
        """Handle label selection (step 1)."""
        session_data = get_session_data()
        data = request.get_json()
        key = data.get('key')

        if not session_data['upload_complete']:
            return jsonify({'success': False, 'message': 'Upload dataset first'}), 400

        images = get_images_list(session_data['unsorted_dir'])
        if not images:
            return jsonify({'success': False, 'message': 'No images left'}), 400

        if key not in CLASS_MAPPING:
            return jsonify({'success': False, 'message': 'Invalid key'}), 400

        current = session_data['current_selection']

        # Check if this is an auto-advance class
        if key in AUTO_ADVANCE_CLASSES:
            # Auto-classify as Usable with no alternative, skip both steps
            success, message = classify_image(session_data, key, None, 'Usable')
            
            if success:
                reset_current_selection(session_data)
                images = get_images_list(session_data['unsorted_dir'])
                sorted_counts = get_sorted_counts(session_data['sorted_dir'])
                total_sorted = get_total_sorted(session_data['sorted_dir'])

                return jsonify({
                    'success': True,
                    'auto_advanced': True,
                    'message': message,
                    'current_image': images[0] if images else None,
                    'remaining_count': len(images),
                    'history_count': len(session_data['history']),
                    'sorted_counts': sorted_counts,
                    'total_sorted': total_sorted,
                    'current_selection': session_data['current_selection']
                })
            else:
                return jsonify({'success': False, 'message': message}), 500

        # Set label and move to alternative step
        current['label'] = key
        current['step'] = 'alternative'

        return jsonify({
            'success': True,
            'selection': current,
            'step': 'alternative'
        })

    @app.route('/select_alternative', methods=['POST'])
    def select_alternative():
        """Handle alternative selection (step 2)."""
        session_data = get_session_data()
        data = request.get_json()
        has_alternative = data.get('has_alternative')

        current = session_data['current_selection']

        if current['label'] is None:
            return jsonify({'success': False, 'message': 'No label selected'}), 400

        if current['step'] != 'alternative':
            return jsonify({'success': False, 'message': 'Invalid step'}), 400

        current['has_alternative'] = has_alternative
        current['step'] = 'status'

        return jsonify({
            'success': True,
            'selection': current,
            'step': 'status'
        })

    @app.route('/clear_selection', methods=['POST'])
    def clear_selection():
        """Clear current label selection."""
        session_data = get_session_data()
        reset_current_selection(session_data)
        
        return jsonify({
            'success': True,
            'selection': session_data['current_selection']
        })

    @app.route('/finalize', methods=['POST'])
    def finalize():
        """Finalize classification with status (step 3)."""
        session_data = get_session_data()
        data = request.get_json()
        status = data.get('status')

        if status not in ['Usable', 'Limited', 'Unusable']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400

        current = session_data['current_selection']
        
        if current['label'] is None:
            return jsonify({'success': False, 'message': 'No label selected'}), 400

        if current['step'] != 'status':
            return jsonify({'success': False, 'message': 'Complete alternative selection first'}), 400

        success, message = classify_image(
            session_data,
            current['label'],
            current['has_alternative'],
            status
        )

        if success:
            reset_current_selection(session_data)
            
            images = get_images_list(session_data['unsorted_dir'])
            sorted_counts = get_sorted_counts(session_data['sorted_dir'])
            total_sorted = get_total_sorted(session_data['sorted_dir'])

            return jsonify({
                'success': True,
                'message': message,
                'current_image': images[0] if images else None,
                'remaining_count': len(images),
                'history_count': len(session_data['history']),
                'sorted_counts': sorted_counts,
                'total_sorted': total_sorted,
                'current_selection': session_data['current_selection']
            })

        return jsonify({'success': False, 'message': message}), 500

    @app.route('/undo', methods=['POST'])
    def undo():
        session_data = get_session_data()
        
        success, message = undo_classification(session_data)
        reset_current_selection(session_data)

        images = get_images_list(session_data['unsorted_dir'])
        sorted_counts = get_sorted_counts(session_data['sorted_dir'])
        total_sorted = get_total_sorted(session_data['sorted_dir'])

        return jsonify({
            'success': success,
            'message': message,
            'current_image': images[0] if images else None,
            'remaining_count': len(images),
            'history_count': len(session_data['history']),
            'sorted_counts': sorted_counts,
            'total_sorted': total_sorted,
            'current_selection': session_data['current_selection']
        })

    @app.route('/download', methods=['GET'])
    def download():
        session_data = get_session_data()
        total = get_total_sorted(session_data['sorted_dir'])

        if total == 0:
            return "No sorted images to download", 400

        try:
            zip_path = create_download_zip(session_data)
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name='sorted_dataset.zip'
            )
        except Exception as e:
            return f"Download error: {str(e)}", 500

    @app.route('/save_progress', methods=['GET'])
    def save_progress():
        session_data = get_session_data()

        if not session_data['history']:
            return "No progress to save", 400

        try:
            csv_content = create_progress_csv(session_data)
            csv_bytes = io.BytesIO(csv_content.encode('utf-8'))
            csv_bytes.seek(0)

            return send_file(
                csv_bytes,
                mimetype='text/csv',
                as_attachment=True,
                download_name='classification_progress.csv'
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

        success, message, count = load_progress_csv(session_data, file)

        if success:
            images = get_images_list(session_data['unsorted_dir'])
            sorted_counts = get_sorted_counts(session_data['sorted_dir'])
            total_sorted = get_total_sorted(session_data['sorted_dir'])

            return jsonify({
                'success': True,
                'message': message,
                'current_image': images[0] if images else None,
                'remaining_count': len(images),
                'history_count': len(session_data['history']),
                'sorted_counts': sorted_counts,
                'total_sorted': total_sorted
            })

        return jsonify({'success': False, 'message': message}), 400

    @app.route('/reset', methods=['POST'])
    def reset():
        session_data = get_session_data()
        
        if clear_session_data(session_data):
            return jsonify({'success': True, 'message': 'Session reset'})
        
        return jsonify({'success': False, 'message': 'Reset failed'}), 500

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})