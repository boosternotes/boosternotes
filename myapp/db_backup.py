import os
import dropbox
from datetime import datetime
from django.conf import settings

DROPBOX_BACKUP_PATH = '/db-backups/db_latest.sqlite3'
DROPBOX_HISTORY_DIR = '/db-backups/history'


def get_dropbox_client():
    return dropbox.Dropbox(
        oauth2_refresh_token=settings.DROPBOX_REFRESH_TOKEN,
        app_key=settings.DROPBOX_APP_KEY,
        app_secret=settings.DROPBOX_APP_SECRET
    )


def get_db_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'db.sqlite3'
    )


def backup_to_dropbox():
    """
    Uploads db.sqlite3 to Dropbox.
    Saves two copies:
      1. /db-backups/db_latest.sqlite3  (always overwritten)
      2. /db-backups/history/db_YYYYMMDD_HHMMSS.sqlite3 (timestamped copy)
    Returns the timestamp string on success.
    """
    dbx = get_dropbox_client()
    db_path = get_db_path()

    with open(db_path, 'rb') as f:
        data = f.read()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Overwrite latest
    dbx.files_upload(
        data,
        DROPBOX_BACKUP_PATH,
        mode=dropbox.files.WriteMode.overwrite
    )

    # Save timestamped history copy
    history_path = f"{DROPBOX_HISTORY_DIR}/db_{timestamp}.sqlite3"
    dbx.files_upload(
        data,
        history_path,
        mode=dropbox.files.WriteMode.add
    )

    return timestamp


def restore_from_dropbox(history_filename=None):
    """
    Restores db.sqlite3 from Dropbox.
    If history_filename is provided, restores that specific backup.
    Otherwise restores the latest backup.
    """
    dbx = get_dropbox_client()
    db_path = get_db_path()

    if history_filename:
        path = f"{DROPBOX_HISTORY_DIR}/{history_filename}"
    else:
        path = DROPBOX_BACKUP_PATH

    _, res = dbx.files_download(path)

    with open(db_path, 'wb') as f:
        f.write(res.content)


def list_backups():
    """
    Returns a list of timestamped backup filenames from Dropbox history folder,
    sorted newest first.
    """
    dbx = get_dropbox_client()
    try:
        result = dbx.files_list_folder(DROPBOX_HISTORY_DIR)
        files = [
            entry.name
            for entry in result.entries
            if isinstance(entry, dropbox.files.FileMetadata)
        ]
        return sorted(files, reverse=True)
    except dropbox.exceptions.ApiError:
        return []
