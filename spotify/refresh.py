import requests
import json
import os

refresh_token = os.environ["SPOTIFY_REFRESH_TOKEN"]
base_64 = os.environ["SPOTIFY_AUTHORIZATION_TOKEN"]


class Refresh:
    def __init__(self):
        self.refresh_token = refresh_token
        self.base_64 = base_64

    def refresh(self):
        query = "https://accounts.spotify.com/api/token"

        response = requests.post(
            query,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={"Authorization": "Basic " + base_64},
        )

        response_json = response.json()
        return (response_json["access_token"], response_json)
        #return response_json


a = Refresh()
a.refresh()
