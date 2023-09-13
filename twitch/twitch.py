import requests
import logging
import os


logger = logging.getLogger(__name__ + ".twitch.oauth")

STREAMER_CHANNEL = os.environ["TWITCH_CHANNEL"]
STREAMER_CHANNEL_ID = os.environ["TWITCH_STREAMER_USER_ID"]

TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]


class TwitchChannelPoint:
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...
        self.bot_access_token = self.bot_access_token
        self.bot_refresh_token = self.bot_refresh_token
        self.stream_access_token = self.stream_access_token
        self.stream_refresh_token = self.stream_refresh_token
        self._parent = self

    def create_channel_point_reward(
        self, title, cost, prompt, user_input_required, background_color
    ):
        # Define the API endpoint URL
        url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
        print(f"create reward with token: {self.bot_access_token}")
        # Define the request headers
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.bot_access_token}",
        }
        # Define the request payload with reward information
        data = {
            "broadcaster_id": STREAMER_CHANNEL_ID,
            "title": title,
            "cost": cost,
            "prompt": prompt,
            "is_user_input_required": user_input_required,
            "background_color": background_color,
        }

        try:
            # Send a POST request to create the custom reward
            response = requests.post(url, headers=headers, json=data)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                reward_data = response.json()
                self.twitch_song_reward_id = reward_data.get("data", [])[0].get("id")
                logger.info(
                    f"Custom reward created with ID: {self.twitch_song_reward_id}"
                )
            elif (
                response.status_code == 400
                and response.json()["message"]
                == "CREATE_CUSTOM_REWARD_DUPLICATE_REWARD"
            ):
                logger.info(
                    f"Channel reward already exists with id {self.twitch_song_reward_id}"
                )
                return
            else:
                logger.info(
                    f"Failed to create custom reward. Status code: {response.status_code}"
                )

        except Exception as e:
            logger.info(f"An error occurred: {e}")


class TwitchOauth:
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...
        self.bot_access_token = self.bot_access_token
        self.bot_refresh_token = self.bot_refresh_token
        self.stream_access_token = self.stream_access_token
        self.stream_refresh_token = self.stream_refresh_token
        self._parent = self

    async def refresh_access_token(self, refresh_token, client_id, client_secret):
        token_refresh_url = "https://id.twitch.tv/oauth2/token"
        refresh_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = requests.post(token_refresh_url, data=refresh_params)
        new_token_data = response.json()
        return new_token_data.get("access_token")

    async def check_exp_access_token(self, bot_access_token):
        token_validate_url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"Bearer {bot_access_token}"}

        response = requests.get(token_validate_url, headers=headers)
        response_json = response.json()
        expires_in = response_json.get("expires_in")
        if response.status_code == 401 or expires_in < 300:
            logger.info("Access token is invalid, expired or going to be expired.")
            # logger.info(response.text)  # Print the response content for debugging
            refreshed_token = await self.refresh_access_token(
                self.bot_refresh_token, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
            )
            # Update the access token in the bot instance
            self.bot_access_token = refreshed_token
            return self.bot_access_token
        elif response.status_code == 200:
            logger.info(f"Access token is valid for {expires_in}")
            return self.bot_access_token
        else:
            logger.info(f"Unexpected response: {response.status_code}")

    
