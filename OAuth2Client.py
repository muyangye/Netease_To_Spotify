import webbrowser
import requests
import base64

# Spotify's authorization and access_token endpoints, replace with other apps' to extend
AUTHORIZATION_ENDPOINT = "https://accounts.spotify.com/authorize"
ACCESS_TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

class OAuth2Client:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        # NOTE: This self.redirect_uri is different from redirect_uri below after logging in. This is the one when you created your Spotify app
        self.redirect_uri = redirect_uri
        self.scope = "playlist-modify-public playlist-modify-private"
        self.access_token = self.get_access_token()

    # TODO: Add access token cache
    def get_access_token(self):
        login_url = requests.post(AUTHORIZATION_ENDPOINT,
            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scope
            }
        ).url
        # Open up browser and sign in to Spotify
        webbrowser.open(login_url)
        # This is the redirect_uri that contains code
        redirect_uri = input("Please copy the entire redirected url after you logged in here:\n")
        code = redirect_uri[redirect_uri.index("?code=") + 6 : ]
        access_token = requests.post(ACCESS_TOKEN_ENDPOINT, 
            headers = {
                "Authorization": "Basic " + base64.b64encode(bytes(self.client_id + ":" + self.client_secret, "utf-8")).decode(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            params = {
                "grant_type": "authorization_code",
                # This is the code in the parameter of redirect_uri
                "code": code,
                "redirect_uri": self.redirect_uri,
            }
        ).json()["access_token"]
        return access_token