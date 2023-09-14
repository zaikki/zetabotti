import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import logging

SCOPE = "user-library-read user-read-currently-playing user-read-playback-state user-modify-playback-state user-read-private"
# logger = logging.getLogger('bot_logger')
logger = logging.getLogger(__name__)


class Spotify:
    # init method or constructor
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=SCOPE,
                open_browser=False,
                redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                show_dialog=True,
                cache_path=".token.txt",
            )
        )

    def spotify_current_track(self):
        json_resp = self.sp.current_user_playing_track()
        if json_resp == None:
            return
        current_track_info = {}
        try:
            is_playing = json_resp["is_playing"]
            track_id = json_resp["item"]["id"]
            track_name = json_resp["item"]["name"]
            artists = [artist for artist in json_resp["item"]["artists"]]
            link = json_resp["item"]["external_urls"]["spotify"]
            artist_names = ", ".join([artist["name"] for artist in artists])
            current_track_info = {
                "is_playing": is_playing,
                "id": track_id,
                "track_name": track_name,
                "artists": artist_names,
                "link": link,
            }
        except Exception as e:
            logger.info(f"An exception occurred: {e}")

        return current_track_info

    def spotify_add_song_to_queue(self, song_request_from_user):
        added_song = {}
        try:
            self.sp.add_to_queue(song_request_from_user)
            added_song = song_request_from_user
        except Exception as e:
            logger.info(f"An exception occurred: {e}")
            return e
        return added_song

    def spotify_get_song_info(self, song):
        json_resp = self.sp.track(song)
        track_info = {}
        try:
            artists = [artist["name"] for artist in json_resp["album"]["artists"]]
            track_id = json_resp["id"]
            track_name = json_resp["name"]
            link = json_resp["external_urls"]["spotify"]
            artist_names = ", ".join([artist for artist in artists])

            track_info = {
                "id": track_id,
                "track_name": track_name,
                "artists": artist_names,
                "link": link,
            }
        except Exception as e:
            logger.info(f"An exception occurred: {e}")

        return track_info

    def spotify_search_song(self, song_request):
        if isinstance(song_request, tuple):
            song_request = " ".join(song_request)
        print(song_request)
        result = self.sp.search(q=f"{song_request}")
        if len(result["tracks"]["items"]) == 0:
            logger.info(f"We did not find any songs! With request {song_request}")
            return f"We did not find any songs! With request {song_request}"
        else:
            logger.info(f"Found song: {result['tracks']['items'][0]['id']}")
            return result["tracks"]["items"][0]["id"]
