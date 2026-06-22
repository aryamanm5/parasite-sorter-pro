import os
import zipfile
import shutil
import csv
import io
from werkzeug.utils import secure_filename

from config import CLASS_MAPPING, STATUS_SUBFOLDERS
from utils import allowed_file, get_images_list, get_unique_filename, get_sorted_counts


def extract_images_from_zip(zip_file, unsorted_dir, session_dir):
    """Extract images from uploaded ZIP file."""
    # Clear existing unsorted images
    shutil.rmtree(unsorted_dir, ignore_errors=True)
    os.makedirs(unsorted_dir, exist_ok=True)

    zip_path = os.path.join(session_dir, 'upload.zip')
    zip_file.save(zip_path)

    extracted_count = 0

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Skip directories and system files
            if member.endswith('/') or member.startswith('__MACOSX') or '/.' in member:
                continue

            filename = os.path.basename(member)

            if filename and allowed_file(filename):
                source = zip_ref.open(member)
                safe_name = secure_filename(filename)
                target_path = os.path.join(unsorted_dir, safe_name)

                # Handle duplicates
                if os.path.exists(target_path):
                    safe_name = get_unique_filename(unsorted_dir, safe_name)
                    target_path = os.path.join(unsorted_dir, safe_name)

                with open(target_path, 'wb') as f:
                    f.write(source.read())
                
                extracted_count += 1

    os.remove(zip_path)
    return extracted_count


def classify_image(session_data, label, has_alternative, status):
    """
    Classify current image with label, alternative flag, and status.
    Returns success status and message.
    """
    images = get_images_list(session_data['unsorted_dir'])
    
    if not images:
        return False, 'No images left to classify'

    img_name = images[0]
    src_path = os.path.join(session_data['unsorted_dir'], img_name)
    
    # Get class name from label
    class_name = CLASS_MAPPING.get(label)
    if not class_name:
        return False, 'Invalid label'

    # Destination
    dest_dir = os.path.join(session_data['sorted_dir'], class_name, status)
    dest_filename = get_unique_filename(dest_dir, img_name)
    dest_path = os.path.join(dest_dir, dest_filename)

    try:
        # Move to destination
        shutil.move(src_path, dest_path)

        # Record in history
        session_data['history'].append({
            'original_filename': img_name,
            'dest_filename': dest_filename,
            'class_name': class_name,
            'status': status,
            'has_alternative': has_alternative,
            'src_dir': session_data['unsorted_dir']
        })

        return True, f'Classified as {class_name}'

    except Exception as e:
        return False, f'Error classifying: {str(e)}'


def undo_classification(session_data):
    """Undo the last classification."""
    if not session_data['history']:
        return False, 'Nothing to undo'

    entry = session_data['history'].pop()

    try:
        # Restore from destination
        src_path = os.path.join(
            session_data['sorted_dir'],
            entry['class_name'],
            entry['status'],
            entry['dest_filename']
        )
        
        restore_path = os.path.join(
            entry['src_dir'], 
            get_unique_filename(entry['src_dir'], entry['original_filename'])
        )

        if os.path.exists(src_path):
            shutil.move(src_path, restore_path)

        return True, 'Undo successful'

    except Exception as e:
        return False, f'Undo error: {str(e)}'


def create_download_zip(session_data):
    """Create ZIP file of sorted images with CSV."""
    sorted_dir = session_data['sorted_dir']
    zip_path = os.path.join(session_data['session_dir'], 'sorted_images.zip')

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add sorted images
        for class_name in CLASS_MAPPING.values():
            class_dir = os.path.join(sorted_dir, class_name)

            if os.path.exists(class_dir):
                for status in STATUS_SUBFOLDERS:
                    status_dir = os.path.join(class_dir, status)
                    
                    if os.path.exists(status_dir):
                        for img_file in os.listdir(status_dir):
                            if allowed_file(img_file):
                                file_path = os.path.join(status_dir, img_file)
                                arcname = os.path.join(class_name, status, img_file)
                                zipf.write(file_path, arcname)

        # Add CSV to root
        csv_content = create_progress_csv(session_data)
        zipf.writestr('classifications.csv', csv_content)

    return zip_path


def create_progress_csv(session_data):
    """Create CSV content from history."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output, 
        fieldnames=['filename', 'label', 'has_alternative', 'status']
    )
    writer.writeheader()

    for entry in session_data['history']:
        writer.writerow({
            'filename': entry['original_filename'],
            'label': entry['class_name'],
            'has_alternative': str(entry.get('has_alternative', '')).lower() if entry.get('has_alternative') is not None else '',
            'status': entry['status']
        })

    return output.getvalue()


def load_progress_csv(session_data, csv_file):
    """Load progress from CSV file."""
    try:
        csv_text = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(csv_text))

        required_fields = ['filename', 'label', 'status']
        if not reader.fieldnames or not all(f in reader.fieldnames for f in required_fields):
            return False, 'CSV must include filename, label, and status columns', 0

        # Create reverse mapping
        name_to_key = {v: k for k, v in CLASS_MAPPING.items()}

        applied = 0
        errors = []

        for row_index, row in enumerate(reader, start=2):
            filename = os.path.basename((row.get('filename') or '').strip())
            label = (row.get('label') or '').strip()
            has_alt_str = (row.get('has_alternative') or '').strip().lower()
            status = (row.get('status') or '').strip()

            if not filename or not label or status not in ['Usable', 'Limited', 'Unusable']:
                errors.append(f"Row {row_index}: invalid data")
                continue

            # Parse has_alternative
            has_alternative = None
            if has_alt_str == 'true':
                has_alternative = True
            elif has_alt_str == 'false':
                has_alternative = False

            # Get key from class name
            label_key = name_to_key.get(label)

            if not label_key:
                errors.append(f"Row {row_index}: unknown class '{label}'")
                continue

            src_path = os.path.join(session_data['unsorted_dir'], filename)
            
            if not os.path.exists(src_path):
                continue  # Skip if file not found

            # Classify the image
            success, msg = classify_image(session_data, label_key, has_alternative, status)
            
            if success:
                applied += 1

        return True, f'Restored {applied} classifications', applied

    except Exception as e:
        return False, f'Error loading progress: {str(e)}', 0