import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import requests
import sys


SCOPE = "user-library-read user-read-currently-playing user-read-playback-state user-modify-playback-state user-read-private"


class Spotify:
    # init method or constructor
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=SCOPE,
                open_browser=False,
                redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                show_dialog=True,
                cache_path=".token.txt",
            )
        )

    def spotify_current_track(self):
        json_resp = self.sp.current_user_playing_track()
        current_track_info = {}
        try: 
            is_playing = json_resp["is_playing"]
            track_id = json_resp["item"]["id"]
            track_name = json_resp["item"]["name"]
            artists = [artist for artist in json_resp["item"]["artists"]]
            link = json_resp["item"]["external_urls"]["spotify"]
            artist_names = ", ".join([artist["name"] for artist in artists])
            current_track_info = {
                "is_playing": is_playing,
                "id": track_id,
                "track_name": track_name,
                "artists": artist_names,
                "link": link,
            }
        except Exception as e:
            print(f"An exception occurred: {e}")

        return current_track_info

    def spotify_add_song_to_queue(self, song_request_from_user):
        added_song = {}
        try:
            self.sp.add_to_queue(song_request_from_user)
            added_song = song_request_from_user
        except Exception as e:
            print(f"An exception occurred: {e}")
            return e
        return added_song

    def spotify_get_song_info(self, song):
        json_resp = self.sp.track(song)
        track_info = {}
        try:
            artists = [artist["name"] for artist in json_resp["album"]["artists"]]
            track_id = json_resp["id"]
            track_name = json_resp["name"]
            link = json_resp["external_urls"]["spotify"]
            artist_names = ", ".join([artist for artist in artists])

            track_info = {
                "id": track_id,
                "track_name": track_name,
                "artists": artist_names,
                "link": link,
            }
        except Exception as e:
            print(f"An exception occurred: {e}")

        return track_info
    

    def split_artist_track(artist_track):
        artist_track = artist_track.replace(" – ", " - ")
        artist_track = artist_track.replace("“", '"')
        artist_track = artist_track.replace("”", '"')
        artist_track = artist_track.replace('\t', ' ')

        (artist, track) = artist_track.split(' - ', 1)
        artist = artist.strip()
        track = track.strip()
        # Validate
        if len(artist) == 0 and len(track) == 0:
            sys.exit("Error: Artist and track are blank")
        if len(artist) == 0:
            sys.exit("Error: Artist is blank")
        if len(track) == 0:
            sys.exit("Error: Track is blank")

        return (artist, track)

    
    # def spotify_search_song(self, arq):
    #     not_found = []
    #     track_ids = []
    #     print(arq)

    #     for line in arq:
    #         if not line[0].isdigit():
    #             continue
    #         song = line.split('. ', 1)[1]
    #         song = song.replace(" – ", " - ")
    #         if '-' not in song:
    #             continue
    #         (a, t) = self.split_artist_track(song)
    #         result = spotipy.search(q='artist: ' + a + ' track: ' + t,
    #                                 limit=1,
    #                                 type='track')
    #         print(result)
    #         if len(result['tracks']['items']) == 0:
    #             result = spotipy.search(q=song, limit=1, type='track')
    #             if len(result['tracks']['items']) == 0:
    #                 result = spotipy.search(q='track: ' + t,
    #                                         limit=20,
    #                                         type='track')
    #                 if len(result['tracks']['items']) == 0:
    #                     not_found.append(line)
    #                     print(a, ' - ', t, ': not found.')
    #                 else:
    #                     msg_t3 = a + ' - ' + t + ': not found.'
    #                     for i in result['tracks']['items']:
    #                         for nome in i['artists']:
    #                             if nome['name'] in a:
    #                                 track_ids.append(i['id'])
    #                                 msg_t3 = a + ' - ' + t + ': found.'
    #                                 break
    #                     if 'not found' in msg_t3:
    #                         not_found.append(line)
    #                     print(msg_t3)
    #             else:
    #                 track_ids.append(result['tracks']['items'][0]['id'])
    #                 print(a, ' - ', t, ': found.')
    #         else:
    #             track_ids.append(result['tracks']['items'][0]['id'])
    #             print(a, ' - ', t, ': found.')
    #     print(track_ids)
    #     return track_ids, not_found


    def spotify_search_song(self, term):
        search_limit = 10
        # searchURL =  "https://api.spotify.com/v1/search"
        # headers = {'Accept': 'application/json', 
        #             'Content-Type': 'application/json', 
        #             'Authorization': 'Bearer ' + accessToken}
        params = {'type': 'track',
                    'market': 'FI',
                    'limit': search_limit}
        params['q'] = term

        # print(json.dumps(self.sp._auth_headers))

        
        # r = requests.get(searchURL, params=params, headers=self.sp._auth_headers)

        r = self.sp.search(q=params)
        print(r)

        # page = r.content
        # print(page)
        # items = json.loads(page)
        # print(items)
        # items = items['tracks']
        # if items['total'] > 0 :
        #     loopcount = items['total']
        #     if items['total'] >= self.__searchLimit:
        #         loopcount = self.__searchLimit                
        #     items = items['items']
        #     res = []
        #     for i in range(loopcount):
        #         item = items[i]
        #         artist = [a['name'] for a in item['artists']]
        #         artists = ', '.join(artist)
        #         url = item['external_urls']['spotify']
        #         uri = item['uri']
        #         name = item['name']
        #         # print("%s - %s - %s - %s" % (artists, name, url, uri))
        #         res.append((artists, name, url, uri))
        #     return res
        # else :
        #     return None