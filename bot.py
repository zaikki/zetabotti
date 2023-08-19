import os
from twitchio.ext import commands
from spotify.spotify import FetchSong


# set up the bot
bot = commands.Bot(
    token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)

@bot.event
async def event_ready():
    'Called once when the bot goes online.'
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")


@bot.event
async def event_message(ctx):
    'Runs every time a message is sent in chat.'

    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
        return

    await bot.handle_commands(ctx)

    # await ctx.channel.send(ctx.content)

    if 'hello' in ctx.content.lower():
        await ctx.channel.send(f"Hi, @{ctx.author.name}!")


@bot.command(name='test')
async def test(ctx):
    await ctx.send('test passed!')

@bot.command(name="song")
async def current_song(ctx):
    current_song = a.spotify_fetch_track()
    spotify_current_artists = current_song["artists"]
    spotify_current_track_name = current_song["track_name"]
    await ctx.send(f"Current song is: {spotify_current_artists} - {spotify_current_track_name}")


if __name__ == "__main__":
    a = FetchSong()
    a.call_refresh()
    bot.run()