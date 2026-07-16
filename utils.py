import os

from config import ALLOWED_IMAGE_EXTENSIONS, CLASS_MAPPING, STATUSES


def allowed_file(filename):
    """Check if file has allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_images_list(directory):
    """Sorted list of image files in directory; empty if it doesn't exist."""
    if not directory or not os.path.exists(directory):
        return []

    try:
        return sorted(f for f in os.listdir(directory) if allowed_file(f))
    except Exception:
        return []


def get_sorted_counts(sorted_dir):
    """How many images are classified under each class name.

    Second_Choice is excluded. It holds duplicate copies of images already counted
    under their primary label, so including it double-counts and makes "done"
    outrun "left". ponytail: real statuses only.
    """
    return {
        name: sum(len(get_images_list(os.path.join(sorted_dir, name, status))) for status in STATUSES)
        for name in CLASS_MAPPING.values()
    }


def get_unique_filename(directory, filename):
    """Generate unique filename if file already exists."""
    if not os.path.exists(os.path.join(directory, filename)):
        return filename

    base, ext = os.path.splitext(filename)
    counter = 1

    while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
        counter += 1

    return f"{base}_{counter}{ext}"


def float_or_none(value):
    """Coerce untrusted input to a float, or None if it isn't one."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
