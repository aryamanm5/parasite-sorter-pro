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
TOP_VISUAL_GUIDE_FILE = "parasite-sorter-pro/visual_guide.png"

# Class mapping - keys are keyboard inputs, values are class names
CLASS_MAPPING = {
    '1': 'Early Ring',
    '2': 'Middle Ring',
    '3': 'Late Ring',
    '4': 'Trophozoite',
    '5': 'Schizont',
    '6': 'Gametocyte',
    '7': 'Merozoite',
    '8': 'Other Artifact',
    '9': 'Platelet',
    '0': 'Uninfected',
    '-': 'Cannot Determine'
}

# First row classes (ordered asexual stages) - can have two labels
FIRST_ROW_CLASSES = ['1', '2', '3', '4', '5']

# Second row classes - single label only
SECOND_ROW_CLASSES = ['6', '7', '8', '9', '0', '-']

# Auto-advance classes - these skip status selection and auto-classify as "Usable"
AUTO_ADVANCE_CLASSES = ['0', '-']  # Uninfected, Cannot Determine

# Adjacency mapping for first row (which keys can be selected as second label)
ADJACENCY_MAP = {
    '1': ['2'],           # Early Ring -> Middle Ring
    '2': ['1', '3'],      # Middle Ring -> Early Ring, Late Ring
    '3': ['2', '4'],      # Late Ring -> Middle Ring, Trophozoite
    '4': ['3', '5'],      # Trophozoite -> Late Ring, Schizont
    '5': ['4']            # Schizont -> Trophozoite
}

# Status options
STATUS_OPTIONS = {
    'Enter': 'Usable',
    "'": 'Limited',
    'Shift': 'Unusable'
}

# Subfolders for each class
STATUS_SUBFOLDERS = ['Usable', 'Limited', 'Unusable', 'Second_Choice']