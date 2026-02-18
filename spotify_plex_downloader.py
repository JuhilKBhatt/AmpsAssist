import subprocess
import shutil
import sys
import os

def check_dependencies():
    """Checks if spotdl and ffmpeg are installed."""
    missing = []
    if not shutil.which("spotdl"):
        missing.append("spotdl")
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    
    if missing:
        print("❌ Missing dependencies:")
        for tool in missing:
            print(f"   - {tool}")
        print("\nPlease install them:")
        print("   pip install spotdl")
        print("   (And ensure FFmpeg is installed and in your system PATH)")
        sys.exit(1)

def download_spotify_playlist(url, base_folder="Music_Downloads"):
    """
    Runs spotdl with the specific arguments to match Plex format:
    Base_Folder / Artist / Playlist_Name / Title.mp3
    """
    
    # OUTPUT TEMPLATE EXPLAINED:
    # {artist}    : The main artist name (e.g., "Daft Punk")
    # {list-name} : The name of the playlist you are downloading (e.g., "Discovery")
    # {title}     : The song title
    # {output-ext}: The extension (mp3/m4a)
    output_template = f"{base_folder}/{{artist}}/{{list-name}}/{{title}}.{{output-ext}}"

    command = [
        "spotdl",
        "download",
        url,
        
        # FORCE THE PLEX FORMAT
        "--output", output_template,
        
        # CONCURRENCY (WORKERS)
        "--dt", "5",  # Download Threads (8 files at once)
        "--st", "5",  # Search Threads (8 searches at once)
        
        # QUALITY
        "--bitrate", "320k", # Force high quality
        
        # METADATA
        "--lyrics", "genius", # Fetch lyrics from Genius
        "--generate-m3u"      # Create a playlist file for Plex to read
    ]

    print(f"\n🚀 Starting 8 Workers for: {url}")
    print(f"📂 Saving to: {base_folder}/[Artist]/[Playlist Name]/...\n")

    try:
        # We use subprocess.run to let spotdl take over the terminal 
        # so you can see its beautiful built-in progress UI.
        subprocess.run(command, check=True)
        print("\n✅ Download Complete!")
        
    except subprocess.CalledProcessError:
        print("\n❌ An error occurred during the download.")
    except KeyboardInterrupt:
        print("\n🛑 Download stopped by user.")

if __name__ == "__main__":
    print("--- Spotify to Plex Downloader ---")
    check_dependencies()
    
    # 1. Get URL
    target_url = input("Enter Spotify Playlist/Album URL: ").strip()
    
    if target_url:
        # 2. Run the downloader
        download_spotify_playlist(target_url)
    else:
        print("No URL provided.")