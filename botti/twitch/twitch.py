import requests
import logging
import os
from .twitch_auth import oauth
from dotenv import load_dotenv
from pathlib import Path
from ..config import load_config


logger = logging.getLogger(__name__)
cfg = load_config(".env.json")

STREAMER_CHANNEL = cfg["TWITCH_CHANNEL"]
STREAMER_CHANNEL_ID = cfg["TWITCH_STREAMER_USER_ID"]

TWITCH_CLIENT_ID = cfg["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = cfg["TWITCH_CLIENT_SECRET"]


class TwitchChannelPoint:
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...
        
        
        self.token = oauth() # Get user token

    def create_channel_point_reward(
        self, title, cost, prompt, user_input_required, background_color
    ):
        # Define the API endpoint URL
        url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
        print(f"create reward with token: {self.token}")
        # Define the request headers
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.token}",
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

    async def refund_points(
        self, broadcaster_id, redemption_id, event_user_id, reward_id
    ):
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id={broadcaster_id}&reward_id={reward_id}&id={redemption_id}"
            headers = {
                "Client-Id": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            data = {"status": "CANCELED"}
            response = requests.patch(url, headers=headers, json=data)
            if response.status_code == 200:
                logger.info(f"Refunded channel points for redemption {redemption_id}.")
                return response
            else:
                logger.error(
                    f"Error refunding channel points. Status code: {response.status_code}"
                )
                return response
        except Exception as e:
            logger.error(f"Error refunding channel points: {e}")

    
