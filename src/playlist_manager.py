# ./src/playlist_manager.py
import os
import re
from ytmusicapi import YTMusic
from config import PLAYLIST_IDS, MAX_SONGS_PER_PLAYLIST

AUTH_FILE = '/app/browser.json'

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

def get_auto_feed_playlists():
    auto_playlists = {}
    try:
        print("Scanning YouTube Music Home screen for Feed playlists...")
        home_shelves = yt.get_home(limit=10)
        
        for shelf in home_shelves:
            title = shelf.get('title', '').lower()
            
            if 'mixed for you' in title or 'from the community' in title:
                count = 0
                for item in shelf.get('contents', []):
                    pid = item.get('playlistId', '')
                    if pid and pid not in auto_playlists:
                        # Memorize the actual title from the home screen
                        mix_title = item.get('title', 'Unknown Mix')
                        auto_playlists[pid] = mix_title
                        print(f" -> Found: {mix_title}")
                        count += 1
                        
                    if count >= 6:
                        break
    except Exception as e:
        print(f"Could not auto-fetch home feeds: {e}")
    return auto_playlists

def get_library_playlists():
    lib_playlists = {}
    try:
        print("Fetching saved playlists from your Library...")
        playlists = yt.get_library_playlists(limit=50)
        for p in playlists:
            if 'playlistId' in p:
                lib_playlists[p['playlistId']] = p.get('title', 'Unknown Playlist')
                print(f" -> Found in Library: {p.get('title', 'Unknown Playlist')}")
    except Exception as e:
        print(f"Could not fetch library playlists: {e}")
    return lib_playlists

def get_playlist_tracks():
    tracks_to_process = []
    
    # Use a dictionary to map IDs to their human-readable titles
    playlists_map = {}
    for raw_pid in PLAYLIST_IDS:
        playlists_map[extract_playlist_id(raw_pid)] = None
        
    if os.path.exists(AUTH_FILE):
        playlists_map.update(get_auto_feed_playlists())
        playlists_map.update(get_library_playlists())

    print(f"\nTotal unique playlists to process: {len(playlists_map)}\n")
    
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