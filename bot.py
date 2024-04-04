import logging
import twitchio
from twitchio.ext import commands, pubsub
from botti.spotify.spotify import Spotify, blacklist
from botti.twitch.twitch import TwitchChannelPoint
from botti.eft_api.goons import Goons
import asyncio
from botti.twitch.twitch_auth import oauth
from botti.config import load_config


logging.basicConfig(level=logging.INFO)


cfg_env_config = load_config("./.env.json")
TWITCH_STREAMER_CHANNEL = cfg_env_config["TWITCH_STREAMER_CHANNEL"]
TWITCH_STREAMER_USER_ID = cfg_env_config["TWITCH_STREAMER_USER_ID"]
TWITCH_CLIENT_ID = cfg_env_config["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = cfg_env_config["TWITCH_CLIENT_SECRET"]
TWITCH_SPOTIFY_REWARD_ID = cfg_env_config["TWITCH_SPOTIFY_REWARD_ID"]
TWITCH_BOT_NICK = cfg_env_config["TWITCH_BOT_NICK"]
TWITCH_BOT_PREFIX = cfg_env_config["TWITCH_BOT_PREFIX"]

TWITCH_BOT_ACCESS_TOKEN = cfg_env_config["TWITCH_BOT_ACCESS_TOKEN"]

ALLOWED_COMMANDS = ["!goons"]

class AuthClientError(Exception):
    pass


class Bot(commands.Bot):
    def __init__(self):
        ### Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        ### prefix can be a callable, which returns a list of strings or a string...
        ### initial_channels can also be a callable which returns a list of strings...

        ### Initialize tokens
        self.token = oauth()
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
            initial_channels=[TWITCH_STREAMER_CHANNEL],
        )
        # asyncio.create_task(self.refresh_token())

    async def __ainit__(self):
        asyncio.create_task(self.refresh_token())
        print("After create task")
        CLIENT = twitchio.Client(token=self.token)
        print("After client creation")
        CLIENT.pubsub = pubsub.PubSubPool(CLIENT)
        print("After pubsub creation")
        topics = [
            pubsub.channel_points(self.token)[TWITCH_STREAMER_USER_ID],
        ]
        try:
            await CLIENT.pubsub.subscribe_topics(topics)
            print("Inside pubsub CLIENT subscribe")
        except twitchio.HTTPException:
            print("we are in http expection, need to refresh something")
            pass
        return CLIENT

    async def refresh_token(self):
        while True:
            try:
                # Implement your token refresh logic here
                # For example, you can use your existing refresh_token logic
                new_token = oauth()
                self.token = new_token  # Update self.token with the new token

                # Sleep for a certain duration (e.g., 50 minutes)
                await asyncio.sleep(3000)
            except Exception as e:
                # Handle any exceptions that might occur during token refresh
                print(f"Token refresh failed: {e}")
                await asyncio.sleep(300)

            # try:
            #     # Attempt to reconnect
            #     await self.__ainit__()
            # except Exception as e:
            #     print(f"Reconnection failed: {e}")
            #     await asyncio.sleep(300)

    def renew_access_token(self, func):
        def wrapper(*args, **kwargs):
            print("doing wrapper stuff")
            try:
                return func(*args, **kwargs)
            except AuthClientError:
                self.token = oauth()
                return func(*args, **kwargs)

        return wrapper

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

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

    def check_if_channel_is_live(self, twitch_channels):
        streamer_channel = list(
            filter(lambda obj: (obj.display_name == TWITCH_STREAMER_CHANNEL), twitch_channels)
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
        if ctx.author.display_name == TWITCH_STREAMER_CHANNEL:
            logger.info(f"Author was {TWITCH_STREAMER_CHANNEL} and queue is {que_on_off}")
        else:
            logger.info(f"Nasty pleb: {ctx.author.display_name}")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo or message.author.display_name == "StreamElements":
            return

        logger.info(f"{message.author.name}: {message.content}")
        try:
            twitch_channels = await self.search_channels(query=TWITCH_STREAMER_CHANNEL)
        except twitchio.HTTPException:
            logger.info("Fetching channels http error, need to refresh token")
            self.token = self.refresh_token()
        
        is_channel_live = self.check_if_channel_is_live(twitch_channels)
        try:
            if message.author.name == TWITCH_STREAMER_CHANNEL:
                # logger.info(f"User is broadcaster so allowing by pass")
                await self.handle_commands(message)
            elif (is_channel_live is False) and message.content.startswith("!"):
                logger.info(f"{TWITCH_STREAMER_CHANNEL} is NOT live")
                await self.send_channel_offline_notification(message)
            elif (is_channel_live is False) and message.content in ALLOWED_COMMANDS:
                logger.info(f"{TWITCH_STREAMER_CHANNEL} is NOT live, but command was inside allowed commands.")
                await self.handle_commands(message)
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
            await self.send_result_to_chat(
                data=f"Current song is: {spotify_current_artists} - {spotify_current_track_name}"
            )
        elif current_song == None:
            logger.info(f"Spotify not running or playing songs.")
            await self.send_result_to_chat(data="Spotify not running or playing songs.")
        else:
            logger.info(
                f"Twitch user {ctx.author.name} tried to find songs, but nothing is playing."
            )
            await self.send_result_to_chat(data="No songs playing!")

    @commands.command(name="searchsong")
    async def search_song(self, ctx: commands.Context, *args):
        search_result = sp.spotify_search_song(args)
        if search_result == False:
            await self.send_result_to_chat(data=f"We did not find any songs!")
            return
        result = f"https://open.spotify.com/track/{search_result}"
        await self.send_result_to_chat(data=f"{result}")


    @commands.command(name="goons")
    async def eft_goons(self, ctx: commands.Context):
        resp_json = goons.find_goons_tarkov_pal()
        current_map = resp_json["Current Map"][0]
        location = resp_json["Location"][0]
        time = resp_json["Time"][0]
        time_submitted = resp_json["TimeSubmitted"][0]
        formatted_data = goons.find_goons()
        if isinstance(formatted_data, dict):
            map_value = formatted_data['map']
            timestamp_value = formatted_data['timestamp']
        else:
            map_value = formatted_data
            timestamp_value = formatted_data
        logger.info(f"Twitch user {ctx.author.name} fetched goons current location. Goons are currently in: {map_value}. Update timestamp: {timestamp_value}")
        await self.send_result_to_chat(
                data=f"According to Goonhunter Goons are currently in: {map_value}. Update timestamp: {timestamp_value}"
            )
        await self.send_result_to_chat(
                data=f"According to TarkovPal Goons are currently in: {current_map}. Update timestamp: {time}"
            )

    async def send_result_to_chat(self, data):
        await self.streamer_channel.send(data)

    async def event_channel_joined(self, channel: twitchio.Channel):
        if channel.name != TWITCH_STREAMER_CHANNEL:
            return
        self.streamer_channel = channel
        self.streamer_id = TWITCH_STREAMER_USER_ID

    async def event_token_expired(self):
        return oauth()

    async def refund(self, event):
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

    async def twitch_pubsub_channel_points_handler(self, event):
        self.refresh_token()
        twitch_channels = await self.search_channels(query=TWITCH_STREAMER_CHANNEL)
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
                # if song_info_request:
                #     logger.info(
                #         f"User {author_name} tried to find song with slur words"
                #     )
                #     await self.send_result_to_chat(data=f"Dirty song. Get lost.")
                #     return
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
                if result == False:
                    await self.send_result_to_chat(
                        data=f"We did not find any songs! Refunding points."
                    )
                    await self.refund(event)
                    return
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
            await self.refund(event)
        else:
            logger.info(
                f"We do not have that reward configured: {event.reward.title} {event.reward.id}"
            )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    CLIENT = bot.loop.run_until_complete(bot.__ainit__())
    print("CLIENT CREATED IN MAIN")
    sp = Spotify()
    goons = Goons()
    
    @CLIENT.event()
    async def event_token_expired():
        return oauth()

    @CLIENT.event()
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        await bot.twitch_pubsub_channel_points_handler(event)

    bot.run()