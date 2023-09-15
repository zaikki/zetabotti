import os
import logging
import twitchio
import requests
from twitchio.ext import commands, pubsub, eventsub
from spotify.spotify import Spotify, blacklist

# from twitch.twitch import TwitchOauth, TwitchChannelPoint
from twitch.twitch import TwitchChannelPoint
import asyncio
from twitch.twitch_auth import oauth
from twitch.config import load_config
from typing import List


logging.basicConfig(level=logging.INFO)


STREAMER_CHANNEL = os.environ["TWITCH_CHANNEL"]
STREAMER_CHANNEL_ID = os.environ["TWITCH_STREAMER_USER_ID"]

TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]

TWITCH_SPOTIFY_REWARD_ID = os.environ["TWITCH_SPOTIFY_REWARD_ID"]
TWITCH_BOT_NICK = os.environ["TWITCH_BOT_NICK"]
TWITCH_BOT_PREFIX = os.environ["TWITCH_BOT_PREFIX"]

cfg = load_config()
token = oauth()

CLIENT = twitchio.Client(token=token)
CLIENT.pubsub = pubsub.PubSubPool(CLIENT)


class Bot(commands.Bot):
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...

        ### Initialize tokens
        self.token = oauth()  # Get user token
        # client = commands.Bot.from_client_credentials(client_id='...',
        #                                  client_secret='...')
        
        self.blacklist = blacklist
        self._parent = self
        self.twitch_song_reward_id = TWITCH_SPOTIFY_REWARD_ID
        self.reward_title = "Song request!"
        self.reward_cost = 1
        self.reward_prompt = "Search with Spotify song link or free search"
        self.user_input_required = True
        self.reward_color = "#FF5733"  # Hex color code

        super().__init__(
            token=self.token,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_BOT_NICK,
            prefix=TWITCH_BOT_PREFIX,
            initial_channels=[STREAMER_CHANNEL],
        )


    async def __ainit__(self) -> None:
        
        # self.token = self.event_token_expired()
        topics = [
            pubsub.channel_points(self.token)[int(STREAMER_CHANNEL_ID)],
        ]
        

        try:
            await CLIENT.pubsub.subscribe_topics(topics)
            #await CLIENT.start()
        except twitchio.HTTPException:
            pass

    

    
    # async def pool(self):
    #     # self.loop.create_task(esclient.listen(port="8080"))
    #     print("DOING STUFF")

    #     topics = [
    #         pubsub.channel_points(self.token)[int(STREAMER_CHANNEL_ID)],
    #     ]        

    #     try:
    #         await CLIENT.pubsub.subscribe_topics(topics)
    #         await CLIENT.start()
    #     except twitchio.HTTPException as e:
    #         print(e)
    #         pass


        # @esbot.event()
        # async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        #     # Access the bot instance using the 'bot' variable
        #     await bot.twitch_pubsub_channel_points_handler(event)

        

    async def refresh_token(self):
        while True:
            try:
                # Implement your token refresh logic here
                # For example, you can use your existing refresh_token logic
                new_token = oauth()
                self.token = new_token  # Update self.token with the new token

                # Sleep for 50 minutes (3000 seconds)
                await asyncio.sleep(3000)
            except Exception as e:
                # Handle any exceptions that might occur during token refresh
                print(f"Token refresh failed: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes if refresh fails

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")
        asyncio.create_task(self.refresh_token())
        # self.client = await MyPubSubPool.create_client(self)

        ### Check that access credentials are valid for PubSub
        # await TwitchOauth.check_exp_access_token(self, self.token)
        reward_title = self.reward_title
        reward_cost = self.reward_cost
        reward_prompt = self.reward_prompt
        user_input_required = self.user_input_required
        reward_color = self.reward_color
        TwitchChannelPoint.create_channel_point_reward(
            self,
            reward_title,
            reward_cost,
            reward_prompt,
            user_input_required,
            reward_color,
        )
        # CLIENT = twitchio.Client(token=self.token)
        # CLIENT.pubsub = pubsub.PubSubPool(CLIENT)

        # topics = [
        #     pubsub.channel_points(self.token)[int(STREAMER_CHANNEL_ID)],
        # ]
        # await CLIENT.pubsub.subscribe_topics(topics)
        # await CLIENT.start()

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
            f"Channel is offline! Some commands are disabled like !song"
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

    async def send_result_to_chat(self, data):
        await self.streamer_channel.send(data)

    async def event_channel_joined(self, channel: twitchio.Channel):
        if channel.name != STREAMER_CHANNEL:
            return
        self.streamer_channel = channel
        self.streamer_id = STREAMER_CHANNEL_ID

    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        pass  # do stuff on bit redemptions

    
    # @esbot.event()
    # async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    #     # Access the bot instance using the 'bot' variable
    #     await bot.twitch_pubsub_channel_points_handler(event)

    # Define a separate function to handle the channel points event
    # @event()
    async def twitch_pubsub_channel_points_handler(self, event):
        twitch_channels = await self.search_channels(query=STREAMER_CHANNEL)
        author_name = event.user.name
        arg = event.input
        blacklist = [keyword.lower() for keyword in self.blacklist]
        # Update self.twitch_song_reward_id if a new reward is created
        if (event.reward.title == "Song request!") and (
            event.reward.cost == self.reward_cost
        ):
            self.twitch_song_reward_id = event.reward.id

        if any(word in arg.lower() for word in blacklist):
            logger.info(f"User {author_name} tried to find song with slur words")
            await self.send_result_to_chat(data=f"Dirty song. Get lost.")
            return

        if (event.reward.id == self.twitch_song_reward_id) and (
            bot.check_if_channel_is_live(twitch_channels) == True
        ):
            if "https://open.spotify.com/track/" in arg:
                song_info_request = sp.spotify_get_song_info(arg)
                if song_info_request:
                    logger.info(f"User {author_name} tried to find song with slur words")
                    await self.send_result_to_chat(data=f"Dirty song. Get lost.")
                    return
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
            refund_response = await TwitchChannelPoint.refund_points(
                self,
                event.channel_id,
                event.id,
                event.user.id,
                self.twitch_song_reward_id,
            )
            data_json = refund_response.json()
            data = data_json["data"][0]
            cost = data["reward"]["cost"]
            user_name = data["user_name"]
            user_input = data["user_input"]
            await self.send_result_to_chat(
                data=f"Refunded for user: {user_name}. Point amount: {cost}. Search query was: '{user_input}'."
            )
        else:
            logger.info(
                f"We do not have that reward configured: {event.reward.title} {event.reward.id}"
            )

@CLIENT.event()
async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    # Access the bot instance using the 'bot' variable
    await bot.twitch_pubsub_channel_points_handler(event)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    bot.loop.run_until_complete(bot.__ainit__())
    sp = Spotify()
    # resultti = sp.spotify_get_song_info("https://open.spotify.com/track/5znIVOv7RucpCHGkbonySq?si=b48f7fb0f6954c73")
    # print(resultti)

    bot.run()
