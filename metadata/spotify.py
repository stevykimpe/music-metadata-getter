""" Definition of tools extracting music metadata from Spotify API.

This is achieving by a simple class, inheriting from the `metadata.base.AlbumMetaData` class, whose
constructor fill the parent class metadata structure by requesting the Spotify API for Developers.

Author: Stevy KIMPE
Date: 2019, October 29th
"""

# Third parties packages importation
import requests
import numpy as np

# Third parties packages specific features importation
from io import BytesIO
from PIL import Image

# Custom packages (whole and specific features) importation
import metadata.base
from metadata.configuration import SpotifyConfig


class AlbumMetaData(metadata.base.AlbumMetaData):
    """ Class in charge of acquiring a specified album music files metadata, and in charge of
    formatting it to allow handling through the `AlbumMetaData` parent class.

    This requires the application to be register on the Spotify for developers platform at
    https://developer.spotify.com/dashboard ; what is needed is a client application ID, associated
    to its secret token, and to have register a specific URI for redirection during the
    authentication process.
    """

    ClientID = SpotifyConfig.ClientID
    ClientSecret = SpotifyConfig.ClientSecret
    RedirectURI = SpotifyConfig.RedirectURI

    def __init__(self, inAlbum, inMainArtist):
        """ Class constructor.

                Args:
                    inAlbum(str): Name of the album.
                    inMainArtist(str): Album main artist (or band) name.
        """
        def getSpotifyImage(sImages):
            """ From an input list of Spotify-like images, choose the one with high dimensions.

                Args:
                    sImages: Spotify-like images list.

                Returns:
                    numpy.ndarray: Numpy-like selected image.
            """
            dimension = max([image['width'] for image in sImages])
            url = list(filter(lambda image: image['width'] == dimension, sImages))[0]['url']
            response = requests.get(url, headers={'Authorization': 'Bearer ' + token})

            return np.asarray(Image.open(BytesIO(response.content))) \
                if response.status_code == 200 else None

        # Initiate the parent class
        super(AlbumMetaData, self).__init__(inAlbum, inMainArtist)

        # Request Spotify for permission
        permission = requests.get('https://accounts.spotify.com/authorize/',
                                  auth=(self.ClientID, self.ClientSecret))

        # Exit if permission not granted
        if permission.status_code != 200: return

        # Request Spotify for a token
        tokenResponse = requests.post('https://accounts.spotify.com/api/token',
                                      data={'grant_type': 'client_credentials'},
                                      auth=(self.ClientID, self.ClientSecret))

        # Exit if no token was granted
        if tokenResponse.status_code != 200: return
        token = tokenResponse.json()['access_token']

        # Request Spotify for finding the desired album of the desired artist
        album = requests.get('https://api.spotify.com/v1/search',
                             headers={'Authorization': 'Bearer ' + token},
                             params={'q': 'album:' + self.album + ' artist:' + self.artist,
                                     'type': 'album', 'limit': 1})

        # Exit if album search did not get a match
        if album.status_code != 200: return
        albumInfos = album.json()['albums']
        if albumInfos['total'] < 1: return
        albumInfos = albumInfos['items'][0]

        # Security over Spotify data
        if not albumInfos['artists']: return
        if albumInfos['name'].upper() != inAlbum.upper() \
                or albumInfos['artists'][0]['name'].upper() != inMainArtist.upper():
            print('You should correct directories name for :   ' + inAlbum + '   by   ' +
                  inMainArtist + '   as   ' + albumInfos['name'] + '   by   ' +
                  albumInfos['artists'][0]['name'])
            return

        if albumInfos['images']:
            self.image = getSpotifyImage(albumInfos['images'])

        # Request for artist information
        artist = requests.get(albumInfos['artists'][0]['href'],
                              headers={'Authorization': 'Bearer ' + token})
        artistInfos = artist.json() if artist.status_code == 200 else {'genres': [], 'images': []}

        # Album and artist special information
        genres = artistInfos['genres']
        label = albumInfos['label'] if 'label' in artistInfos.keys() else ''

        # Get artist image
        self.artistImage = getSpotifyImage(artistInfos['images'])

        # Request for tracks metadata
        tracks = requests.get('https://api.spotify.com/v1/albums/' + albumInfos['id'] + '/tracks',
                              headers={'Authorization': 'Bearer ' + token}, params={'limit': 50})

        # Exit if no tracks found
        if tracks.status_code != 200: return
        tracksInfo = tracks.json()

        for music in tracksInfo['items']:
            title = music['name']
            self.musics[title] = dict()
            self.musics[title]['artists'] = [a['name'] for a in music['artists']]
            self.musics[title]['track'] = music['track_number']
            self.musics[title]['disc'] = music['disc_number']
            self.musics[title]['genres'] = genres
            self.musics[title]['date'] = albumInfos['release_date']
            self.musics[title]['label'] = label
