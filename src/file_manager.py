# ./src/file_manager.py
import os
import shutil
from config import ALL_SONGS_DIR, PLAYLISTS_DIR

def setup_directories():
    """Ensure base directories exist."""
    os.makedirs(ALL_SONGS_DIR, exist_ok=True)
    os.makedirs(PLAYLISTS_DIR, exist_ok=True)

def copy_to_playlist_folder(file_path, playlist_name):
    """Copies a downloaded track from the main folder to its playlist folder."""
    # Clean the playlist name for safe folder creation
    safe_playlist_name = "".join(x for x in playlist_name if x.isalnum() or x in " -_")
    playlist_path = os.path.join(PLAYLISTS_DIR, safe_playlist_name)
    os.makedirs(playlist_path, exist_ok=True)
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(playlist_path, filename)
    
    # Copy if it doesn't already exist in the playlist folder
    if not os.path.exists(dest_path):
        shutil.copy2(file_path, dest_path)
        print(f"Copied: {filename} -> {safe_playlist_name}/")