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

# Default zoom level. The image fills the viewer at 1.0 (fit-to-display); this is a
# multiplier on top of that. Tune this knob to taste — lower = smaller start.
DEFAULT_ZOOM = 2

# Class mapping - keys are keyboard inputs, values are class names (and folder names).
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

NAME_TO_KEY = {v: k for k, v in CLASS_MAPPING.items()}

# Image quality — also the subfolder each classified image lands in.
STATUSES = ('Usable', 'Limited', 'Unusable')

# Uninfected: one keypress classifies it Usable, skipping the alternative and status steps.
AUTO_ADVANCE_CLASSES = ['0']

# Cannot Determine: skip the alternative step, still prompt for Usable/Limited/Unusable.
SKIP_ALTERNATIVE_CLASSES = ['-']

# Never offered as somebody else's alternative — "Early Ring, or possibly Uninfected"
# is not a judgement anyone makes.
NOT_OFFERED_AS_ALTERNATIVE = ['0', '-']

# Adjacency mapping for first row (which keys are the expected alternative)
ADJACENCY_MAP = {
    '1': ['2'],           # Early Ring -> Middle Ring
    '2': ['1', '3'],      # Middle Ring -> Early Ring, Late Ring
    '3': ['2', '4'],      # Late Ring -> Middle Ring, Trophozoite
    '4': ['3', '5'],      # Trophozoite -> Late Ring, Schizont
    '5': ['4']            # Schizont -> Trophozoite
}

# The browser owns the 3-step selection flow, so it needs these same constants.
# Injected into the page as JSON — one source of truth, no hand-copied JS literals.
JS_CONFIG = {
    'classMap': CLASS_MAPPING,
    'adjacency': ADJACENCY_MAP,
    'autoAdvance': AUTO_ADVANCE_CLASSES,
    'skipAlternative': SKIP_ALTERNATIVE_CLASSES,
    'notOfferedAsAlternative': NOT_OFFERED_AS_ALTERNATIVE,
    'defaultZoom': DEFAULT_ZOOM,
}
