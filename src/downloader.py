# ./src/downloader.py
import os
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from config import ALL_SONGS_DIR, ARCHIVE_FILE, RATE_LIMIT_BYTES, NUM_WORKERS
from file_manager import copy_to_playlist_folder

def apply_metadata(file_path, track):
    """Forcefully embeds ytmusicapi metadata directly into the MP3 tags."""
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass # Tags already exist
        
        # Inject standard MP3 metadata
        audio.tags.add(TIT2(encoding=3, text=track['title']))
        audio.tags.add(TPE1(encoding=3, text=track['artist']))
        audio.tags.add(TALB(encoding=3, text=track['album']))
        audio.save()
        print(f"Tagged: {track['artist']} - {track['title']}")
    except Exception as e:
        print(f"Failed to apply metadata to {file_path}: {e}")

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
                
                if os.path.exists(final_filename):
                    # Step 1: Apply YTMusic API Metadata
                    apply_metadata(final_filename, track)
                    # Step 2: Copy to Playlist directory
                    copy_to_playlist_folder(final_filename, track['playlist_name'])
    except Exception as e:
        print(f"Failed to process {track['title']}: {e}")

def process_downloads(tracks):
    """Manages the download queue using workers."""
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(download_track, tracks)