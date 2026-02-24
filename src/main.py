# ./src/main.py
import time
import schedule
from file_manager import setup_directories, clear_old_playlists, remove_orphaned_songs
from playlist_manager import get_playlist_tracks
from downloader import process_downloads
from plex_sync import get_protected_plex_data, sync_to_plex

def sync_job():
    print("Starting AmpsAssist Sync Job...")
    setup_directories()
    
    # Wipe the old .m3u files so we get a fresh mix generated
    clear_old_playlists()
    
    tracks = get_playlist_tracks()
    print(f"Found {len(tracks)} tracks across playlists. Processing...")
    
    # Download the tracks and generate the .m3u files
    process_downloads(tracks)
    
    # Check Plex for playlists you manually marked with "save"
    protected_data = get_protected_plex_data()
    protected_paths = []
    for pl_info in protected_data.values():
        protected_paths.extend(pl_info.get("paths", []))
    
    # Clean up (pass the protected paths so they survive!)
    remove_orphaned_songs(protected_paths)
    
    # Talk to Plex to update the live playlists
    sync_to_plex(protected_data)
    
    print("AmpsAssist Sync Complete. Waiting for next interval...\n")

if __name__ == "__main__":
    # Run immediately on startup
    sync_job()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(sync_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)