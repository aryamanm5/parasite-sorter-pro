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

# Default zoom level. The image fills the viewer at 1.0 (fit-to-display); this is a
# multiplier on top of that. Tune this knob to taste — lower = smaller start.
DEFAULT_ZOOM = 2

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

# Auto-advance classes - these skip alternative and status selection, auto-classify as "Usable"
AUTO_ADVANCE_CLASSES = ['0']  # Uninfected

# No-alternative classes - skip the alternative step but still prompt for Usable/Limited/Unusable
NO_ALTERNATIVE_CLASSES = ['-']  # Cannot Determine

# Adjacency mapping for first row (which keys can be selected as alternative)
ADJACENCY_MAP = {
    '1': ['2'],           # Early Ring -> Middle Ring
    '2': ['1', '3'],      # Middle Ring -> Early Ring, Late Ring
    '3': ['2', '4'],      # Late Ring -> Middle Ring, Trophozoite
    '4': ['3', '5'],      # Trophozoite -> Late Ring, Schizont
    '5': ['4']            # Schizont -> Trophozoite
}

# Subfolders for each class
STATUS_SUBFOLDERS = ['Usable', 'Limited', 'Unusable', 'Second_Choice']