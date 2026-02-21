# ./src/downloader.py
import os
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from config import ALL_SONGS_DIR, ARCHIVE_FILE, RATE_LIMIT_BYTES, NUM_WORKERS
from file_manager import copy_to_playlist_folder

def download_track(track):
    """Downloads a single track and routes it to the correct folder."""
    video_url = f"https://www.youtube.com/watch?v={track['video_id']}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(ALL_SONGS_DIR, '%(title)s [%(id)s].%(ext)s'),
        'download_archive': ARCHIVE_FILE,
        'ratelimit': RATE_LIMIT_BYTES,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info runs the download if it's not in the archive
            info = ydl.extract_info(video_url, download=True)
            
            if info:
                # Resolve the final filename (.mp3)
                expected_filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(expected_filename)
                final_filename = base + ".mp3"
                
                # Copy to specific playlist folder
                if os.path.exists(final_filename):
                    copy_to_playlist_folder(final_filename, track['playlist_name'])
    except Exception as e:
        print(f"Failed to process {track['title']}: {e}")

def process_downloads(tracks):
    """Manages the download queue using workers."""
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(download_track, tracks)