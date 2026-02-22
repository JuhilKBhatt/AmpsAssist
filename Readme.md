# Amps Assist

Description: Plex Amps Music Download Assistant.

Add config.py file

```
import os

# Your 4 YouTube Music Playlist IDs (Replace these with your actual IDs)
# You can find the ID in the URL: music.youtube.com/playlist?list=ID_HERE
PLAYLIST_IDS = [
    "PL_EXAMPLE_ID_1",
    "PL_EXAMPLE_ID_2",
    "PL_EXAMPLE_ID_3",
    "PL_EXAMPLE_ID_4"
]

MAX_SONGS_PER_PLAYLIST = 10
NUM_WORKERS = 4
RATE_LIMIT_BYTES = 1_000_000  # Cap at ~1 MB/s per worker to avoid throttling

# Directory configurations
BASE_DIR = os.getenv("DOWNLOAD_DIR", "/app/downloads")
ALL_SONGS_DIR = os.path.join(BASE_DIR, "All_Songs")
PLAYLISTS_DIR = os.path.join(BASE_DIR, "Playlists")
ARCHIVE_FILE = os.path.join(BASE_DIR, "downloaded_archive.txt")
```



docker run -it --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install ytmusicapi && ytmusicapi oauth"
