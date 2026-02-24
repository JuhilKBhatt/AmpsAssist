# ./src/plex_sync.py
import os
import time
import glob
import requests
from config import PLAYLISTS_DIR

PLEX_URL = os.getenv("PLEX_URL", "http://192.168.1.230:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_LIBRARY_NAME = os.getenv("PLEX_LIBRARY", "Music")
PLEX_M3U_PATH = os.getenv("PLEX_M3U_PATH", "/data/music/Playlists")

def get_section_id():
    """Finds the internal ID of your Plex Music library."""
    url = f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers).json()
    for directory in response.get("MediaContainer", {}).get("Directory", []):
        if directory.get("title") == PLEX_LIBRARY_NAME:
            return directory.get("key")
    return None

def trigger_scan(section_id):
    """Tells Plex to look for the newly downloaded MP3s."""
    url = f"{PLEX_URL}/library/sections/{section_id}/refresh?X-Plex-Token={PLEX_TOKEN}"
    requests.get(url)

def get_existing_playlists():
    """Fetches a list of all current playlists in Plex."""
    url = f"{PLEX_URL}/playlists?X-Plex-Token={PLEX_TOKEN}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers).json()
    playlists = {}
    if "Metadata" in response.get("MediaContainer", {}):
        for pl in response["MediaContainer"]["Metadata"]:
            playlists[pl["title"]] = pl["ratingKey"]
    return playlists

def delete_playlist(rating_key):
    """Deletes an old playlist from Plex."""
    url = f"{PLEX_URL}/playlists/{rating_key}?X-Plex-Token={PLEX_TOKEN}"
    requests.delete(url)

def upload_m3u(section_id, m3u_name):
    """Uploads the new .m3u file natively into Plex's database safely."""
    plex_path = f"{PLEX_M3U_PATH}/{m3u_name}"
    url = f"{PLEX_URL}/playlists/upload"
    
    # Passing parameters this way is much safer for special characters
    params = {
        "sectionID": section_id,
        "path": plex_path,
        "X-Plex-Token": PLEX_TOKEN
    }
    
    response = requests.post(url, params=params)
    
    if response.status_code == 200:
        return True
    else:
        # If Plex rejects it, print exactly what Plex's brain is saying!
        print(f"    Failed! Plex Error: {response.text.strip()}")
        return False

def sync_to_plex():
    """Main function to run the sync logic."""
    if not PLEX_TOKEN:
        print("PLEX_TOKEN not found in .env. Skipping Plex API sync.")
        return

    try:
        print(f"\n--- Starting Plex API Sync ---")
        print(f"Connecting to Plex at {PLEX_URL}...")
        section_id = get_section_id()
        if not section_id:
            print(f"Could not find a library named '{PLEX_LIBRARY_NAME}'.")
            return

        print(f"Triggering library scan for '{PLEX_LIBRARY_NAME}'...")
        trigger_scan(section_id)
        
        # INCREASED WAIT TIME: Give Plex more time to ingest the files!
        print("Waiting 60 seconds for Plex to process the new MP3 files...")
        time.sleep(60)

        print("Fetching existing Plex playlists...")
        existing_playlists = get_existing_playlists()

        # 1. STRICT MIRRORING: Delete ALL existing playlists in Plex to remove abandoned mixes
        for pl_title, rating_key in existing_playlists.items():
            print(f" -> Deleting old Plex playlist: '{pl_title}'")
            delete_playlist(rating_key)

        # 2. Upload only the fresh, active M3U files
        m3u_files = glob.glob(os.path.join(PLAYLISTS_DIR, "*.m3u"))
        for m3u_file in m3u_files:
            m3u_name = os.path.basename(m3u_file)
            playlist_title = os.path.splitext(m3u_name)[0]

            print(f" -> Uploading new M3U to Plex: '{playlist_title}'")
            success = upload_m3u(section_id, m3u_name)
            if success:
                print(f"    Success!")

        print("Plex API Sync Complete!\n")
        
    except Exception as e:
        print(f"Plex sync failed: {e}")

if __name__ == "__main__":
    sync_to_plex()