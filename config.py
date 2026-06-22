import os
import tempfile

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

# Visual guide file - set this to your guide image/pdf filename
TOP_VISUAL_GUIDE_FILE = "visual_guide.png"

# Class mapping - keys are keyboard inputs, values are class names
CLASS_MAPPING = {
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
}

# First row classes (ordered asexual stages)
FIRST_ROW_CLASSES = ['1', '2', '3', '4', '5']

# Second row classes
SECOND_ROW_CLASSES = ['6', '7', '8', '9', '0', '-']

# Auto-advance classes - these skip alternative and status selection, auto-classify as "Usable"
AUTO_ADVANCE_CLASSES = ['0', '-']  # Uninfected, Cannot Determine

# Status options
STATUS_OPTIONS = {
    'Enter': 'Usable',
    "'": 'Limited',
    'Shift': 'Unusable'
}

# Subfolders for each class
STATUS_SUBFOLDERS = ['Usable', 'Limited', 'Unusable']

# Default zoom level (4 = 400%)
DEFAULT_ZOOM = 4