import logging
from twitchio.ext import commands, pubsub
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(
            irc_token=os.getenv('TWITCH_IRC_TOKEN'),  # replace with your IRC token
            client_id=os.getenv('TWITCH_CLIENT_ID'),  # replace with your client ID
            nick=os.getenv('TWITCH_BOT_NICK'),  # replace with your bot's nickname
            prefix='!',  # command prefix
            initial_channels=[os.getenv('TWITCH_CHANNEL')]  # replace with your channel
        )
        self.pubsub = pubsub.PubSub(self)
        self.reward_id = os.getenv('TWITCH_REWARD_ID')  # replace with your reward ID
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope="user-modify-playback-state"
        ))

    async def event_ready(self):
        print(f'Ready | {self.nick}')
        await self.pubsub.listen_to_channel_points(self.reward_id)

    async def event_message(self, message):
        print(message.content)
        await self.handle_commands(message)

    @pubsub.on_channel_points
    async def on_channel_points(self, data):
        user = data['data']['redemption']['user']['display_name']
        reward = data['data']['redemption']['reward']['title']
        song_name = data['data']['redemption']['user_input']
        if not self.is_channel_live():
            self.refund_points(data['data']['redemption']['id'])
            await self.get_channel(os.getenv('TWITCH_CHANNEL')).send(f'Refunded {reward} to {user}!')
        else:
            results = self.spotify.search(q=song_name, limit=1, type='track')
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                self.spotify.add_to_queue(track_uri)
                await self.get_channel(os.getenv('TWITCH_CHANNEL')).send(f'Added {song_name} to the queue!')
            else:
                await self.get_channel(os.getenv('TWITCH_CHANNEL')).send(f'Could not find {song_name} on Spotify.')

    def is_channel_live(self):
        # This is a simplified version, in a real bot you'd want to use the Twitch API to check if the channel is live
        return True

    def refund_points(self, redemption_id):
        # This is a simplified version, in a real bot you'd want to use the Twitch API to refund the points
        pass

    async def event_token_expired(self):
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope="user-modify-playback-state"
        ))

bot = Bot()
bot.run()