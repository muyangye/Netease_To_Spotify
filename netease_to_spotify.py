from pyncm import apis
import spotipy
import yaml
import base64
import sys

class NeteaseToSpotify:
    def __init__(self):
        with open("config.yml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            try:
                self.spotify = spotipy.Spotify(
                    auth_manager=spotipy.oauth2.SpotifyOAuth(
                        client_id=config["client_id"],
                        client_secret=config["client_secret"],
                        redirect_uri=config["redirect_uri"],
                        scope="playlist-modify-public playlist-modify-private user-library-read ugc-image-upload"
                    )
                )
            except:
                # print("Spotify授权失败, 终止程序")
                print("Spotify authorization failed, program terminated.")
                sys.exit()
            self.spotify_playlist_name = config["spotify_playlist_name"]
            # Use netease.png as default Spotify playlist cover image
            self.cover_image_path = config["cover_image_path"] if config["cover_image_path"] != "DESIRED_SPOTIFY_PLAYLIST_COVER_IMAGE_PATH" else "netease.png"
            self.netease_playlist_id = config["netease_playlist_id"]
    
    def migrate(self):
        """
        Migrate the Netease playlist to Spotify

        :return: None
        """
        spotify_playlist_id = self.get_or_create_playlist()
        # Basically just retrieve all tracks' name and 1st artist in Netease's playlist
        # and do a search using Spotify's Search API
        for name, artist in self.get_netease_playlist_tracks_name_and_artist():
            try:
                track_id = self.search_for_track(name, artist)
                self.spotify.playlist_add_items(spotify_playlist_id, [track_id])
            except Exception as e:
                # print("此歌曲Spotify无版权, 迁移失败: " + name + ", " + artist)
                print("Spotify does not have this track's copyright: " + name + ", " + artist)
    
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
            if (playlist["name"] == self.spotify_playlist_name):
                playlist_id = playlist["id"]
                break
        if (not playlist_id):
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
            # print("创建Spotify歌单失败(歌单封面图像不存在或过大), 终止程序")
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
        
    def search_for_track(self, name, artist=None):
        """
        Search for a track by name and artist (if provided)

        :return: the track's Spotify ID
        :rtype: str
        """
        # This is a very aggressive search, so there may be tracks that mismatch, 
        # but this approach correctly gives many tracks that are searchable but not
        # found using a more precise search
        query = name
        if (artist):
            query += " " + artist
        # Assume the first one is the most relevant
        return self.spotify.search(query, type="track")["tracks"]["items"][0]["id"]
    
    def get_netease_playlist_tracks_name_and_artist(self):
        """
        Get all tracks' name and 1st artist in the given Netease playlist

        :return: list of (name, artist) pairs of all tracks in the playlist
        :rtype: list(tuple(str, str))
        """
        playlist = apis.playlist.GetPlaylistInfo(self.netease_playlist_id)
        track_ids = [track_id["id"] for track_id in playlist["playlist"]["trackIds"]]
        songs = apis.track.GetTrackDetail(track_ids)["songs"]
        result = [(song["name"], song["ar"][0]["name"]) for song in songs]
        return result