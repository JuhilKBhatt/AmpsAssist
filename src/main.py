import time
import schedule
from file_manager import setup_directories, clear_old_playlists, remove_orphaned_songs
from playlist_manager import get_playlist_tracks
from downloader import process_downloads, console
from jellyfin_sync import sync_to_jellyfin

import yt_dlp

def sync_job():
    console.rule("[bold cyan]AmpsAssist Sync Job Started")
    console.print(f"[dim]yt-dlp version: {yt_dlp.version.__version__}[/dim]")
    setup_directories()
    
    # Wipe the old .m3u files so we get a fresh mix generated
    console.print("[yellow]Clearing old playlist files...[/yellow]")
    clear_old_playlists()
    
    tracks = get_playlist_tracks()
    console.print(f"\n[bold green]Found {len(tracks)} tracks across playlists.[/bold green] Processing...")
    
    # Download the tracks and generate the .m3u files
    process_downloads(tracks)
    
    # Note: Jellyfin doesn't support the 'save' description feature like Plex.
    # To protect files, you could add logic to read specific M3Us.
    protected_paths = []
    
    # Clean up (pass the protected paths so they survive!)
    console.print("\n[yellow]Removing orphaned songs...[/yellow]")
    remove_orphaned_songs(protected_paths)
    
    # Talk to Jellyfin to trigger a library scan
    console.print("[cyan]Triggering Jellyfin Library Scan...[/cyan]")
    sync_to_jellyfin()
    
    console.rule("[bold green]Sync Complete! Waiting for next interval...")

if __name__ == "__main__":
    # Run immediately on startup
    sync_job()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(sync_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)