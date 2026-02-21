# ./src/playlist_manager.py
from ytmusicapi import YTMusic
from config import PLAYLIST_IDS, MAX_SONGS_PER_PLAYLIST

# Initialize YouTube Music API
yt = YTMusic()

def get_playlist_tracks():
    """Fetches track metadata from the configured playlists."""
    tracks_to_process = []
    
    for pid in PLAYLIST_IDS:
        try:
            playlist = yt.get_playlist(pid, limit=MAX_SONGS_PER_PLAYLIST)
            playlist_name = playlist['title']
            
            # Grab up to the max specified limit
            for track in playlist['tracks'][:MAX_SONGS_PER_PLAYLIST]:
                tracks_to_process.append({
                    'video_id': track['videoId'],
                    'title': track['title'],
                    'playlist_name': playlist_name
                })
        except Exception as e:
            print(f"Error fetching playlist {pid}: {e}")
            
    return tracks_to_process