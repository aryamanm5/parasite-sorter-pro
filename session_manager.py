import os
import uuid
import shutil
import threading
from datetime import datetime, timedelta
from flask import session

from config import (
    UPLOAD_FOLDER, 
    SESSION_TIMEOUT_HOURS, 
    CLASS_MAPPING,
    STATUS_SUBFOLDERS
)

# Store session data in memory
sessions_data = {}
sessions_lock = threading.Lock()


def get_session_id():
    """Get or create session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_session_data():
    """Get or create session data for current user."""
    session_id = get_session_id()

    with sessions_lock:
        if session_id not in sessions_data:
            session_dir = os.path.join(UPLOAD_FOLDER, session_id)
            os.makedirs(session_dir, exist_ok=True)

            sessions_data[session_id] = {
                'created': datetime.now(),
                'last_access': datetime.now(),
                'session_dir': session_dir,
                'unsorted_dir': os.path.join(session_dir, 'unsorted'),
                'sorted_dir': os.path.join(session_dir, 'sorted'),
                'history': [],
                'upload_complete': False,
                'current_selection': {
                    'first_label': None,
                    'second_label': None
                }
            }

            # Create directories
            os.makedirs(sessions_data[session_id]['unsorted_dir'], exist_ok=True)
            os.makedirs(sessions_data[session_id]['sorted_dir'], exist_ok=True)

            # Create class folders with status subfolders
            for class_name in CLASS_MAPPING.values():
                class_dir = os.path.join(sessions_data[session_id]['sorted_dir'], class_name)
                os.makedirs(class_dir, exist_ok=True)
                
                for subfolder in STATUS_SUBFOLDERS:
                    os.makedirs(os.path.join(class_dir, subfolder), exist_ok=True)

        sessions_data[session_id]['last_access'] = datetime.now()
        return sessions_data[session_id]


def cleanup_old_sessions():
    """Remove expired sessions."""
    cutoff = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)

    with sessions_lock:
        expired = [sid for sid, data in sessions_data.items() if data['last_access'] < cutoff]

        for sid in expired:
            try:
                shutil.rmtree(sessions_data[sid]['session_dir'], ignore_errors=True)
                del sessions_data[sid]
                print(f"Cleaned up session: {sid}")
            except Exception as e:
                print(f"Error cleaning session {sid}: {e}")


def reset_current_selection(session_data):
    """Reset the current image selection state."""
    session_data['current_selection'] = {
        'first_label': None,
        'second_label': None
    }


def clear_session_data(session_data):
    """Clear all session data for reset."""
    try:
        shutil.rmtree(session_data['unsorted_dir'], ignore_errors=True)
        shutil.rmtree(session_data['sorted_dir'], ignore_errors=True)

        os.makedirs(session_data['unsorted_dir'], exist_ok=True)
        os.makedirs(session_data['sorted_dir'], exist_ok=True)

        for class_name in CLASS_MAPPING.values():
            class_dir = os.path.join(session_data['sorted_dir'], class_name)
            os.makedirs(class_dir, exist_ok=True)
            
            for subfolder in STATUS_SUBFOLDERS:
                os.makedirs(os.path.join(class_dir, subfolder), exist_ok=True)

        session_data['history'] = []
        session_data['upload_complete'] = False
        reset_current_selection(session_data)

        return True
    except Exception as e:
        print(f"Error clearing session: {e}")
        return False