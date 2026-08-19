# ./src/file_manager.py
import os
import glob
import shutil
from config import ALL_SONGS_DIR, PLAYLISTS_DIR, DELETE_ORPHANED_SONGS

# Path constants for Docker environment
DOCKER_DOWNLOADS_PATH = "/app/downloads"
JELLYFIN_MUSIC_PATH = os.getenv("JELLYFIN_MUSIC_PATH", "/media/music")
PLEX_MUSIC_PATH = os.getenv("PLEX_MUSIC_PATH", "/media/music")

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
    """Appends the song's absolute path to .m3u playlist files."""
    safe_playlist_name = "".join(x for x in playlist_name if x.isalnum() or x in " -_")
    
    jellyfin_absolute_path = file_path.replace(DOCKER_DOWNLOADS_PATH, JELLYFIN_MUSIC_PATH)
    plex_absolute_path = file_path.replace(DOCKER_DOWNLOADS_PATH, PLEX_MUSIC_PATH)
    
    try:
        # If both systems use the same internal mount path, we only need ONE file!
        if JELLYFIN_MUSIC_PATH == PLEX_MUSIC_PATH:
            single_m3u_path = os.path.join(PLAYLISTS_DIR, f"{safe_playlist_name}.m3u")
            with open(single_m3u_path, 'a', encoding='utf-8') as f:
                f.write(f"{jellyfin_absolute_path}\n")
        else:
            jellyfin_m3u_path = os.path.join(PLAYLISTS_DIR, f"{safe_playlist_name}_jellyfin.m3u")
            plex_m3u_path = os.path.join(PLAYLISTS_DIR, f"{safe_playlist_name}_plex.m3u")
            
            with open(jellyfin_m3u_path, 'a', encoding='utf-8') as f:
                f.write(f"{jellyfin_absolute_path}\n")
                
            with open(plex_m3u_path, 'a', encoding='utf-8') as f:
                f.write(f"{plex_absolute_path}\n")
            
    except Exception as e:
        print(f"Failed to add to M3U: {e}")

def remove_orphaned_songs(protected_jellyfin_paths=None):
    if not DELETE_ORPHANED_SONGS:
        return

    if protected_jellyfin_paths is None:
        protected_jellyfin_paths = []

    print("\nScanning for orphaned songs to free up storage...")
    
    # Gather all 'in-use' songs from the current M3U files
    in_use_local_paths = set()

    for jellyfin_path in protected_jellyfin_paths:
        local_path = jellyfin_path.replace(JELLYFIN_MUSIC_PATH, DOCKER_DOWNLOADS_PATH)
        in_use_local_paths.add(local_path)

    # Protect the current active M3U files
    m3u_files = glob.glob(os.path.join(PLAYLISTS_DIR, "*.m3u"))
    
    for m3u in m3u_files:
        try:
            with open(m3u, 'r', encoding='utf-8') as f:
                for line in f:
                    media_path = line.strip()
                    if media_path:
                        # Since JELLYFIN_MUSIC_PATH and PLEX_MUSIC_PATH are the same, 
                        # replacing either will work. If they differ, check suffix.
                        if "_plex" in m3u:
                            local_path = media_path.replace(PLEX_MUSIC_PATH, DOCKER_DOWNLOADS_PATH)
                        else:
                            local_path = media_path.replace(JELLYFIN_MUSIC_PATH, DOCKER_DOWNLOADS_PATH)
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