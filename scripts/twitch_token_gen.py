# import requests
# import os

# # Set up the OAuth token endpoint URL
# oauth_url = "https://id.twitch.tv/oauth2/token"

# # Set up the OAuth token endpoint request parameters
# params = {
#     "grant_type": "client_credentials",
#     "client_id": os.environ["TWITCH_CLIENT_ID"],
#     "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
#     "scope": "analytics:read:extensions user:edit user:read:email clips:edit bits:read analytics:read:games user:edit:broadcast user:read:broadcast chat:read chat:edit channel:moderate channel:read:subscriptions whispers:read whispers:edit moderation:read channel:read:redemptions channel:edit:commercial channel:read:hype_train channel:read:stream_key channel:manage:extensions channel:manage:broadcast user:edit:follows channel:manage:redemptions channel:read:editors channel:manage:videos user:read:blocked_users user:manage:blocked_users user:read:subscriptions user:read:follows channel:manage:polls channel:manage:predictions channel:read:polls channel:read:predictions moderator:manage:automod channel:manage:schedule channel:read:goals moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:read:chat_settings moderator:manage:chat_settings channel:manage:raids moderator:manage:announcements moderator:manage:chat_messages user:manage:chat_color channel:manage:moderators channel:read:vips channel:manage:vips user:manage:whispers channel:read:charity moderator:read:chatters moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts moderator:read:followers channel:read:guest_star channel:manage:guest_star moderator:read:guest_star moderator:manage:guest_star",
# }

# # Send the OAuth token endpoint request and parse the response
# response = requests.post(oauth_url, params=params)
# response_data = response.json()
# print(response_data)

# # Extract the access token from the response data
# access_token = response_data["access_token"]

# # Print the access token to confirm that it was successfully generated
# print(f"Access token: {access_token}")

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import ssl
import os
import requests
from dotenv import load_dotenv

load_dotenv()

host = "localhost"
port = 3000
redirect_uri = f"https://{host}:{port}/"

code = None


class HandleRequests(BaseHTTPRequestHandler):
    keep_running = True

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        global code

        self._set_headers()

        path = urlparse(self.path)

        if not path.query:
            # If there's no auth code, keep serving the web page.
            request_payload = {
                "client_id": os.environ["TWITCH_CLIENT_ID"],
                "force_verify": "false",
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "analytics:read:extensions user:edit user:read:email clips:edit bits:read analytics:read:games user:edit:broadcast user:read:broadcast chat:read chat:edit channel:moderate channel:read:subscriptions whispers:read whispers:edit moderation:read channel:read:redemptions channel:edit:commercial channel:read:hype_train channel:read:stream_key channel:manage:extensions channel:manage:broadcast user:edit:follows channel:manage:redemptions channel:read:editors channel:manage:videos user:read:blocked_users user:manage:blocked_users user:read:subscriptions user:read:follows channel:manage:polls channel:manage:predictions channel:read:polls channel:read:predictions moderator:manage:automod channel:manage:schedule channel:read:goals moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:read:chat_settings moderator:manage:chat_settings channel:manage:raids moderator:manage:announcements moderator:manage:chat_messages user:manage:chat_color channel:manage:moderators channel:read:vips channel:manage:vips user:manage:whispers channel:read:charity moderator:read:chatters moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts moderator:read:followers channel:read:guest_star channel:manage:guest_star moderator:read:guest_star moderator:manage:guest_star",
            }
            encoded_payload = urlencode(request_payload)
            url = "https://id.twitch.tv/oauth2/authorize?" + encoded_payload
            self.wfile.write(
                f'<html><head><body><a href="{url}">Click here to auth with Twitch</a></body></head>'.encode(
                    "utf-8"
                )
            )
        else:
            # If Twitch has provided a code, store it and stop the web server.
            code = parse_qs(path.query)["code"][0]
            print(f"Code: {code}")
            HandleRequests.keep_running = False


access_token = None
refresh_token = None


def get_tokens():
    print("Fetching Twitch tokens")
    # global access_token
    # global refresh_token

    url = "https://id.twitch.tv/oauth2/token"
    request_payload = {
        "client_id": os.environ["TWITCH_CLIENT_ID"],
        "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
        "grant_type": "authorization_code",
        "code": os.environ["auth_code"],
        "redirect_uri": redirect_uri,
    }

    r = requests.post(url, data=request_payload).json()
    try:
        access_token = r["access_token"]
        refresh_token = r["refresh_token"]
        print(f"Access token: {access_token}")
        print(f"Refresh token: {refresh_token}")
    except:
        print("Unexpected response on redeeming auth code:")
        print(r)


# Authorisation Code Flow
# Launch HTTP Server, listen for request, direct user to Twitch,
# listen for response.
# THIS PART REQUIRES TO HAVE .pem FILES:  openssl req -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out cert.pem -keyout key.pem
def auth_code_flow():
    httpd = HTTPServer((host, port), HandleRequests)
    httpd.socket = ssl.wrap_socket(
        httpd.socket, keyfile="key.pem", certfile="cert.pem", server_side=True
    )

    print(f"Please open your browser at {redirect_uri}")

    # Keep listening until we handle a post request
    while HandleRequests.keep_running:
        httpd.handle_request()


# auth_code_flow()
# get_tokens()
