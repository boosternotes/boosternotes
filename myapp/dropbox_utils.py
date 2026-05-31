import os
import io
import dropbox
from django.conf import settings
from dropbox import Dropbox, exceptions
from dropbox.files import FileMetadata, UploadSessionCursor, CommitInfo
from dropbox.exceptions import ApiError


class DropboxManager:
    """Handle all Dropbox operations"""
    
    @staticmethod
    def get_dropbox_client():
        return Dropbox(
            oauth2_refresh_token=settings.DROPBOX_REFRESH_TOKEN,
            app_key=settings.DROPBOX_APP_KEY,
            app_secret=settings.DROPBOX_APP_SECRET
        )
    @staticmethod
    def upload_file(file_obj, file_name, folder_path=None):
        """
        Upload file to Dropbox
        Returns: dropbox_path, link
        """
        try:
            dbx = DropboxManager.get_dropbox_client()
            
            # Ensure folder exists
            if folder_path is None:
                folder_path = settings.DROPBOX_FOLDER
            
            # Create full path
            full_path = f"{folder_path}/{file_name}"
            
            # Upload file
            file_size = file_obj.size
            chunk_size = 4 * 1024 * 1024  # 4MB chunks
            
            if file_size <= chunk_size:
                # Small file - upload directly
                file_obj.seek(0)
                dbx.files_upload(
                    file_obj.read(),
                    full_path,
                    mode=dropbox.files.WriteMode('overwrite')
                )
            else:
                # Large file - upload in chunks
                session = dbx.files_upload_session_start(file_obj.read(chunk_size))
                cursor = dropbox.files.UploadSessionCursor(
                    session.session_id,
                    offset=file_obj.tell()
                )
                commit = dropbox.files.CommitInfo(path=full_path, mode='overwrite')
                
                while file_obj.tell() < file_size:
                    chunk = file_obj.read(chunk_size)
                    if file_obj.tell() + len(chunk) >= file_size:
                        # Last chunk
                        dbx.files_upload_session_finish(chunk, cursor, commit)
                    else:
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = file_obj.tell()
            
            # Get shared link
            try:
                shared_link = dbx.sharing_create_shared_link_with_settings(full_path)
                link = shared_link.url
            except:
                link = f"https://www.dropbox.com/s/{full_path}"
            
            return {
                'success': True,
                'dropbox_path': full_path,
                'link': link,
                'message': 'File uploaded successfully'
            }
            
        except exceptions.ApiError as e:
            return {
                'success': False,
                'error': f'Dropbox API error: {str(e)}',
                'dropbox_path': None,
                'link': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'dropbox_path': None,
                'link': None
            }
    
    @staticmethod
    def delete_file(dropbox_path):
        """Delete file from Dropbox"""
        try:
            dbx = DropboxManager.get_dropbox_client()
            dbx.files_delete_v2(dropbox_path)
            return {
                'success': True,
                'message': 'File deleted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }