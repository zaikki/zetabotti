import requests
from urllib.parse import urlencode
import base64
import webbrowser
import os


client_id="get_it_from_dev_spotify_website"
client_secret="get_it_from_dev_spotify_website"
callback_uri="http://localhost:7777/callback"
spotify_authorization_code="endcoded_client_id_client_secret"

auth_headers = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": callback_uri,
    "scope": "user-library-read user-read-currently-playing"
}


def spotify_generate_access_token():
    """THIS GENERATES ACCESS TOKEN"""
    # webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))


    encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")

    token_headers = {
        "Authorization": "Basic " + encoded_credentials,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token_data = {
        "grant_type": "authorization_code",
        "code": spotify_authorization_code,
        "redirect_uri": callback_uri,
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    #token = r.json()["access_token"]
    print(r.json())

    

spotify_generate_access_token()