import requests
import os
from .refresh import Refresh


class FetchSong:
    def __init__(self):
        self.user_id = os.environ["SPOTIFY_USER_ID"]
        self.spotify_token = ""

    def spotify_fetch_track(self):
        SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'
        
        response = requests.get(
            SPOTIFY_GET_CURRENT_TRACK_URL,
            headers={
                "Authorization": f"Bearer {self.spotify_token}",
                "Content-Type": "application/json"
            }
        )
        json_resp = response.json()

        track_id = json_resp['item']['id']
        track_name = json_resp['item']['name']
        artists = [artist for artist in json_resp['item']['artists']]

        link = json_resp['item']['external_urls']['spotify']

        artist_names = ', '.join([artist['name'] for artist in artists])

        current_track_info = {
            "id": track_id,
            "track_name": track_name,
            "artists": artist_names,
            "link": link
        }

        return current_track_info

    def call_refresh(self):

        print("Refreshing token")

        refreshCaller = Refresh()

        self.spotify_token = refreshCaller.refresh()

a = Refresh()
a.refresh()