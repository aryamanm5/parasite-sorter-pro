import os
import uuid
import shutil
import threading
from datetime import datetime, timedelta
from flask import session

from config import UPLOAD_FOLDER, SESSION_TIMEOUT_HOURS

# Store session data in memory
sessions_data = {}
sessions_lock = threading.Lock()


def get_session_id():
    """Get or create session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_session_data():
    """Get or create session data for current user.

    Only the two top-level directories are made here. Class/status subfolders are
    created on demand at write time — a session that classifies ten images has no
    use for 44 empty directories. ponytail: makedirs where the write happens.
    """
    session_id = get_session_id()

    with sessions_lock:
        if session_id not in sessions_data:
            session_dir = os.path.join(UPLOAD_FOLDER, session_id)
            data = {
                'last_access': datetime.now(),
                'session_dir': session_dir,
                'unsorted_dir': os.path.join(session_dir, 'unsorted'),
                'sorted_dir': os.path.join(session_dir, 'sorted'),
                'dataset_name': None,
                'history': [],
                'redo_stack': [],
                'flag_counter': 0,
                'upload_complete': False,
            }

            os.makedirs(data['unsorted_dir'], exist_ok=True)
            os.makedirs(data['sorted_dir'], exist_ok=True)
            sessions_data[session_id] = data

        sessions_data[session_id]['last_access'] = datetime.now()
        return sessions_data[session_id]


def cleanup_old_sessions():
    """Remove expired sessions."""
    cutoff = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)

    with sessions_lock:
        expired = [sid for sid, data in sessions_data.items() if data['last_access'] < cutoff]

        for sid in expired:
            shutil.rmtree(sessions_data.pop(sid)['session_dir'], ignore_errors=True)
            print(f"Cleaned up session: {sid}")


def reset_session():
    """Drop this session's data and files. The next request rebuilds it empty."""
    with sessions_lock:
        data = sessions_data.pop(get_session_id(), None)

    if data:
        shutil.rmtree(data['session_dir'], ignore_errors=True)
