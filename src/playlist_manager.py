# ./src/playlist_manager.py
import os
import re
from ytmusicapi import YTMusic, OAuthCredentials
from config import PLAYLIST_IDS, MAX_SONGS_PER_PLAYLIST

AUTH_FILE = '/app/oauth.json'

# Grab credentials securely from Docker environment
client_id = os.getenv('YTM_CLIENT_ID')
client_secret = os.getenv('YTM_CLIENT_SECRET')

# Initialize an unauthenticated fallback client (crucial for bypassing the OAuth 400 bug)
yt_unauth = YTMusic()

# Auth Check: Initialize Authenticated YouTube Music API
if os.path.exists(AUTH_FILE) and client_id and client_secret:
    print("Logged in: Using authenticated YTMusic session.")
    yt = YTMusic(
        AUTH_FILE, 
        oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret)
    )
else:
    print("WARNING: Running unauthenticated. Private/Feed playlists will fail.")
    yt = yt_unauth

def extract_playlist_id(url_or_id):
    """Extracts the playlist ID from a full YouTube URL."""
    match = re.search(r"[?&]list=([^&]+)", url_or_id)
    return match.group(1) if match else url_or_id

def get_playlist_tracks():
    """Fetches track metadata from the configured playlists."""
    tracks_to_process = []
    
    for raw_pid in PLAYLIST_IDS:
        pid = extract_playlist_id(raw_pid)
        try:
            tracks = []
            playlist_name = f"Playlist_{pid}"

            # 1. YouTube Feed / Mix Playlists (IDs starting with RD)
            if pid.startswith('RD'):
                print(f"Fetching Feed/Mix Playlist: {pid}")
                res = yt.get_watch_playlist(playlistId=pid, limit=MAX_SONGS_PER_PLAYLIST)
                tracks = res.get('tracks', [])
                playlist_name = res.get('title', playlist_name)
            
            # 2. Standard Playlists (IDs starting with PL)
            else:
                try:
                    res = yt.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                    tracks = res.get('tracks', [])
                    playlist_name = res.get('title', playlist_name)
                except Exception as e:
                    # Catch the known OAuth HTTP 400 Bug and fallback to unauthenticated
                    if "400" in str(e) or "404" in str(e):
                        print(f"OAuth blocked fetching {pid}. Falling back to unauthenticated fetch...")
                        res = yt_unauth.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
                        tracks = res.get('tracks', [])
                        playlist_name = res.get('title', playlist_name)
                    else:
                        raise e

            # Process the tracks
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