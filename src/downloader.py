# ./src/downloader.py
import os
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2
from config import ALL_SONGS_DIR, RATE_LIMIT_BYTES, NUM_WORKERS
from file_manager import add_to_m3u_playlist

def apply_metadata(file_path, track):
    """Forcefully embeds ytmusicapi metadata and Plex required tags directly into the MP3."""
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass # Tags already exist
        
        audio.tags.add(TIT2(encoding=3, text=track['title']))
        audio.tags.add(TPE1(encoding=3, text=track['artist']))
        audio.tags.add(TPE2(encoding=3, text=track['artist'])) # Plex Album Artist
        audio.tags.add(TALB(encoding=3, text=track['album']))
        audio.save()
        print(f"Tagged: {track['artist']} - {track['title']}")
    except Exception as e:
        print(f"Failed to apply metadata to {file_path}: {e}")

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
    """Downloads a single track and routes it to the correct Plex folder."""
    
    # Skip invalid tracks (like local YTM uploads that have no YouTube ID)
    if not track.get('video_id'):
        print(f"Skipped {track.get('title')}: No YouTube ID (likely a local upload or region blocked).")
        return
        
    existing_file = find_existing_file(track['video_id'])
    if existing_file:
        # We already have the file! Just add its path to the M3U playlist.
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
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            if info:
                expected_filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(expected_filename)
                final_filename = base + ".mp3"
                
                if os.path.exists(final_filename):
                    apply_metadata(final_filename, track)
                    # Add the brand new file to the M3U playlist!
                    add_to_m3u_playlist(final_filename, track['playlist_name'])
    except Exception as e:
        print(f"Failed to process {track['title']}: {e}")

def process_downloads(tracks):
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(download_track, tracks)