# ./src/main.py
import time
import schedule
from file_manager import setup_directories
from playlist_manager import get_playlist_tracks
from downloader import process_downloads

def sync_job():
    print("Starting AmpsAssist Sync Job...")
    setup_directories()
    
    tracks = get_playlist_tracks()
    print(f"Found {len(tracks)} tracks across playlists. Processing...")
    
    process_downloads(tracks)
    print("AmpsAssist Sync Complete. Waiting for next interval...\n")

if __name__ == "__main__":
    # Run immediately on startup
    sync_job()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(sync_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)