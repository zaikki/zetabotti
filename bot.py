import os
from twitchio.ext import commands

# import twitchio
from spotify.spotify import Spotify
import requests

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
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")

    # def get_args(self, ctx):
    #     if self.has_args(ctx):
    #         return self.clean_message(ctx)

    def check_if_channel_is_live(self, channel_name):
        contents = requests.get(f"https://www.twitch.tv/{channel_name}").content.decode(
            "utf-8"
        )
        if "isLiveBroadcast" in contents:
            return True
        else:
            return False

    async def send_channel_offline_notification(self, message):
        return await message.channel.send(
            f"Channel is offline! Some commands are disabled like !song and !addsong"
        )

    async def turn_off_song_queue(self, ctx: commands.Context, que_on_off=False):
        if ctx.author.display_name == STREAMER_CHANNEL:
            print(f"Author was {STREAMER_CHANNEL} and queue is {que_on_off}")
        else:
            print(f"Nasty pleb: {ctx.author.display_name}")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Print the contents of our message to console...
        print(f"{message.author.name}: {message.content}")

        # user = twitchio.SearchUser(http="https://api.twitch.tv/helix/search/channels",data={id: os.environ["STREAMER_USER_ID"]})
        # print(user)
        # await self.fetch_channels([os.environ["CHANNEL"]])

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        is_channel_live = self.check_if_channel_is_live(STREAMER_CHANNEL)
        try:
            if message.author.name == STREAMER_CHANNEL:
                print(f"User is broadcaster so allowing by pass")
                await self.handle_commands(message)
            elif (is_channel_live is False) and message.content.startswith("!"):
                print(f"{STREAMER_CHANNEL} is NOT live")
                await self.send_channel_offline_notification(message)
            elif (is_channel_live is True) and message.content.startswith("!"):
                print(f"{STREAMER_CHANNEL} is live")
                await self.handle_commands(message)
        except Exception as e:
            print(f"An exception occurred: {e}")

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command(name="songqueue")
    async def song_queue_on_off(self, ctx: commands.Context, on_off):
        await self.turn_off_song_queue(ctx, on_off)

    @commands.command(name="song")
    async def current_song(self, ctx: commands.Context):
        current_song = sp.spotify_current_track()
        if (current_song is not None) and (current_song["is_playing"] is True):
            spotify_current_artists = current_song["artists"]
            spotify_current_track_name = current_song["track_name"]
            print(
                f"Twitch user {ctx.author.name} fetched song: {spotify_current_artists} - {spotify_current_track_name}"
            )
            await ctx.send(
                f"Current song is: {spotify_current_artists} - {spotify_current_track_name}"
            )
        else:
            print(
                f"Twitch user {ctx.author.name} tried to find songs, but nothing is playing."
            )
            await ctx.send(f"No songs playing!")

    @commands.command(name="search")
    async def search_song(self, ctx: commands.Context, *args):
        arguments = args
        #arguments = ', '.join(args)
        
        sp.spotify_search_song(arguments)
        #await ctx.send(f'{len(args)} arguments: {arguments}')

    @commands.command(name="addsong")
    async def add_song(self, ctx: commands.Context, args):
        if args.startswith("https://open.spotify.com/track/"):
            song_info_request = sp.spotify_get_song_info(args)
            que_return = sp.spotify_add_song_to_queue(args)
            print(que_return)
            spotify_artists_name = song_info_request["artists"]
            spotify_track_name = song_info_request["track_name"]
            print(
                f"Twitch user {ctx.author.name} added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )
            await ctx.send(
                f"Added song to queue: {spotify_artists_name} - {spotify_track_name}"
            )
        else:
            await ctx.send(
                "We do not support currently that format, please use from Spotify: Share --> Copy Song Link"
            )


if __name__ == "__main__":
    bot = Bot()
    sp = Spotify()
    bot.run()
