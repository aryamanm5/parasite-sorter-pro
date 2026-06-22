import os
from config import ALLOWED_IMAGE_EXTENSIONS, CLASS_MAPPING, STATUS_SUBFOLDERS, TOP_VISUAL_GUIDE_FILE


def allowed_file(filename):
    """Check if file has allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_images_list(directory):
    """Get sorted list of image files in directory."""
    if not directory or not os.path.exists(directory):
        return []

    try:
        files = [f for f in os.listdir(directory) if allowed_file(f)]
        return sorted(files)
    except Exception:
        return []


def get_sorted_counts(sorted_dir):
    """Get count of images in each class/status combination."""
    counts = {}

    for class_name in CLASS_MAPPING.values():
        counts[class_name] = {
            'total': 0,
            'Usable': 0,
            'Limited': 0,
            'Unusable': 0
        }
        
        class_dir = os.path.join(sorted_dir, class_name)
        
        if os.path.exists(class_dir):
            for status in STATUS_SUBFOLDERS:
                status_dir = os.path.join(class_dir, status)
                if os.path.exists(status_dir):
                    count = len(get_images_list(status_dir))
                    counts[class_name][status] = count
                    counts[class_name]['total'] += count

    return counts


def get_total_sorted(sorted_dir):
    """Get total number of sorted images."""
    counts = get_sorted_counts(sorted_dir)
    return sum(c['total'] for c in counts.values())


def get_unique_filename(directory, filename):
    """Generate unique filename if file already exists."""
    if not os.path.exists(os.path.join(directory, filename)):
        return filename
    
    base, ext = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
        counter += 1
    
    return f"{base}_{counter}{ext}"


def get_progress_rows(sorted_dir):
    """Get all sorted images as rows for CSV export."""
    rows = []

    for class_key, class_name in CLASS_MAPPING.items():
        class_dir = os.path.join(sorted_dir, class_name)

        if not os.path.exists(class_dir):
            continue

        for status in ['Usable', 'Limited', 'Unusable']:
            status_dir = os.path.join(class_dir, status)
            
            if not os.path.exists(status_dir):
                continue

            for img_file in get_images_list(status_dir):
                rows.append({
                    'filename': img_file,
                    'label': class_name,
                    'has_alternative': '',
                    'status': status
                })

    return rows


def get_visual_guide_info():
    """Get information about the built-in visual guide."""
    if not TOP_VISUAL_GUIDE_FILE:
        return {'exists': False, 'url': None, 'type': None}

    full_path = os.path.abspath(TOP_VISUAL_GUIDE_FILE)

    if not os.path.exists(full_path):
        return {'exists': False, 'url': None, 'type': None}

    ext = os.path.splitext(full_path)[1].lower().replace('.', '')

    if ext == 'pdf':
        guide_type = 'pdf'
    elif ext in ALLOWED_IMAGE_EXTENSIONS:
        guide_type = 'image'
    else:
        guide_type = 'unsupported'

    return {
        'exists': guide_type in {'pdf', 'image'},
        'url': '/visual_guide',
        'type': guide_type
    }