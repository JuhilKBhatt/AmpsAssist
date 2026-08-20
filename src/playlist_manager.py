# ./src/playlist_manager.py
import os
import re
from ytmusicapi import YTMusic
from config import PLAYLIST_IDS, MAX_SONGS_PER_PLAYLIST

import json

AUTH_FILE = '/app/browser.json'
COOKIES_FILE = '/app/cookies.txt'

def sync_cookies_to_browser_json():
    """Generates browser.json from cookies.txt so the user only needs one auth file."""
    if not os.path.exists(COOKIES_FILE):
        return
        
    # Only update if cookies.txt is newer than browser.json, or browser.json doesn't exist
    if os.path.exists(AUTH_FILE) and os.path.getmtime(AUTH_FILE) >= os.path.getmtime(COOKIES_FILE):
        return
        
    print("New cookies.txt detected! Converting to browser.json automatically...")
    cookie_str = []
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#HttpOnly_"):
                    line = line[10:]
                elif line.startswith("#") or not line:
                    continue
                    
                parts = line.split("\t")
                if len(parts) >= 7:
                    name = parts[5]
                    value = parts[6]
                    cookie_str.append(f"{name}={value}")
                    
        cookie_header = "; ".join(cookie_str)
        
        # ytmusicapi requires the word SAPISIDHASH in authorization to trigger Browser auth type
        browser_json = {
            "cookie": cookie_header,
            "x-origin": "https://music.youtube.com",
            "authorization": "SAPISIDHASH dummy",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept-language": "en-US,en;q=0.9"
        }
        
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(browser_json, f, indent=4)
        print("Successfully generated browser.json from cookies.txt!")
    except Exception as e:
        print(f"Failed to parse cookies.txt: {e}")

sync_cookies_to_browser_json()

yt_unauth = YTMusic()

if os.path.exists(AUTH_FILE):
    print("Logged in: Using authenticated Browser session.")
    yt = YTMusic(AUTH_FILE)
else:
    print("WARNING: Running unauthenticated. Private/Feed playlists will fail.")
    yt = yt_unauth

def extract_playlist_id(url_or_id):
    match = re.search(r"[?&]list=([^&]+)", url_or_id)
    return match.group(1) if match else url_or_id

from rich.console import Console
console = Console()

def get_auto_feed_playlists():
    auto_playlists = {}
    try:
        console.print("[cyan]Scanning YouTube Music Home screen for Feed playlists...[/cyan]")
        home_shelves = yt.get_home(limit=10)
        
        for shelf in home_shelves:
            title = shelf.get('title', '').lower()
            
            if 'mixed for you' in title:
                for item in shelf.get('contents', []):
                    pid = item.get('playlistId', '')
                    mix_title = item.get('title', 'Unknown Mix')
                    # Only download the specific mixes the user requested
                    if mix_title.lower() in ['my supermix', 'my mix 1']:
                        if pid and pid not in auto_playlists:
                            auto_playlists[pid] = mix_title
                            console.print(f" [green]✓ Found:[/green] {mix_title}")
                            
            elif 'from the community' in title:
                count = 0
                for item in shelf.get('contents', []):
                    pid = item.get('playlistId', '')
                    if pid and pid not in auto_playlists:
                        mix_title = item.get('title', 'Unknown Mix')
                        auto_playlists[pid] = mix_title
                        console.print(f" [green]✓ Found:[/green] {mix_title}")
                        count += 1
                        
                    if count >= 6:
                        break
    except Exception as e:
        console.print(f"[red]Could not auto-fetch home feeds: {e}[/red]")
    return auto_playlists

def get_library_playlists():
    lib_playlists = {}
    try:
        console.print("[cyan]Fetching saved playlists from your Library...[/cyan]")
        playlists = yt.get_library_playlists(limit=50)
        for p in playlists:
            if 'playlistId' in p:
                lib_playlists[p['playlistId']] = p.get('title', 'Unknown Playlist')
                console.print(f" [green]✓ Found in Library:[/green] {p.get('title', 'Unknown Playlist')}")
    except Exception as e:
        console.print(f"[red]Could not fetch library playlists: {e}[/red]")
    return lib_playlists

def get_playlist_tracks():
    tracks_to_process = []
    
    # Use a dictionary to map IDs to their human-readable titles
    playlists_map = {}
    
    def normalize_pid(pid):
        return pid[2:] if pid.startswith('VL') else pid

    for raw_pid in PLAYLIST_IDS:
        pid = extract_playlist_id(raw_pid)
        playlists_map[normalize_pid(pid)] = None
        
    if os.path.exists(AUTH_FILE):
        for pid, title in get_auto_feed_playlists().items():
            playlists_map[normalize_pid(pid)] = title
            
        for pid, title in get_library_playlists().items():
            norm_pid = normalize_pid(pid)
            if norm_pid not in playlists_map or not playlists_map[norm_pid]:
                playlists_map[norm_pid] = title

    console.print(f"\n[bold blue]Total unique playlists to process: {len(playlists_map)}[/bold blue]\n")
    
    for pid, known_title in playlists_map.items():
        try:
            tracks = []
            
            # Default to the known title if we have it!
            playlist_name = known_title if known_title else f"Playlist_{pid}"

            if pid.startswith('RD'):
                res = yt.get_watch_playlist(playlistId=pid, limit=MAX_SONGS_PER_PLAYLIST)
                tracks = res.get('tracks', [])
                
                # Only try to grab the title from the response if we don't already have it
                if not known_title and res.get('title'):
                    playlist_name = res.get('title')
            else:
                try:
                    res = yt.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                    tracks = res.get('tracks', [])
                    if not known_title:
                        playlist_name = res.get('title', playlist_name)
                except Exception as e:
                    if "400" in str(e) or "404" in str(e):
                        res = yt_unauth.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                        tracks = res.get('tracks', [])
                        if not known_title:
                            playlist_name = res.get('title', playlist_name)
                    else:
                        raise e

            # Clean up YouTube's weird formatting for Supermixes
            if playlist_name.startswith("Playlist_RD"):
                playlist_name = "My Supermix" # Ultimate fallback

            for track in tracks[:MAX_SONGS_PER_PLAYLIST]:
                title = track.get('title', 'Unknown Title')
                artists = ", ".join([a['name'] for a in track.get('artists', []) if 'name' in a])
                album = track.get('album', {}).get('name') if track.get('album') else 'Unknown Album'
                
                tracks_to_process.append({
                    'video_id': track['videoId'],
                    'title': title,
                    'artist': artists,
                    'album': album,
                    'playlist_name': playlist_name
                })
        except Exception as e:
            print(f"Error fetching playlist {pid}: {e}")
            
    return tracks_to_process