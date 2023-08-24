import requests
import os
from .refresh import Refresh


class Spotify:
    def __init__(self):
        self.user_id = os.environ["SPOTIFY_USER_ID"]
        self.spotify_token = ""
        self.spotify_response = ""

    def spotify_fetch_track(self):
        spotify_get_current_track_url = (
            "https://api.spotify.com/v1/me/player/currently-playing"
        )
        try:
            response = requests.get(
                spotify_get_current_track_url,
                headers={
                    "Authorization": f"Bearer {self.spotify_token}",
                    "Content-Type": "application/json",
                },
            )
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print(e)
            self.call_refresh()
            response = requests.get(
                spotify_get_current_track_url,
                headers={
                    "Authorization": f"Bearer {self.spotify_token}",
                    "Content-Type": "application/json",
                },
            )
        json_resp = response.json()

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

        return current_track_info

    def add_song_to_queue(self):
        requested_song = (
            "https://open.spotify.com/track/0HlhtIdbSWSKW9DU5sXeFX?si=ac855f6f794646f5"
        )
        splitted_request_song = requested_song.split("/")[-1].split("?")[0]
        print(splitted_request_song)
        spotify_song_queue_url = "https://api.spotify.com/v1/me/player/queue"
        requested_song = f"?uri=spotify%3Atrack%3A{splitted_request_song}"
        print(f"{spotify_song_queue_url}{requested_song}")

        response = requests.post(
            f"{spotify_song_queue_url}{requested_song}",
            headers={
                "Authorization": f"Bearer {self.spotify_token}",
                "Content-Type": "application/json",
            },
        )
        return requested_song
       

    def call_refresh(self):
        print("Refreshing token")
        refreshCaller = Refresh()
        self.spotify_token, self.spotify_response = refreshCaller.refresh()
        


a = Refresh()
a.refresh()
