# ./src/file_manager.py
import os
import glob
from config import ALL_SONGS_DIR, PLAYLISTS_DIR

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