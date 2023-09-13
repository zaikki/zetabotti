import os
import logging
import twitchio
import requests
from twitchio.ext import commands, pubsub
from spotify.spotify import Spotify
from twitch.twitch import TwitchOauth, TwitchChannelPoint


logging.basicConfig(level=logging.INFO)


STREAMER_CHANNEL = os.environ["TWITCH_CHANNEL"]
STREAMER_CHANNEL_ID = os.environ["TWITCH_STREAMER_USER_ID"]

TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]

TWITCH_BOT_ACCESS_TOKEN = os.environ["TWITCH_BOT_ACCESS_TOKEN"]
TWITCH_BOT_REFRESH_TOKEN = os.environ["TWITCH_BOT_REFRESH_TOKEN"]

### TWITCH_STREAMER_ACCESS_TOKEN and TWITCH_STREAMER_REFRESH_TOKEN are authed with the bot credentials
TWITCH_STREAMER_ACCESS_TOKEN = os.environ["TWITCH_STREAMER_ACCESS_TOKEN"]
TWITCH_STREAMER_REFRESH_TOKEN = os.environ["TWITCH_STREAMER_REFRESH_TOKEN"]

TWITCH_SPOTIFY_REWARD_ID = os.environ["TWITCH_SPOTIFY_REWARD_ID"]
TWITCH_BOT_NICK = os.environ["TWITCH_BOT_NICK"]
TWITCH_BOT_PREFIX = os.environ["TWITCH_BOT_PREFIX"]


class Bot(commands.Bot):
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...
        self.bot_access_token = TWITCH_BOT_ACCESS_TOKEN
        self.bot_refresh_token = TWITCH_BOT_REFRESH_TOKEN
        self.stream_access_token = TWITCH_STREAMER_ACCESS_TOKEN
        self.stream_refresh_token = TWITCH_STREAMER_REFRESH_TOKEN
        self._parent = self
        self.twitch_song_reward_id = TWITCH_SPOTIFY_REWARD_ID
        self.reward_title = "Song request!"
        self.reward_cost = 1
        self.reward_prompt = "Search with Spotify song link or free search"
        self.user_input_required = True
        self.reward_color = "#FF5733"  # Hex color code

        super().__init__(
            token=self.bot_access_token,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_BOT_NICK,
            prefix=TWITCH_BOT_PREFIX,
            initial_channels=[STREAMER_CHANNEL],
        )

        # asyncio.run(self.init_channel_points())

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

        ### Check that access credentials are valid for PubSub
        await TwitchOauth.check_exp_access_token(self, self.bot_access_token)
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
        CLIENT = twitchio.Client(token=self.bot_access_token)
        CLIENT.pubsub = pubsub.PubSubPool(CLIENT)

        topics = [
            pubsub.channel_points(self.bot_access_token)[int(STREAMER_CHANNEL_ID)],
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

    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        # Access the bot instance using the 'bot' variable
        await bot.twitch_pubsub_channel_points_handler(event)

    # Define a separate function to handle the channel points event
    async def twitch_pubsub_channel_points_handler(self, event):
        twitch_channels = await self.search_channels(query=STREAMER_CHANNEL)
        # Update self.twitch_song_reward_id if a new reward is created
        if (event.reward.title == "Song request!") and (
            event.reward.cost == self.reward_cost
        ):
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
            refund_response = await TwitchChannelPoint.refund_points(self,
                event.channel_id, event.id, event.user.id, self.twitch_song_reward_id
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


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    sp = Spotify()
    bot.run()


# from twitchAPI import Twitch
# from twitchAPI.oauth import UserAuthenticator
# from twitchAPI.types import AuthScope, ChatEvent
# from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
# import asyncio
# from twitchAPI.oauth import refresh_access_token


# APP_ID = os.environ["TWITCH_CLIENT_ID"]
# APP_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
# USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
# TARGET_CHANNEL = os.environ["TWITCH_CHANNEL"]
# TARGET_CHANNEL_ID = os.environ["TWITCH_STREAMER_USER_ID"]


# # this will be called when the event READY is triggered, which will be on bot start
# async def on_ready(ready_event: EventData):
#     print('Bot is ready for work, joining channels')
#     # join our target channel, if you want to join multiple, either call join for each individually
#     # or even better pass a list of channels as the argument
#     await ready_event.chat.join_room(TARGET_CHANNEL)
#     # you can do other bot initialization things in here


# # this will be called whenever a message in a channel was send by either the bot OR another user
# async def on_message(msg: ChatMessage):
#     print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')


# # this will be called whenever someone subscribes to a channel
# async def on_sub(sub: ChatSub):
#     print(f'New subscription in {sub.room.name}:\\n'
#           f'  Type: {sub.sub_plan}\\n'
#           f'  Message: {sub.sub_message}')


# # this will be called whenever the !reply command is issued
# async def test_command(cmd: ChatCommand):
#     if len(cmd.parameter) == 0:
#         await cmd.reply('you did not tell me what to reply with')
#     else:
#         await cmd.reply(f'{cmd.user.name}: {cmd.parameter}')


# # this is where we set up the bot
# async def run():
#     # set up twitch api instance and add user authentication with some scopes
#     twitch = await Twitch(APP_ID, APP_SECRET)
#     # auth = UserAuthenticator(twitch, USER_SCOPE)
#     # token, refresh_token = await auth.authenticate()
#     new_token, new_refresh_token = await refresh_access_token(os.environ["TWITCH_STREAMER_REFRESH_TOKEN"], twitch.app_id, twitch.app_secret)

#     await twitch.set_user_authentication(new_token, USER_SCOPE, new_refresh_token)

#     # create chat instance
#     chat = await Chat(twitch)

#     # register the handlers for the events you want

#     # listen to when the bot is done starting up and ready to join channels
#     chat.register_event(ChatEvent.READY, on_ready)
#     # listen to chat messages
#     chat.register_event(ChatEvent.MESSAGE, on_message)
#     # listen to channel subscriptions
#     chat.register_event(ChatEvent.SUB, on_sub)
#     # there are more events, you can view them all in this documentation

#     # you can directly register commands and their handlers, this will register the !reply command
#     chat.register_command('reply', test_command)


#     # we are done with our setup, lets start this bot up!
#     chat.start()

#     # lets run till we press enter in the console
#     try:
#         input('press ENTER to stop\n')
#     finally:
#         # now we can close the chat bot and the twitch api client
#         chat.stop()
#         await twitch.close()


# if __name__ == "__main__":
#     logger = logging.getLogger(__name__)
#     asyncio.run(run())
