# ./src/jellyfin_sync.py
import os
import requests

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "http://192.168.1.230:8096")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")

def trigger_library_scan():
    """Tells Jellyfin to scan the library for the newly downloaded MP3s and M3Us."""
    if not JELLYFIN_API_KEY:
        print("JELLYFIN_API_KEY not found in .env. Skipping Jellyfin API sync.")
        return
        
    print(f"\n--- Starting Jellyfin Library Scan ---")
    print(f"Connecting to Jellyfin at {JELLYFIN_URL}...")
    
    url = f"{JELLYFIN_URL}/Library/Refresh"
    headers = {
        "X-Emby-Token": JELLYFIN_API_KEY,
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 204 or response.status_code == 200:
            print("Successfully triggered Jellyfin library scan.")
        else:
            print(f"Failed to trigger scan. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error communicating with Jellyfin: {e}")
        
    print("Jellyfin API Sync Complete!\n")

def sync_to_jellyfin(protected_data=None):
    # For now, just trigger a scan. Jellyfin will pick up the M3Us.
    # In the future we could manage playlists directly via API.
    trigger_library_scan()

if __name__ == "__main__":
    sync_to_jellyfin()