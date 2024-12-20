from datetime import date, datetime
from pyncm import apis
from tqdm import tqdm
from unidecode import unidecode
import base64
import re
import spotipy
import sys
import yaml


DEFAULT_COVER_PATH = "assets/netease.png"
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private user-library-read ugc-image-upload"

# For some reason, Netease's API sometimes returns a publishTime of really weird unix timestamp like year 2240 after converting to time
# so we need to filter out those strange values
# This will not affect songs published before unix start, just that in Spotify's search query, will not use the year filter
# in ms
UNIX_START = 1000
MS_PER_S = 1000
NEXT_YEAR = datetime(datetime.now().year + 1, 1, 1).timestamp() * MS_PER_S

class NeteaseToSpotify:
    def __init__(self):
        print("---------- Starting Application ----------")
        with open("config.yml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            try:
                self.spotify = spotipy.Spotify(
                    auth_manager=spotipy.oauth2.SpotifyOAuth(
                        client_id=config["client_id"],
                        client_secret=config["client_secret"],
                        redirect_uri=config["redirect_uri"],
                        scope=SPOTIFY_SCOPES
                    )
                )
            except:
                print("Spotify authorization failed, program terminated.")
                sys.exit()
            self.spotify_playlist_name = config["spotify_playlist_name"]
            # Use netease.png as default Spotify playlist cover image
            self.cover_image_path = config["cover_image_path"] if config["cover_image_path"] != "DESIRED_SPOTIFY_PLAYLIST_COVER_IMAGE_PATH" else DEFAULT_COVER_PATH
            self.netease_playlist_id = config["netease_playlist_id"]
    
    def migrate(self):
        """
        Migrate the Netease playlist to Spotify

        :return: None
        """
        spotify_playlist_id = self.get_or_create_playlist()
        # Basically just retrieve all tracks' name and 1st artist in Netease's playlist
        # and do a search using Spotify's Search API
        netease_playlist_tracks_name_and_artist = self.get_netease_playlist_tracks_name_and_artist()
        print("---------- Inserting Songs to Spotify ----------")
        for name, artist, year in tqdm(netease_playlist_tracks_name_and_artist):
            # Delete all parentheses because whatever inside will make search return much less/no results
            trimmed_name = re.sub(r'\(.*\)', '', name)
            try:
                track_id = self.search_for_track(year, trimmed_name, artist)
                self.spotify.playlist_add_items(spotify_playlist_id, [track_id])
            except Exception as e:
                print(f"Spotify does not have this song's copyright: {unidecode(name)}, {unidecode(artist)}")
    
    def get_or_create_playlist(self):
        """
        Get or create the playlist of name given as the value of key "spotify_playlist_names" in the config file

        :return: the playlist's Spotify ID
        :rtype: str
        """
        playlist_id = None
        # First search through all current user's playlists to see if a playlist with the same name already exists
        user_playlists = self.spotify.user_playlists(self.spotify.me()["id"])
        for playlist in user_playlists["items"]:
            if playlist["name"] == self.spotify_playlist_name:
                playlist_id = playlist["id"]
                break
        if not playlist_id:
            playlist_id = self.create_playlist()
        return playlist_id

    def create_playlist(self):
        """
        Create a playlist

        :return: the new playlist's Spotify ID
        :rtype: str
        """
        playlist_id = self.spotify.user_playlist_create(self.spotify.me()["id"], self.spotify_playlist_name)["id"]
        try:
            b64_cover_image = self.get_base64_from_image(self.cover_image_path)
            self.spotify.playlist_upload_cover_image(playlist_id, b64_cover_image)
        except Exception as e:
            print("Failed to create Spotify playlist (can't find cover_image_path or image is too large), program terminated.")
            sys.exit()
        return playlist_id
    
    def get_base64_from_image(self, path):
        """
        Get the base64 representation of an image

        :return: base64 representation
        :rtype: str
        """
        binary_fc = open(path, "rb").read()
        base64_utf8_str = base64.b64encode(binary_fc).decode("utf-8")
        return base64_utf8_str
        
    def search_for_track(self, year, name, artist=None):
        """
        Search for a track by name and artist (if provided)

        :return: the track's Spotify ID
        :rtype: str
        """
        query = ""
        # 3 years interval
        if year != -1:
            query += f"year:{year - 1}-{year + 1} "
        query += name
        if artist:
            query += " " + artist
        # Only search for the most relevant result (first)
        return self.spotify.search(query, limit=1, type="track")["tracks"]["items"][0]["id"]
    
    def get_netease_playlist_tracks_name_and_artist(self):
        """
        Get all tracks' name and 1st artist in the given Netease playlist

        :return: list of (name, artist) pairs of all tracks in the playlist
        :rtype: list(tuple(str, str))
        """
        print("---------- Getting Netease Cloud Music Data (this may take a few seconds) ----------")
        playlist = apis.playlist.GetPlaylistInfo(self.netease_playlist_id)
        track_ids = [track_id["id"] for track_id in playlist["playlist"]["trackIds"]]
        songs = []
        # Split track_ids to pieces of length at most 1000 to avoid PyNCM API limitation
        left, right = 0, 0
        while right < len(track_ids):
            right = left + min(1000, len(track_ids) - right)
            songs.extend(apis.track.GetTrackDetail(track_ids[left:right])["songs"])
            left = right
        result = [(song["name"],
                   song["ar"][0]["name"], 
                   date.fromtimestamp(song["publishTime"] / MS_PER_S).year if "publishTime" in song and UNIX_START <= song["publishTime"] <= NEXT_YEAR else -1)
                for song in songs]
        return result