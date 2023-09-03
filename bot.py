import os
import logging
from twitchio.ext import commands
from spotify.spotify import Spotify


logging.basicConfig(level=logging.INFO)
STREAMER_CHANNEL = os.environ["CHANNEL"]


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(
            token=os.environ["TMI_TOKEN"],
            client_id=os.environ["CLIENT_ID"],
            nick=os.environ["BOT_NICK"],
            prefix=os.environ["BOT_PREFIX"],
            initial_channels=[STREAMER_CHANNEL],
        )

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")

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
                #logger.info(f"User is broadcaster so allowing by pass")
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

    @commands.command(name="addsong")
    async def add_song(self, ctx: commands.Context, *args):
        if "https://open.spotify.com/track/" in args[0]:
            song_info_request = sp.spotify_get_song_info(args[0])
            sp.spotify_add_song_to_queue(args[0])
            spotify_artists_name = song_info_request["artists"]
            spotify_track_name = song_info_request["track_name"]
            logger.info(
                f"Twitch user {ctx.author.name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )
            await ctx.send(
                f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )
        else:
            result = sp.spotify_search_song(args)
            song_info_request = sp.spotify_get_song_info(result)
            sp.spotify_add_song_to_queue(result)
            spotify_artists_name = song_info_request["artists"]
            spotify_track_name = song_info_request["track_name"]
            logger.info(
                f"Twitch user {ctx.author.name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )
            await ctx.send(
                f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    bot = Bot()
    sp = Spotify()
    bot.run()
