import os
from twitchio.ext import commands
from spotify.spotify import Spotify
import pprint


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
            initial_channels=[os.environ["CHANNEL"]],
        )

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Print the contents of our message to console...
        print(message.content)

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command(name="song")
    async def current_song(self, ctx: commands.Context):
        current_song = sp.spotify_current_track()
        if current_song["is_playing"] is True:
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

    @commands.command(name="addsong")
    async def add_song(self, ctx: commands.Context, song_request_from_user):
        if song_request_from_user.startswith("https://open.spotify.com/track/"):
            song_info_request = sp.spotify_get_song_info(song_request_from_user)
            sp.spotify_add_song_to_queue(song_request_from_user)
            spotify_artists_name = song_info_request["artists"]
            spotify_track_name = song_info_request["track_name"]
            await ctx.send(
                f"Added song to playlist: {spotify_artists_name} - {spotify_track_name}"
            )
        else:
            await ctx.send(
                "We do not support currently that format, please use from Spotify: Share --> Copy Song Link"
            )

    def get_args(self, ctx):
        if self.has_args(ctx):
            return self.clean_message(ctx)


if __name__ == "__main__":
    bot = Bot()
    sp = Spotify()
    bot.run()
