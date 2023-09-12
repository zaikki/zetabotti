import os
import logging
import datetime
import twitchio
import requests
from twitchio.ext import commands, pubsub
from spotify.spotify import Spotify
from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.oauth import refresh_access_token

import asyncio
from pprint import pprint
from uuid import UUID

logging.basicConfig(level=logging.INFO)
STREAMER_CHANNEL = os.environ["CHANNEL"]
STREAMER_CHANNEL_ID = os.environ["STREAMER_USER_ID"]
TWITCH_SPOTIFY_REWARD_ID = os.environ["TWITCH_SPOTIFY_REWARD_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
BOT_NICK = os.environ["BOT_NICK"]
BOT_PREFIX = os.environ["BOT_PREFIX"]

TOKEN = os.environ["TMI_TOKEN"]
USER_OAUTH_TOKEN = os.environ["ACCESS_TOKEN"]
USER_CHANNEL_ID = int(STREAMER_CHANNEL_ID)
CLIENT = twitchio.Client(token=TOKEN)
CLIENT.pubsub = pubsub.PubSubPool(CLIENT)





class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(
            token=TOKEN,
            client_id=CLIENT_ID,
            nick=BOT_NICK,
            prefix=BOT_PREFIX,
            initial_channels=[STREAMER_CHANNEL],
        )
    
    # async def event_token_expired(self):
    #     return await super().event_token_expired()

    def refresh_access_token(refresh_token):
        token_refresh_url = "https://id.twitch.tv/oauth2/token"
        refresh_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(token_refresh_url, data=refresh_params)
        new_token_data = response.json()
        return new_token_data.get("access_token")


    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

        USER_OAUTH_TOKEN = self.refresh_access_token(REFRESH_TOKEN)

        topics = [
            pubsub.channel_points(USER_OAUTH_TOKEN)[USER_CHANNEL_ID],
        ]
        await CLIENT.pubsub.subscribe_topics(topics)
        await CLIENT.start()
        
        # twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)

        # target_scope = [AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
        # auth = UserAuthenticator(twitch, target_scope, force_verify=False)
        # # this will open your default browser and prompt you with the twitch verification website
        # token, refresh_token = await auth.authenticate()
        # # add User authentication
        # await twitch.set_user_authentication(token, target_scope, refresh_token)

    #     twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)
    #     new_token, new_refresh_token = await refresh_access_token(REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET)
    #     twitch.app_auth_refresh_callback = self.app_refresh
    #     twitch.user_auth_refresh_callback = self.user_refresh

    #     print(new_token, new_refresh_token)
    #     await self.user_refresh(new_token, new_refresh_token)

    # async def user_refresh(self, token: str, refresh_token: str):
    #     print(f'my new user token is: {token} {refresh_token}')

    # async def app_refresh(self, token: str):
    #     print(f'my new app token is: {token}')

    


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

    async def make_api_request(self, url, params):
        if self.is_token_expired():
            # Refresh the access token
            new_access_token = refresh_access_token(USER_OAUTH_TOKEN)
            # Update the access token in the bot instance
            self.token = new_access_token

        # Make the API request with the updated access token
        response = requests.get(url, params=params, headers={"Client-ID": CLIENT_ID, "Authorization": f"Bearer {self.token}"})
        # Handle the API response here

    def is_token_expired(self):
        # Calculate the expiration time of the token and check if it's about to expire
        expiration_time = datetime.datetime.fromtimestamp(USER_TOKEN_EXPIRATION_TIMESTAMP)
        current_time = datetime.datetime.now()
        return current_time >= expiration_time

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

    # @commands.command(name="addsong")
    # async def add_song(self, ctx: commands.Context, *args):
    #     if "https://open.spotify.com/track/" in args[0]:
    #         song_info_request = sp.spotify_get_song_info(args[0])
    #         sp.spotify_add_song_to_queue(args[0])
    #         spotify_artists_name = song_info_request["artists"]
    #         spotify_track_name = song_info_request["track_name"]
    #         logger.info(
    #             f"Twitch user {ctx.author.name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
    #         )
    #         await ctx.send(
    #             f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
    #         )
    #     else:
    #         result = sp.spotify_search_song(args)
    #         song_info_request = sp.spotify_get_song_info(result)
    #         sp.spotify_add_song_to_queue(result)
    #         spotify_artists_name = song_info_request["artists"]
    #         spotify_track_name = song_info_request["track_name"]
    #         logger.info(
    #             f"Twitch user {ctx.author.name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
    #         )
    #         await ctx.send(
    #             f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
    #         )


    # async def refu_points():
    #     await twitchio.CustomRewardRedemption.refund(token=USER_OAUTH_TOKEN)
    #     #await twitchio.CustomRewardRedemption.refund(token=USER_OAUTH_TOKEN)

    async def send_result_to_chat(self, data):
        await self.streamer_channel.send(data)

    async def event_channel_joined(self, channel: twitchio.Channel):
        if channel.name == STREAMER_CHANNEL:
            self.streamer_channel = channel
            self.streamer_id = STREAMER_CHANNEL_ID

    @CLIENT.event()
    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        pass  # do stuff on bit redemptions

    @CLIENT.event()
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        twitch_channels = await bot.search_channels(query=STREAMER_CHANNEL)
        if (event.reward.id == TWITCH_SPOTIFY_REWARD_ID) and (bot.check_if_channel_is_live(twitch_channels) == True):
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
                await bot.send_result_to_chat(
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
                await bot.send_result_to_chat(
                    data=f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
                )
        elif (event.reward.id == TWITCH_SPOTIFY_REWARD_ID) and (bot.check_if_channel_is_live(twitch_channels) == False):
            await bot.send_result_to_chat(
                    data=f"Channel not live"
                )
            #await bot.refu_points()
            #await twitchio.CustomRewardRedemption.refund(token=USER_OAUTH_TOKEN)
        else:
            logger.info(
                f"We do not have that reward configured: {event.reward.title} {event.reward.id}"
            )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    sp = Spotify()
    bot.run()
