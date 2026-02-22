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
    auto_ids = []
    try:
        print("Scanning YouTube Music Home screen for Feed playlists...")
        
        # --- THE FIX: Tell YouTube to 'scroll down' and load 10 shelves instead of 3 ---
        home_shelves = yt.get_home(limit=10)
        
        for shelf in home_shelves:
            title = shelf.get('title', '').lower()
            
            print(f"[Debug] The scanner sees shelf: '{shelf.get('title', 'Untitled')}'")
            
            if 'mixed for you' in title or 'from the community' in title:
                print(f"\n[Scanner] Found Target Shelf: '{shelf.get('title')}'")
                
                count = 0
                for item in shelf.get('contents', []):
                    pid = item.get('playlistId', '')
                    if pid and pid not in auto_ids:
                        auto_ids.append(pid)
                        print(f" -> Added: {item.get('title', 'Unknown Mix')}")
                        count += 1
                        
                    if count >= 6:
                        break
    except Exception as e:
        print(f"Could not auto-fetch home feeds: {e}")
    return auto_ids

def get_library_playlists():
    lib_ids = []
    try:
        print("\nFetching saved playlists from your Library...")
        playlists = yt.get_library_playlists(limit=50)
        for p in playlists:
            if 'playlistId' in p:
                lib_ids.append(p['playlistId'])
                print(f" -> Found in Library: {p.get('title', 'Unknown Playlist')}")
    except Exception as e:
        print(f"Could not fetch library playlists: {e}")
    return lib_ids

def get_playlist_tracks():
    tracks_to_process = []
    all_raw_ids = set(PLAYLIST_IDS)
    
    if os.path.exists(AUTH_FILE):
        for pid in get_auto_feed_playlists():
            all_raw_ids.add(pid)
        for pid in get_library_playlists():
            all_raw_ids.add(pid)

    print(f"\nTotal unique playlists to process: {len(all_raw_ids)}\n")
    
    for raw_pid in all_raw_ids:
        pid = extract_playlist_id(raw_pid)
        try:
            tracks = []
            playlist_name = f"Playlist_{pid}"

            if pid.startswith('RD'):
                res = yt.get_watch_playlist(playlistId=pid, limit=MAX_SONGS_PER_PLAYLIST)
                tracks = res.get('tracks', [])
                playlist_name = res.get('title', playlist_name)
            else:
                try:
                    res = yt.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                    tracks = res.get('tracks', [])
                    playlist_name = res.get('title', playlist_name)
                except Exception as e:
                    if "400" in str(e) or "404" in str(e):
                        res = yt_unauth.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                        tracks = res.get('tracks', [])
                        playlist_name = res.get('title', playlist_name)
                    else:
                        raise e

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