# ./src/downloader.py
import os
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2
from config import ALL_SONGS_DIR, RATE_LIMIT_BYTES, NUM_WORKERS
from file_manager import add_to_m3u_playlist

def apply_metadata(file_path, track):
    """Forcefully embeds ytmusicapi metadata and Jellyfin required tags directly into the MP3."""
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass # Tags already exist
        
        audio.tags.add(TIT2(encoding=3, text=track['title']))
        audio.tags.add(TPE1(encoding=3, text=track['artist']))
        audio.tags.add(TPE2(encoding=3, text=track['artist'])) # Jellyfin Album Artist
        audio.tags.add(TALB(encoding=3, text=track['album']))
        audio.save()
    except Exception as e:
        pass

def get_safe_filename(name):
    return "".join(x for x in str(name) if x.isalnum() or x in " -_") or "Unknown"

def find_existing_file(video_id):
    if not os.path.exists(ALL_SONGS_DIR):
        return None
    search_string = f"[{video_id}].mp3"
    
    for root, dirs, files in os.walk(ALL_SONGS_DIR):
        for filename in files:
            if filename.endswith(search_string):
                return os.path.join(root, filename)
    return None

def download_track(track):
    """Downloads a single track and routes it to the correct Jellyfin folder."""
    
    # Remove noisy print statements so they don't break the progress bar display.
    if not track.get('video_id'):
        return
        
    existing_file = find_existing_file(track['video_id'])
    if existing_file:
        add_to_m3u_playlist(existing_file, track['playlist_name'])
        return

    video_url = f"https://www.youtube.com/watch?v={track['video_id']}"
    
    safe_artist = get_safe_filename(track['artist'])
    safe_album = get_safe_filename(track['album'])
    safe_title = get_safe_filename(track['title'])
    
    plex_dir = os.path.join(ALL_SONGS_DIR, safe_artist, safe_album)
    os.makedirs(plex_dir, exist_ok=True)
    
    out_path = os.path.join(plex_dir, f"{safe_title} [{track['video_id']}].%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_path,
        'ratelimit': RATE_LIMIT_BYTES,
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'}
        ],
        'extractor_args': {
            'youtube': {'player_client': ['default', 'web_safari', 'web_embedded']}
        },
        'quiet': True,
        'no_warnings': True,
        'logger': YtLogger(),
    }

    if os.path.exists('/app/cookies.txt') and os.path.getsize('/app/cookies.txt') > 0:
        ydl_opts['cookiefile'] = '/app/cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            if info:
                expected_filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(expected_filename)
                final_filename = base + ".mp3"
                
                if os.path.exists(final_filename):
                    apply_metadata(final_filename, track)
                    add_to_m3u_playlist(final_filename, track['playlist_name'])
    except Exception as e:
        pass

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

class YtLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): 
        # Ignore normal errors like "Video unavailable" to avoid spam, but show critical ones
        if "reloaded" in msg or "DRM" in msg or "bot" in msg or "Sign in" in msg:
            console.print(f"[bold red]yt-dlp Error:[/bold red] {msg}")

def process_downloads(tracks):
    total = len(tracks)
    completed = 0
    
    def track_wrapper(track):
        nonlocal completed
        try:
            download_track(track)
        except Exception:
            pass
        finally:
            completed += 1
            if completed % 10 == 0 or completed == total:
                console.print(f"[cyan]Progress:[/cyan] {completed}/{total} tracks processed...")

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(track_wrapper, tracks)