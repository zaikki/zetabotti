# Twitch OAuth Handling

from .config import load_config
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import ssl
import requests
from os.path import exists
import logging

code = None
access_token = None
refresh_token = None

logger = logging.getLogger(__name__)


cfg = load_config()
redirect_uri = f'https://{cfg["server_host"]}:{cfg["server_port"]}/'


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
        # logger.info(f"Incoming request {path}")
        if not path.query:
            request_payload = {
                "client_id": cfg["twitch_client_id"],
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
            code = parse_qs(path.query)["code"][0]
            logger.info(f"Code: {code}")
            HandleRequests.keep_running = False


# Authorisation Code Flow
# Launch HTTP Server, listen for request, direct user to Twitch,
# listen for response.
def auth_code_flow():
    httpd = HTTPServer((cfg["server_host"], cfg["server_port"]), HandleRequests)
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        keyfile="twitch/key.pem",
        certfile="twitch/cert.pem",
        server_side=True,
    )
    logger.info(f"Please open your browser at {redirect_uri}")
    # Keep listening until we handle a post request
    while HandleRequests.keep_running:
        httpd.handle_request()


def read_code():
    global access_token
    global refresh_token
    if exists("twitch/code.json"):
        logger.info("Reading Twitch tokens")
        with open("twitch/code.json", "r") as json_file:
            code = json.load(json_file)
            access_token = code["access_token"]
            refresh_token = code["refresh_token"]
            return True

    return False


def write_code():
    global access_token
    global refresh_token
    with open("twitch/code.json", "w") as json_file:
        logger.info("Writing Twitch tokens")
        json.dump(
            {"access_token": access_token, "refresh_token": refresh_token}, json_file
        )


def validate():
    print("Validating Twitch tokens...", end="")
    url = "https://id.twitch.tv/oauth2/validate"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    expires_in = response_json.get("expires_in")
    if r.status_code == 200:
        response_json = r.json()
        print(f"valid still {expires_in} seconds")
        return True
    elif r.status_code == 401:
        print("invalid")
        return False
    elif expires_in < 300:
        print(f"invalid {expires_in} seconds, so refreshing")
        return False
    else:
        raise Exception(f"Unrecognised status code on validate {r.status_code}")


def get_tokens():
    logger.info("Fetching Twitch tokens")
    global access_token
    global refresh_token
    url = "https://id.twitch.tv/oauth2/token"
    request_payload = {
        "client_id": cfg["twitch_client_id"],
        "client_secret": cfg["twitch_client_secret"],
        "redirect_uri": redirect_uri,
    }
    if code:
        request_payload["grant_type"] = "authorization_code"
        request_payload["code"] = code
    if refresh_token:
        request_payload["grant_type"] = "refresh_token"
        request_payload["refresh_token"] = refresh_token

    r = requests.post(url, data=request_payload).json()
    try:
        access_token = r["access_token"]
        refresh_token = r["refresh_token"]
        logger.info(f"Access token: {access_token}")
        logger.info(f"Refresh token: {refresh_token}")
    except:
        logger.error("Unexpected response on redeeming auth code:")
        logger.error(r)


def oauth():
    if read_code():  # Code exists
        if not validate():
            get_tokens()
    else:
        auth_code_flow()  # User login auth
        get_tokens()
    write_code()

    return access_token
