"""End-to-end check of the classify/undo/redo/flag flow.

Run with: python test_sorter.py

ponytail: one file, plain asserts, no framework. It drives the real Flask app
through its real routes and looks at the real files on disk.
"""
import io
import os
import zipfile

from app import app

# allowed_file only looks at the extension and nothing ever decodes these,
# so a few bytes with the right name is a valid test image.
IMAGES = ['a.png', 'b.png', 'c.png']


def make_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name in IMAGES:
            z.writestr(name, b'not-really-a-png')
        z.writestr('__MACOSX/junk.png', b'skip me')
        z.writestr('notes.txt', b'skip me too')
    buf.seek(0)
    return buf


def sorted_dir(client):
    from session_manager import sessions_data
    with client.session_transaction() as sess:
        return sessions_data[sess['session_id']]['sorted_dir']


def classify(client, first, second, status):
    return client.post('/classify', json={'first': first, 'second': second,
                                          'status': status, 'time_spent': 1.5}).get_json()


def main():
    client = app.test_client()

    client.get('/')
    res = client.post('/upload_dataset', data={'dataset_zip': (make_zip(), 'my_dataset.zip')},
                      content_type='multipart/form-data').get_json()
    assert res['success'] and res['image_count'] == 3, res      # .txt and __MACOSX skipped

    state = client.get('/state').get_json()
    assert state['remaining_count'] == 3 and state['current_image'] == 'a.png', state
    assert state['total_sorted'] == 0, state

    # --- classify with an adjacent alternative -----------------------------
    res = classify(client, '1', '2', 'Usable')
    assert res['success'], res
    assert res['remaining_count'] == 2 and res['current_image'] == 'b.png', res
    assert res['total_sorted'] == 1, res
    # Second_Choice is a duplicate copy and must NOT inflate the counts.
    assert res['sorted_counts']['Middle Ring'] == 0, res['sorted_counts']

    root = sorted_dir(client)
    assert os.path.exists(os.path.join(root, 'Early Ring', 'Usable', 'a.png'))
    assert os.path.exists(os.path.join(root, 'Middle Ring', 'Second_Choice', 'a.png'))
    # Folders are made on demand — untouched classes have no directory at all.
    assert not os.path.exists(os.path.join(root, 'Schizont')), 'subfolders should be lazy'

    # --- undo puts the image back and drops the duplicate ------------------
    res = client.post('/undo').get_json()
    assert res['success'] and res['remaining_count'] == 3, res
    assert res['current_image'] == 'a.png' and res['redo_count'] == 1, res
    assert not os.path.exists(os.path.join(root, 'Middle Ring', 'Second_Choice', 'a.png'))

    # --- redo replays it ---------------------------------------------------
    res = client.post('/redo').get_json()
    assert res['success'] and res['remaining_count'] == 2 and res['redo_count'] == 0, res
    assert os.path.exists(os.path.join(root, 'Early Ring', 'Usable', 'a.png'))

    # --- flag sends the front image to the back ----------------------------
    res = client.post('/flag').get_json()
    assert res['success'] and res['current_image'] == 'c.png', res       # b.png went behind c.png
    assert res['remaining_count'] == 2, res

    # --- invalid input is rejected at the boundary -------------------------
    assert client.post('/classify', json={'first': 'zz', 'status': 'Usable'}).status_code == 400
    assert client.post('/classify', json={'first': '1', 'status': 'Excellent'}).status_code == 400
    assert client.post('/classify', json={'first': '1', 'second': 'zz',
                                          'status': 'Usable'}).status_code == 400
    # send_from_directory refuses to escape the session's unsorted dir.
    assert client.get('/serve_image/../../etc/passwd').status_code in (400, 404)

    # --- is_adjacent is derived, not stored --------------------------------
    classify(client, '1', '5', 'Limited')       # Early Ring / Schizont: not adjacent
    csv_text = client.get('/save_progress').get_data(as_text=True)
    rows = [line.split(',') for line in csv_text.strip().splitlines()[1:]]
    by_file = {r[0]: r for r in rows}
    assert by_file['a.png'][2] == 'Middle Ring' and by_file['a.png'][4] == 'Yes', by_file['a.png']
    assert by_file['c.png'][2] == 'Schizont' and by_file['c.png'][4] == 'No', by_file['c.png']
    assert by_file['a.png'][5] == '1.5', by_file['a.png']

    # --- download names itself after the dataset and carries the CSV -------
    res = client.get('/download')
    assert 'my_dataset_sorted.zip' in res.headers['Content-Disposition'], res.headers
    with zipfile.ZipFile(io.BytesIO(res.get_data())) as z:
        names = z.namelist()
    assert 'classifications.csv' in names, names
    assert 'Early Ring/Usable/a.png' in names, names
    assert 'Middle Ring/Second_Choice/a.png' in names, names   # duplicates ship, they just don't count

    # --- restoring progress classifies BY NAME, not by queue position ------
    # Only b.png is left unsorted; a CSV naming a.png first must not consume it.
    fresh = app.test_client()
    fresh.get('/')
    fresh.post('/upload_dataset', data={'dataset_zip': (make_zip(), 'd.zip')},
               content_type='multipart/form-data')
    saved = 'filename,first_label,second_label,status,is_adjacent,time_spent_sec\n' \
            'nosuchfile.png,Early Ring,,Usable,Yes,1\n' \
            'c.png,Schizont,,Limited,Yes,2\n'
    res = fresh.post('/upload_progress', data={'progress_csv': (io.BytesIO(saved.encode()), 'p.csv')},
                     content_type='multipart/form-data').get_json()
    assert res['success'] and res['sorted_counts']['Schizont'] == 1, res
    assert res['sorted_counts']['Early Ring'] == 0, res      # the missing row classified nothing
    assert res['current_image'] == 'a.png', res              # a.png untouched at the front

    # --- reset wipes it ----------------------------------------------------
    assert client.post('/reset').get_json()['success']
    state = client.get('/state').get_json()
    assert state['total_sorted'] == 0 and not state['upload_complete'], state

    print('ok — all checks passed')


if __name__ == '__main__':
    main()
