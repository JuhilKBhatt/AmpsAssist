import yt_dlp
import os
from concurrent.futures import ThreadPoolExecutor

def get_ydl_opts(base_folder, is_playlist_info=False):
    """Returns the configuration for yt-dlp."""
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ],
        'writethumbnail': True,
        # UPDATED: This template saves everything directly into the base_folder
        'outtmpl': f'{base_folder}/%(title)s.%(ext)s',
        'ignoreerrors': True,
        'download_archive': 'downloaded_songs.txt',
        'quiet': True,
        'no_warnings': True,
    }
    
    if is_playlist_info:
        opts.update({'extract_flat': True, 'quiet': True})
        
    return opts

def download_single_track(track_url, base_folder):
    """Worker function to download a single track."""
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(base_folder)) as ydl:
            ydl.download([track_url])
    except Exception as e:
        print(f"Error downloading {track_url}: {e}")

def download_playlist_parallel(playlist_url, base_folder="Music_Downloads", workers=4):
    """
    Extracts track URLs from a playlist and downloads them using multiple workers.
    """
    # Create the folder if it doesn't exist
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    print(f"--- Extracting playlist info ---")
    
    with yt_dlp.YoutubeDL(get_ydl_opts(base_folder, is_playlist_info=True)) as ydl:
        playlist_dict = ydl.extract_info(playlist_url, download=False)
        
        if 'entries' not in playlist_dict:
            print("Could not find any tracks.")
            return

        track_urls = [
            f"https://www.youtube.com/watch?v={entry['id']}" 
            for entry in playlist_dict['entries'] if entry
        ]

    total_tracks = len(track_urls)
    print(f"Found {total_tracks} tracks. Downloading to '{base_folder}' with {workers} workers...\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i, url in enumerate(track_urls, 1):
            executor.submit(download_single_track, url, base_folder)
            # This print will show up as soon as a worker picks up the job
            print(f"Queued [{i}/{total_tracks}]: {url}")

    print(f"\n--- Finished! Your music is in the '{base_folder}' folder. ---")

if __name__ == "__main__":
    PLAYLIST_URL = input("Enter YouTube Playlist URL: ").strip()
    
    # You can change "Music_Downloads" to whatever folder name you prefer
    OUTPUT_FOLDER = "Music_Downloads"
    MAX_WORKERS = 4 
    
    download_playlist_parallel(PLAYLIST_URL, OUTPUT_FOLDER, workers=MAX_WORKERS)