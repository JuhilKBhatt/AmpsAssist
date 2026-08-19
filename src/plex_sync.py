# ./src/plex_sync.py
import os
import requests

PLEX_URL = os.getenv("PLEX_URL", "http://192.168.1.230:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_LIBRARY = os.getenv("PLEX_LIBRARY", "Music")

def trigger_library_scan():
    """Tells Plex to scan the library for the newly downloaded MP3s and M3Us."""
    if not PLEX_TOKEN:
        print("PLEX_TOKEN not found in .env. Skipping Plex API sync.")
        return
        
    print(f"\n--- Starting Plex Library Scan ---")
    print(f"Connecting to Plex at {PLEX_URL}...")
    
    # First, get the library section ID
    section_id = None
    try:
        sections_url = f"{PLEX_URL}/library/sections"
        headers = {"X-Plex-Token": PLEX_TOKEN, "Accept": "application/json"}
        response = requests.get(sections_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for directory in data.get('MediaContainer', {}).get('Directory', []):
                if directory.get('title') == PLEX_LIBRARY:
                    section_id = directory.get('key')
                    break
        else:
            print(f"Failed to fetch Plex sections. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error communicating with Plex: {e}")
        return

    if not section_id:
        print(f"Could not find a Plex library named '{PLEX_LIBRARY}'. Cannot trigger scan.")
        return

    # Trigger the refresh
    try:
        refresh_url = f"{PLEX_URL}/library/sections/{section_id}/refresh"
        headers = {"X-Plex-Token": PLEX_TOKEN}
        response = requests.get(refresh_url, headers=headers)
        if response.status_code == 200:
            print(f"Successfully triggered Plex library scan for '{PLEX_LIBRARY}'.")
        else:
            print(f"Failed to trigger Plex scan. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error triggering Plex scan: {e}")
        
    print("Plex API Sync Complete!\n")

def sync_to_plex():
    trigger_library_scan()

if __name__ == "__main__":
    sync_to_plex()
