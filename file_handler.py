import os
import zipfile
import shutil
import csv
import io
from werkzeug.utils import secure_filename

from config import CLASS_MAPPING, NAME_TO_KEY, ADJACENCY_MAP, STATUSES
from utils import allowed_file, get_images_list, get_unique_filename, float_or_none

# Flagged images are renamed with this prefix so they sort to the back of the
# unsorted set (the app always classifies get_images_list()[0]). '~' sorts after
# all letters/digits. ponytail: reuse the alphabetical ordering, no extra queue state.
FLAG_PREFIX = '~flag~'


def strip_flag(name):
    """Recover the original filename from a flagged (renamed) file."""
    if name.startswith(FLAG_PREFIX):
        return name.split('~', 3)[-1]  # ['', 'flag', '<counter>', '<original>']
    return name


def current_image(session_data):
    """The image at the front of the unsorted queue, or None."""
    images = get_images_list(session_data['unsorted_dir'])
    return images[0] if images else None


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
                safe_name = get_unique_filename(unsorted_dir, secure_filename(filename))

                with zip_ref.open(member) as source, \
                        open(os.path.join(unsorted_dir, safe_name), 'wb') as target:
                    shutil.copyfileobj(source, target)

                extracted_count += 1

    os.remove(zip_path)
    return extracted_count


def is_adjacent(first_key, second_key):
    """Check if two keys are adjacent in the classification sequence."""
    if first_key is None or second_key is None:
        return False
    return second_key in ADJACENCY_MAP.get(first_key, [])


def _copy_into(src_path, sorted_dir, class_name, status, filename):
    """Copy src into <sorted>/<class>/<status>/, making it on demand. Returns the name used."""
    dest_dir = os.path.join(sorted_dir, class_name, status)
    os.makedirs(dest_dir, exist_ok=True)

    name = get_unique_filename(dest_dir, filename)
    shutil.copy2(src_path, os.path.join(dest_dir, name))
    return name


def classify_image(session_data, img_name, first_label, second_label, status,
                   is_redo=False, time_spent=None):
    """File img_name under its class/status folder. Returns (success, message)."""
    src_path = os.path.join(session_data['unsorted_dir'], img_name)
    if not os.path.exists(src_path):
        return False, f'Image not found: {img_name}'

    first_class = CLASS_MAPPING.get(first_label)
    if not first_class:
        return False, 'Invalid first label'

    second_class = CLASS_MAPPING.get(second_label) if second_label else None
    original_name = strip_flag(img_name)  # store/output under the real name, not the flag alias

    # A fresh classification invalidates the redo history.
    if not is_redo:
        session_data['redo_stack'] = []

    try:
        sorted_dir = session_data['sorted_dir']
        primary_filename = _copy_into(src_path, sorted_dir, first_class, status, original_name)
        second_filename = (
            _copy_into(src_path, sorted_dir, second_class, 'Second_Choice', original_name)
            if second_class else None
        )

        os.remove(src_path)

        session_data['history'].append({
            'original_filename': original_name,
            'primary_filename': primary_filename,
            'primary_class': first_class,
            'primary_status': status,
            'second_class': second_class,
            'second_filename': second_filename,
            'time_spent': time_spent,
        })

        return True, f'Classified as {first_class}'

    except Exception as e:
        return False, f'Error classifying: {str(e)}'


def undo_classification(session_data):
    """Undo the last classification."""
    if not session_data['history']:
        return False, 'Nothing to undo'

    entry = session_data['history'].pop()

    # Remember how to replay this classification if the user hits Redo.
    session_data['redo_stack'].append({
        'first_key': NAME_TO_KEY.get(entry['primary_class']),
        'second_key': NAME_TO_KEY.get(entry['second_class']),
        'status': entry['primary_status'],
        'time_spent': entry['time_spent'],
    })

    try:
        sorted_dir = session_data['sorted_dir']
        unsorted_dir = session_data['unsorted_dir']

        primary_path = os.path.join(
            sorted_dir, entry['primary_class'], entry['primary_status'], entry['primary_filename']
        )
        if os.path.exists(primary_path):
            restore_name = get_unique_filename(unsorted_dir, entry['original_filename'])
            shutil.move(primary_path, os.path.join(unsorted_dir, restore_name))

        # Drop the second-choice duplicate; it belongs to the classification we just undid.
        if entry['second_class']:
            second_path = os.path.join(
                sorted_dir, entry['second_class'], 'Second_Choice', entry['second_filename']
            )
            if os.path.exists(second_path):
                os.remove(second_path)

        return True, 'Undo successful'

    except Exception as e:
        return False, f'Undo error: {str(e)}'


