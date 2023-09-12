import os
import logging
import twitchio
import requests
from twitchio.ext import commands, pubsub
from spotify.spotify import Spotify



logging.basicConfig(level=logging.INFO)


STREAMER_CHANNEL = os.environ["TWITCH_CHANNEL"]
STREAMER_CHANNEL_ID = os.environ["TWITCH_STREAMER_USER_ID"]
TWITCH_STREAMER_USER_OAUTH_TOKEN = os.environ["TWITCH_ACCESS_TOKEN"]
TWITCH_SPOTIFY_REWARD_ID = os.environ["TWITCH_SPOTIFY_REWARD_ID"]
TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["TWITCH_REFRESH_TOKEN"]
TWITCH_OAUTH_TOKEN = os.environ["TWITCH_OAUTH_TOKEN"]
TWITCH_BOT_NICK = os.environ["TWITCH_BOT_NICK"]
TWITCH_BOT_PREFIX = os.environ["TWITCH_BOT_PREFIX"]
CLIENT = twitchio.Client(token=TWITCH_OAUTH_TOKEN)
CLIENT.pubsub = pubsub.PubSubPool(CLIENT)


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        self.access_token = TWITCH_STREAMER_USER_OAUTH_TOKEN
        self._parent = self
        self.twitch_song_reward_id = TWITCH_SPOTIFY_REWARD_ID
        self.reward_title = "Song request!"
        self.reward_cost = 1
        self.reward_prompt = "Search with Spotify song link or free search"
        self.user_input_required = True
        self.reward_color = "#FF5733"  # Hex color code

        super().__init__(
            token=TWITCH_OAUTH_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_BOT_NICK,
            prefix=TWITCH_BOT_PREFIX,
            initial_channels=[STREAMER_CHANNEL],
        )

        # asyncio.run(self.init_channel_points())

    def create_channel_point_reward(
        self, title, cost, prompt, user_input_required, background_color
    ):
        # Define the API endpoint URL
        url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"

        # Define the request headers
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.access_token}",
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
                logger.info(f"Custom reward created with ID: {self.twitch_song_reward_id}")
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

    async def check_exp_access_token(self, access_token):
        token_validate_url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(token_validate_url, headers=headers)
        response_json = response.json()
        expires_in = response_json.get("expires_in")
        if response.status_code == 401:
            logger.info("Access token is invalid or expired.")
            # logger.info(response.text)  # Print the response content for debugging
            refreshed_token = await self.refresh_access_token(
                REFRESH_TOKEN, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
            )
            # Update the access token in the bot instance
            self.access_token = refreshed_token[0]
            return self.access_token
        elif response.status_code == 200:
            logger.info(f"Access token is valid. For {expires_in}")
            return self.access_token
        else:
            logger.info(f"Unexpected response: {response.status_code}")

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

        ### Check that access credentials are valid for PubSub
        await self.check_exp_access_token(self.access_token)
        reward_title = self.reward_title
        reward_cost = self.reward_cost
        reward_prompt = self.reward_prompt
        user_input_required = self.user_input_required
        reward_color = self.reward_color
        self.create_channel_point_reward(
            reward_title, reward_cost, reward_prompt, user_input_required, reward_color
        )

        topics = [
            pubsub.channel_points(self.access_token)[int(STREAMER_CHANNEL_ID)],
        ]
        await CLIENT.pubsub.subscribe_topics(topics)
        await CLIENT.start()

    def check_if_channel_is_live(self, twitch_channels):
        streamer_channel = list(
            filter(lambda obj: (obj.display_name == STREAMER_CHANNEL), twitch_channels)
        )
        if streamer_channel[0].live == True:
            return True
        else:
            return False

    async def send_channel_offline_notification(self, message):
        return await message.channel.send(
            f"Channel is offline! Some commands are disabled like !song and !addsong"
        )

    async def turn_off_song_queue(self, ctx: commands.Context, que_on_off=False):
        if ctx.author.display_name == STREAMER_CHANNEL:
            logger.info(f"Author was {STREAMER_CHANNEL} and queue is {que_on_off}")
        else:
            logger.info(f"Nasty pleb: {ctx.author.display_name}")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo or message.author.display_name == "StreamElements":
            return

        logger.info(f"{message.author.name}: {message.content}")
        twitch_channels = await self.search_channels(query=STREAMER_CHANNEL)

        is_channel_live = self.check_if_channel_is_live(twitch_channels)
        try:
            if message.author.name == STREAMER_CHANNEL:
                # logger.info(f"User is broadcaster so allowing by pass")
                await self.handle_commands(message)
            elif (is_channel_live is False) and message.content.startswith("!"):
                logger.info(f"{STREAMER_CHANNEL} is NOT live")
                await self.send_channel_offline_notification(message)
            elif (is_channel_live is True) and message.content.startswith("!"):
                await self.handle_commands(message)
        except Exception as e:
            logger.info(f"An exception occurred: {e}")

    @commands.command(name="songqueue")
    async def song_queue_on_off(self, ctx: commands.Context, on_off):
        await self.turn_off_song_queue(ctx, on_off)

    @commands.command(name="song")
    async def current_song(self, ctx: commands.Context):
        current_song = sp.spotify_current_track()
        if (current_song is not None) and (current_song["is_playing"] is True):
            spotify_current_artists = current_song["artists"]
            spotify_current_track_name = current_song["track_name"]
            logger.info(
                f"Twitch user {ctx.author.name} fetched song: {spotify_current_artists} - {spotify_current_track_name}"
            )
            await ctx.send(
                f"Current song is: {spotify_current_artists} - {spotify_current_track_name}"
            )
        elif current_song == None:
            logger.info(f"Spotify not running or playing songs.")
            await ctx.send(f"Spotify not running or playing songs.")
        else:
            logger.info(
                f"Twitch user {ctx.author.name} tried to find songs, but nothing is playing."
            )
            await ctx.send(f"No songs playing!")

    @commands.command(name="searchsong")
    async def search_song(self, ctx: commands.Context, *args):
        search_result = sp.spotify_search_song(args)
        result = f"https://open.spotify.com/track/{search_result}"
        await ctx.send(result)

    async def refund_points(
        self, broadcaster_id, redemption_id, event_user_id, reward_id
    ):
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id={broadcaster_id}&reward_id={reward_id}&id={redemption_id}"
            headers = {
                "Client-Id": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {self.access_token}",
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

    async def send_result_to_chat(self, data):
        await self.streamer_channel.send(data)

    async def event_channel_joined(self, channel: twitchio.Channel):
        if channel.name != STREAMER_CHANNEL:
            return
        self.streamer_channel = channel
        self.streamer_id = STREAMER_CHANNEL_ID

    @CLIENT.event()
    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        pass  # do stuff on bit redemptions

    @CLIENT.event()
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        # Access the bot instance using the 'bot' variable
        await bot.twitch_pubsub_channel_points_handler(event)

    # Define a separate function to handle the channel points event
    async def twitch_pubsub_channel_points_handler(self, event):
        twitch_channels = await self.search_channels(query=STREAMER_CHANNEL)
        # Update self.twitch_song_reward_id if a new reward is created
        if (event.reward.title == "Song request!") and (event.reward.cost == self.reward_cost):
            self.twitch_song_reward_id = event.reward.id

        if (event.reward.id == self.twitch_song_reward_id) and (
            bot.check_if_channel_is_live(twitch_channels) == True
        ):
            author_name = event.user.name
            arg = event.input
            if "https://open.spotify.com/track/" in arg:
                song_info_request = sp.spotify_get_song_info(arg)
                sp.spotify_add_song_to_queue(arg)
                spotify_artists_name = song_info_request["artists"]
                spotify_track_name = song_info_request["track_name"]
                logger.info(
                    f"Twitch user {author_name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
                )
                await self.send_result_to_chat(
                    data=f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
                )
            else:
                result = sp.spotify_search_song(arg)
                song_info_request = sp.spotify_get_song_info(result)
                sp.spotify_add_song_to_queue(result)
                spotify_artists_name = song_info_request["artists"]
                spotify_track_name = song_info_request["track_name"]
                logger.info(
                    f"Twitch user {author_name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
                )
                await self.send_result_to_chat(
                    data=f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
                )
        elif (event.reward.id == self.twitch_song_reward_id) and (
            self.check_if_channel_is_live(twitch_channels) == False
        ):
            await self.send_result_to_chat(data=f"Channel not live")
            refund_response = await self.refund_points(
                event.channel_id, event.id, event.user.id, self.twitch_song_reward_id
            )
            data_json = refund_response.json()
            data = data_json["data"][0]
            cost = data["reward"]["cost"]
            user_name = data["user_name"]
            user_input = data["user_input"]
            await self.send_result_to_chat(
                data=f"Refunded for user {user_name} his {cost}. Search query was: {user_input}"
            )
        else:
            logger.info(
                f"We do not have that reward configured: {event.reward.title} {event.reward.id}"
            )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    sp = Spotify()
    bot.run()
