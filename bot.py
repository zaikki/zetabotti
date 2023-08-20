import os
from twitchio.ext import commands
from spotify.spotify import Spotify


# set up the bot
# bot = commands.Bot(
#     token=os.environ["TMI_TOKEN"],
#     client_id=os.environ["CLIENT_ID"],
#     nick=os.environ["BOT_NICK"],
#     prefix=os.environ["BOT_PREFIX"],
#     initial_channels=[os.environ["CHANNEL"]],
# )


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
        current_song = a.spotify_fetch_track()
        if isinstance(current_song, str):
            print(
                f"Twitch user {ctx.author.name} tried to find songs, but nothing is playing."
            )
            await ctx.send(f"No songs playing!")
        else:
            spotify_current_artists = current_song["artists"]
            spotify_current_track_name = current_song["track_name"]
            print(
                f"Twitch user {ctx.author.name} fetched song: {spotify_current_artists} - {spotify_current_track_name}"
            )
            await ctx.send(
                f"Current song is: {spotify_current_artists} - {spotify_current_track_name}"
            )

    @commands.command(name="addsong")
    async def add_song(self, ctx: commands.Context):
        spotify_artists_name = "Artisti"
        spotify_track_name = "Maksaa"
        # added_song = a.add_song_to_queue()
        await ctx.send(
            f"Added song to playlist: {spotify_artists_name} - {spotify_track_name}"
        )


# @bot.event
# async def event_ready():
#     "Called once when the bot goes online."
#     print(f"{os.environ['BOT_NICK']} is online!")
#     ws = bot._ws  # this is only needed to send messages within event_ready
#     await ws.send_privmsg(os.environ["CHANNEL"], f"/me has landed!")


# @bot.event
# async def event_message(ctx):
#     "Runs every time a message is sent in chat."

#     # make sure the bot ignores itself and the streamer
#     # if ctx.author.name.lower() == os.environ["BOT_NICK"].lower():
#     #     return

#     if "hello" in ctx.content.lower():
#         await ctx.channel.send(f"Hi, @{ctx.author.name}!")

#     await bot.handle_commands(ctx)

#     # await ctx.channel.send(ctx.content)


# @bot.command(name="test")
# async def test(ctx):
#     await ctx.send("test passed!")


# @bot.command(name="song")
# async def current_song(ctx):
#     current_song = a.spotify_fetch_track()
#     if isinstance(current_song, str):
#         print(
#             f"Twitch user {ctx.author.name} tried to find songs, but nothing is playing."
#         )
#         await ctx.send(f"No songs playing!")
#     else:
#         spotify_current_artists = current_song["artists"]
#         spotify_current_track_name = current_song["track_name"]
#         print(
#             f"Twitch user {ctx.author.name} fetched song: {spotify_current_artists} - {spotify_current_track_name}"
#         )
#         await ctx.send(
#             f"Current song is: {spotify_current_artists} - {spotify_current_track_name}"
#         )


# @bot.command(name="addsong")
# async def add_song(ctx):
#     spotify_artists_name = "Artisti"
#     spotify_track_name = "Maksaa"
#     #added_song = a.add_song_to_queue()
#     await ctx.send(
#         f"Added song to playlist: {spotify_artists_name} - {spotify_track_name}"
#     )


if __name__ == "__main__":
    a = Spotify()
    a.call_refresh()
    bot = Bot()
    bot.run()
