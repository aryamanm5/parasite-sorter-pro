import os
import zipfile
import shutil
import csv
import io
from werkzeug.utils import secure_filename

from config import CLASS_MAPPING, STATUS_SUBFOLDERS, ADJACENCY_MAP
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


def is_adjacent(first_key, second_key):
    """Check if two keys are adjacent in the classification sequence."""
    if first_key is None or second_key is None:
        return False
    adjacent_keys = ADJACENCY_MAP.get(first_key, [])
    return second_key in adjacent_keys


def classify_image(session_data, first_label, second_label, status, is_adjacent_selection=True):
    """
    Classify current image with labels and status.
    Returns success status and message.
    """
    images = get_images_list(session_data['unsorted_dir'])
    
    if not images:
        return False, 'No images left to classify'

    img_name = images[0]
    src_path = os.path.join(session_data['unsorted_dir'], img_name)
    
    # Get class name from first label
    first_class = CLASS_MAPPING.get(first_label)
    if not first_class:
        return False, 'Invalid first label'

    # Primary destination
    primary_dir = os.path.join(session_data['sorted_dir'], first_class, status)
    primary_filename = get_unique_filename(primary_dir, img_name)
    primary_path = os.path.join(primary_dir, primary_filename)

    try:
        # Move to primary location
        shutil.copy2(src_path, primary_path)

        # If second label exists, copy to second choice folder
        second_class = None
        second_filename = None
        
        if second_label:
            second_class = CLASS_MAPPING.get(second_label)
            if second_class:
                second_dir = os.path.join(session_data['sorted_dir'], second_class, 'Second_Choice')
                second_filename = get_unique_filename(second_dir, img_name)
                second_path = os.path.join(second_dir, second_filename)
                shutil.copy2(src_path, second_path)

        # Remove original
        os.remove(src_path)

        # Record in history with adjacency flag
        session_data['history'].append({
            'original_filename': img_name,
            'primary_filename': primary_filename,
            'primary_class': first_class,
            'primary_status': status,
            'second_class': second_class,
            'second_filename': second_filename,
            'is_adjacent': is_adjacent_selection,
            'src_dir': session_data['unsorted_dir']
        })

        return True, f'Classified as {first_class}'

    except Exception as e:
        return False, f'Error classifying: {str(e)}'


def undo_classification(session_data):
    """Undo the last classification."""
    if not session_data['history']:
        return False, 'Nothing to undo'

    entry = session_data['history'].pop()

    try:
        # Restore from primary location
        primary_path = os.path.join(
            session_data['sorted_dir'],
            entry['primary_class'],
            entry['primary_status'],
            entry['primary_filename']
        )
        
        restore_path = os.path.join(
            entry['src_dir'], 
            get_unique_filename(entry['src_dir'], entry['original_filename'])
        )

        if os.path.exists(primary_path):
            shutil.move(primary_path, restore_path)

        # Remove second choice copy if exists
        if entry['second_class'] and entry['second_filename']:
            second_path = os.path.join(
                session_data['sorted_dir'],
                entry['second_class'],
                'Second_Choice',
                entry['second_filename']
            )
            if os.path.exists(second_path):
                os.remove(second_path)

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
    """Create CSV content from history with adjacency flag."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output, 
        fieldnames=['filename', 'first_label', 'second_label', 'status', 'is_adjacent']
    )
    writer.writeheader()

    for entry in session_data['history']:
        writer.writerow({
            'filename': entry['original_filename'],
            'first_label': entry['primary_class'],
            'second_label': entry.get('second_class', '') or '',
            'status': entry['primary_status'],
            'is_adjacent': 'Yes' if entry.get('is_adjacent', True) else 'No'
        })

    return output.getvalue()


def load_progress_csv(session_data, csv_file):
    """Load progress from CSV file."""
    try:
        csv_text = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(csv_text))

        required_fields = ['filename', 'first_label', 'status']
        if not reader.fieldnames or not all(f in reader.fieldnames for f in required_fields):
            return False, 'CSV must include filename, first_label, and status columns', 0

        # Create reverse mapping
        name_to_key = {v: k for k, v in CLASS_MAPPING.items()}

        applied = 0
        errors = []

        for row_index, row in enumerate(reader, start=2):
            filename = os.path.basename((row.get('filename') or '').strip())
            first_label = (row.get('first_label') or '').strip()
            second_label = (row.get('second_label') or '').strip()
            status = (row.get('status') or '').strip()
            is_adjacent_str = (row.get('is_adjacent') or 'Yes').strip()

            if not filename or not first_label or status not in ['Usable', 'Limited', 'Unusable']:
                errors.append(f"Row {row_index}: invalid data")
                continue

            # Get key from class name
            first_key = name_to_key.get(first_label)
            second_key = name_to_key.get(second_label) if second_label else None

            if not first_key:
                errors.append(f"Row {row_index}: unknown class '{first_label}'")
                continue

            src_path = os.path.join(session_data['unsorted_dir'], filename)
            
            if not os.path.exists(src_path):
                continue  # Skip if file not found

            # Determine adjacency
            is_adjacent_selection = is_adjacent_str.lower() == 'yes' if is_adjacent_str else True

            # Classify the image
            success, msg = classify_image(session_data, first_key, second_key, status, is_adjacent_selection)
            
            if success:
                applied += 1

        return True, f'Restored {applied} classifications', applied

    except Exception as e:
        return False, f'Error loading progress: {str(e)}', 0