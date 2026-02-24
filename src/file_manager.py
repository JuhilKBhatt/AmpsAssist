# ./src/file_manager.py
import os
import glob
import shutil
from config import ALL_SONGS_DIR, PLAYLISTS_DIR, DELETE_ORPHANED_SONGS

def setup_directories():
    """Ensure base directories exist."""
    os.makedirs(ALL_SONGS_DIR, exist_ok=True)
    os.makedirs(PLAYLISTS_DIR, exist_ok=True)

def clear_old_playlists():
    """Deletes old .m3u files before a fresh sync so mixes stay perfectly up-to-date."""
    print("Clearing old playlist files...")
    m3u_files = glob.glob(os.path.join(PLAYLISTS_DIR, "*.m3u"))
    for f in m3u_files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"Could not remove old playlist {f}: {e}")

def add_to_m3u_playlist(file_path, playlist_name):
    """Appends the song's absolute Plex path to an .m3u playlist file."""
    safe_playlist_name = "".join(x for x in playlist_name if x.isalnum() or x in " -_")
    m3u_path = os.path.join(PLAYLISTS_DIR, f"{safe_playlist_name}.m3u")
    
    try:
        plex_absolute_path = file_path.replace("/app/downloads", "/data/music")
        
        # Append the absolute path to the .m3u file
        with open(m3u_path, 'a', encoding='utf-8') as f:
            f.write(f"{plex_absolute_path}\n")
            
    except Exception as e:
        print(f"Failed to add to M3U: {e}")

def remove_orphaned_songs(protected_plex_paths=None):
    if not DELETE_ORPHANED_SONGS:
        return

    if protected_plex_paths is None:
        protected_plex_paths = []

    print("\nScanning for orphaned songs to free up storage...")
    
    # 1. Gather all 'in-use' songs from the current M3U files
    in_use_local_paths = set()

    # 1. Protect the saved files from Plex
    for plex_path in protected_plex_paths:
        local_path = plex_path.replace("/data/music", "/app/downloads")
        in_use_local_paths.add(local_path)

    # 2. Protect the current active M3U files
    m3u_files = glob.glob(os.path.join(PLAYLISTS_DIR, "*.m3u"))
    
    for m3u in m3u_files:
        try:
            with open(m3u, 'r', encoding='utf-8') as f:
                for line in f:
                    plex_path = line.strip()
                    if plex_path:
                        # Convert Plex paths back to local Docker paths for comparison
                        local_path = plex_path.replace("/data/music", "/app/downloads")
                        in_use_local_paths.add(local_path)
        except Exception as e:
            print(f"Error reading {m3u}: {e}")

    # 3. Walk through All_Songs and delete anything not in use
    deleted_count = 0
    for root, dirs, files in os.walk(ALL_SONGS_DIR):
        for filename in files:
            if filename.endswith(".mp3"):
                file_path = os.path.join(root, filename)
                if file_path not in in_use_local_paths:
                    try:
                        os.remove(file_path)
                        print(f" -> Deleted orphaned song: {filename}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete {filename}: {e}")

    # 4. Aggressive folder cleanup
    for root, dirs, files in os.walk(ALL_SONGS_DIR, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            
            # Check if there are any mp3 files in this directory or its subdirectories
            has_mp3 = False
            for r, d, f in os.walk(dir_path):
                if any(file.endswith(".mp3") for file in f):
                    has_mp3 = True
                    break
            
            # If no MP3s exist, forcefully delete the entire folder and any leftover thumbnails
            if not has_mp3:
                try:
                    shutil.rmtree(dir_path)
                    print(f" -> Removed empty/ghost folder: {dir_name}")
                except Exception:
                    pass
    
    print(f"Storage cleanup complete. Removed {deleted_count} unused tracks.")