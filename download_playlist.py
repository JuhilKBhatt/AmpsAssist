import yt_dlp
import os

def download_playlist(playlist_url, base_folder="Music_Downloads"):
    """
    Downloads a YouTube playlist and formats it for Plexamp.
    Structure: base_folder/Artist/Playlist_Title/Title.ext
    """
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        # Use FFmpeg to extract audio and convert to mp3
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'EmbedThumbnail',  # Embeds video thumbnail as cover art
            },
            {
                'key': 'FFmpegMetadata',  # Writes metadata (Artist, Title, etc.)
            }
        ],
        # Write thumbnail to disk so it can be embedded, then delete it
        'writethumbnail': True,
        
        # OUTPUT TEMPLATE (Critical for Plex)
        # We try to get the 'Artist' (channel or uploader) and 'Playlist Title' (Album)
        # If 'artist' metadata isn't perfect on YT, it defaults to the Uploader name.
        # Structure: Base_Folder / Artist / Playlist_Name / Title.mp3
        'outtmpl': f'{base_folder}/%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s',
        
        # Ignore errors (like deleted videos) so the script doesn't crash
        'ignoreerrors': True,
        
        # Archive file to record downloaded IDs so we don't re-download them later
        'download_archive': 'downloaded_songs.txt',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Starting download for: {playlist_url}...")
            ydl.download([playlist_url])
            print("\nDownload complete!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Replace this with your YouTube Playlist URL
    PLAYLIST_URL = input("Enter the YouTube Playlist URL: ").strip()
    
    # Optional: Change the output folder path
    OUTPUT_DIR = "Plex_Music"
    
    download_playlist(PLAYLIST_URL, OUTPUT_DIR)