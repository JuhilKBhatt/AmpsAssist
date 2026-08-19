# ./src/plex_sync.py
import os
import time
import glob
import requests
from config import PLAYLISTS_DIR
from rich.console import Console

console = Console()

PLEX_URL = os.getenv("PLEX_URL", "http://192.168.1.230:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_LIBRARY_NAME = os.getenv("PLEX_LIBRARY", "Music")
PLEX_MUSIC_PATH = os.getenv("PLEX_MUSIC_PATH", "/media/music")
PLEX_M3U_PATH = f"{PLEX_MUSIC_PATH}/Playlists"

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
            title = pl.get("title")
            rating_key = pl.get("ratingKey")
            # Check if the word "save" is in the Plex description
            summary = pl.get("summary", "").lower()
            playlists[title] = {
                "ratingKey": rating_key,
                "is_saved": "save" in summary
            }
    return playlists

def get_playlist_items(rating_key):
    """Fetches the internal file paths of every song inside a specific Plex playlist."""
    url = f"{PLEX_URL}/playlists/{rating_key}/items?X-Plex-Token={PLEX_TOKEN}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers).json()
    paths = []
    if "Metadata" in response.get("MediaContainer", {}):
        for track in response["MediaContainer"]["Metadata"]:
            try:
                for media in track.get("Media", []):
                    for part in media.get("Part", []):
                        if "file" in part:
                            paths.append(part["file"])
            except Exception:
                pass
    return paths

def get_protected_plex_data():
    """Finds all saved playlists and bundles their file paths to protect them from deletion."""
    if not PLEX_TOKEN:
        return {}
    console.print("[cyan]Checking Plex for 'saved' playlists...[/cyan]")
    try:
        playlists = get_existing_playlists()
        protected_data = {}
        for title, info in playlists.items():
            if info["is_saved"]:
                console.print(f" [green]✓[/green] Found saved playlist in Plex: '{title}'")
                paths = get_playlist_items(info["ratingKey"])
                protected_data[title] = {
                    "ratingKey": info["ratingKey"],
                    "paths": paths
                }
        return protected_data
    except Exception as e:
        console.print(f"[red]Could not fetch protected playlists: {e}[/red]")
        return {}

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
        console.print(f"    [red]Failed! Plex Error: {response.text.strip()}[/red]")
        return False

def sync_to_plex(protected_data=None):
    if not PLEX_TOKEN:
        console.print("[yellow]PLEX_TOKEN not found in .env. Skipping Plex API sync.[/yellow]")
        return
    if protected_data is None:
        protected_data = {}

    try:
        console.print(f"\n[cyan]--- Starting Plex API Sync ---[/cyan]")
        console.print(f"[dim]Connecting to Plex at {PLEX_URL}...[/dim]")
        section_id = get_section_id()
        if not section_id:
            console.print(f"[red]Could not find a library named '{PLEX_LIBRARY_NAME}'.[/red]")
            return

        console.print(f"[cyan]Triggering library scan for '{PLEX_LIBRARY_NAME}'...[/cyan]")
        trigger_scan(section_id)
        
        # Give Plex time to ingest the files
        console.print("[yellow]Waiting 30 seconds for Plex to process the new MP3 files...[/yellow]")
        time.sleep(30)

        console.print("[cyan]Fetching existing Plex playlists...[/cyan]")
        existing_playlists = get_existing_playlists()

        # 1. Delete unprotected playlists
        for pl_title, info in existing_playlists.items():
            if info["is_saved"]:
                console.print(f" -> [green]Preserving saved Plex playlist:[/green] '{pl_title}'")
                continue
            else:
                console.print(f" -> [yellow]Deleting old Plex playlist:[/yellow] '{pl_title}'")
                delete_playlist(info["ratingKey"])

        # 2. Upload M3Us
        m3u_files = glob.glob(os.path.join(PLAYLISTS_DIR, "*.m3u"))
        for m3u_file in m3u_files:
            m3u_name = os.path.basename(m3u_file)
            playlist_title = os.path.splitext(m3u_name)[0]

            # If the user saved this playlist, do not upload a new M3U or it will duplicate/overwrite it
            if playlist_title in protected_data:
                console.print(f" -> [yellow]Skipping M3U upload[/yellow] for '{playlist_title}' because it is marked as 'save' in Plex.")
                continue

            console.print(f" -> [cyan]Uploading new M3U to Plex:[/cyan] '{playlist_title}'")
            success = upload_m3u(section_id, m3u_name)
            if success:
                console.print(f"    [green]Success![/green]")

        console.print("[bold green]Plex API Sync Complete![/bold green]\n")
        
    except Exception as e:
        console.print(f"[bold red]Plex sync failed:[/bold red] {e}")

if __name__ == "__main__":
    sync_to_plex()