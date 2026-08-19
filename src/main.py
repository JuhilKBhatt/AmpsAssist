import time
import schedule
from file_manager import setup_directories, clear_old_playlists, remove_orphaned_songs
from playlist_manager import get_playlist_tracks
from downloader import process_downloads, console
from jellyfin_sync import sync_to_jellyfin
from plex_sync import sync_to_plex, get_protected_plex_data

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
    
    # Check Plex for playlists manually marked with "save"
    protected_data = get_protected_plex_data()
    protected_paths = []
    for pl_info in protected_data.values():
        protected_paths.extend(pl_info.get("paths", []))
    
    # Clean up (pass the protected paths so they survive!)
    console.print("\n[yellow]Removing orphaned songs...[/yellow]")
    remove_orphaned_songs(protected_paths)
    
    # Talk to Media Servers to trigger a library scan
    console.print("\n[cyan]Triggering Library Scans...[/cyan]")
    sync_to_jellyfin()
    sync_to_plex(protected_data)
    
    console.rule("[bold green]Sync Complete! Waiting for next interval...")

if __name__ == "__main__":
    # Run immediately on startup
    sync_job()
    
    # Schedule to run at 4am and 4pm every day
    schedule.every().day.at("04:00").do(sync_job)
    schedule.every().day.at("16:00").do(sync_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)