def redo_classification(session_data):
    """Replay the most recently undone classification."""
    if not session_data['redo_stack']:
        return False, 'Nothing to redo'

    entry = session_data['redo_stack'].pop()
    img_name = current_image(session_data)

    if not entry['first_key'] or not img_name:
        return False, 'Cannot redo'

    return classify_image(
        session_data,
        img_name,
        entry['first_key'],
        entry['second_key'],
        entry['status'],
        is_redo=True,
        time_spent=entry['time_spent'],
    )


def flag_current_image(session_data):
    """Skip the current image and send it to the back of the unsorted set."""
    img_name = current_image(session_data)
    if not img_name:
        return False, 'No image to flag'

    session_data['flag_counter'] += 1
    new_name = f"{FLAG_PREFIX}{session_data['flag_counter']:06d}~{strip_flag(img_name)}"

    unsorted_dir = session_data['unsorted_dir']
    src = os.path.join(unsorted_dir, img_name)
    dst = os.path.join(unsorted_dir, get_unique_filename(unsorted_dir, new_name))

    try:
        os.rename(src, dst)
        session_data['redo_stack'] = []  # front image changed; redo no longer applies
        return True, 'Flagged — moved to the back'
    except Exception as e:
        return False, f'Flag error: {str(e)}'


def create_progress_csv(session_data):
    """CSV of the classification history.

    is_adjacent is derived here rather than stored — it is a pure function of the
    two labels, so threading it through classify/undo/redo was carrying a value we
    can always recompute. No alternative picked reads as 'Yes': there is nothing
    non-adjacent about a call with no second opinion.
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['filename', 'first_label', 'second_label', 'status', 'is_adjacent', 'time_spent_sec']
    )
    writer.writeheader()

    for entry in session_data['history']:
        second = entry['second_class']
        adjacent = not second or is_adjacent(
            NAME_TO_KEY.get(entry['primary_class']), NAME_TO_KEY.get(second)
        )
        time_spent = entry['time_spent']

        writer.writerow({
            'filename': entry['original_filename'],
            'first_label': entry['primary_class'],
            'second_label': second or '',
            'status': entry['primary_status'],
            'is_adjacent': 'Yes' if adjacent else 'No',
            'time_spent_sec': round(time_spent, 1) if time_spent else ''
        })

    return output.getvalue()


def load_progress_csv(session_data, csv_file):
    """Replay saved classifications onto the current unsorted set."""
    try:
        reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8-sig')))

        required_fields = ['filename', 'first_label', 'status']
        if not reader.fieldnames or not all(f in reader.fieldnames for f in required_fields):
            return False, 'CSV must include filename, first_label, and status columns', 0

        applied = 0

        for row in reader:
            filename = os.path.basename((row.get('filename') or '').strip())
            first_key = NAME_TO_KEY.get((row.get('first_label') or '').strip())
            second_key = NAME_TO_KEY.get((row.get('second_label') or '').strip())
            status = (row.get('status') or '').strip()
            time_spent = float_or_none(row.get('time_spent_sec') or row.get('time_spent'))

            if not filename or not first_key or status not in STATUSES:
                continue

            # Classify by name — rows may be missing or out of order, and the
            # unsorted queue must not be consumed front-to-back on faith.
            success, _ = classify_image(
                session_data, filename, first_key, second_key, status, time_spent=time_spent
            )
            if success:
                applied += 1

        return True, f'Restored {applied} classifications', applied

    except Exception as e:
        return False, f'Error loading progress: {str(e)}', 0
