import requests
import os

# Set up the OAuth token endpoint URL
oauth_url = "https://id.twitch.tv/oauth2/token"

# Set up the OAuth token endpoint request parameters
params = {
    "grant_type": "client_credentials",
    "client_id": os.environ["TWITCH_CLIENT_ID"],
    "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
    "scope": "analytics:read:extensions user:edit user:read:email clips:edit bits:read analytics:read:games user:edit:broadcast user:read:broadcast chat:read chat:edit channel:moderate channel:read:subscriptions whispers:read whispers:edit moderation:read channel:read:redemptions channel:edit:commercial channel:read:hype_train channel:read:stream_key channel:manage:extensions channel:manage:broadcast user:edit:follows channel:manage:redemptions channel:read:editors channel:manage:videos user:read:blocked_users user:manage:blocked_users user:read:subscriptions user:read:follows channel:manage:polls channel:manage:predictions channel:read:polls channel:read:predictions moderator:manage:automod channel:manage:schedule channel:read:goals moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:read:chat_settings moderator:manage:chat_settings channel:manage:raids moderator:manage:announcements moderator:manage:chat_messages user:manage:chat_color channel:manage:moderators channel:read:vips channel:manage:vips user:manage:whispers channel:read:charity moderator:read:chatters moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts moderator:read:followers channel:read:guest_star channel:manage:guest_star moderator:read:guest_star moderator:manage:guest_star",
}

# Send the OAuth token endpoint request and parse the response
response = requests.post(oauth_url, params=params)
response_data = response.json()
print(response_data)

# Extract the access token from the response data
access_token = response_data["access_token"]

# Print the access token to confirm that it was successfully generated
print(f"Access token: {access_token}")


