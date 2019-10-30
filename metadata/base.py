""" Definition of base classes inherited by the auto metadata music files getter.

On the principle that several music streaming platforms furnish REST - or not - API to automatically
get music files metadata, the following classes template the features of the different API handling
classes for the current program.

Author: Stevy KIMPE
Date: 2019, October 29th
"""

# Third parties packages importation
import matplotlib.pyplot as plt
import os, re, shutil

# Third parties packages specific features importation
from mutagen.flac import FLAC, Picture
from mutagen.id3 import PictureType

# Custom packages (whole and specific features) importation
from metadata.configuration import MusicConfig


class AlbumMetaData:
    """ Template class of album tracks metadata acquisition.

    This class is in charge of templating the features of classes in charge of handling the
    automatic acquisition of the targeted album music files metadata.

    This class is actually not directly in charge of the metadata acquisition. Instead, it is in
    charge of an easy-to-use set of to features to get targeted information. Inherited classes are
    in charge of filling the data gap, by whatever means they are designed to do so.

            Attributes:
                album(str): Album name.
                artist(str): Main artist (or band) name.
                musics(dict): Metadata of the music tracks in the given album.
                image(numpy.ndarray): Album image.
                artistImage(numpy.ndarray): Artist image.
    """

    details = ["artist", "artists", "title", "date", "image"]
    """ List metadata details which might be accessible for a specific music track. """

    def __init__(self, inAlbum, inMainArtist):
        """ Class constructor.

                Args:
                    inAlbum(str): Name of the album.
                    inMainArtist(str): Album main artist (or band) name.
        """

        self.album = inAlbum
        self.artist = inMainArtist
        self.musics = dict()
        self.image = None
        self.artistImage = None

    def associateFilesToInfos(self, files):
        """ Associate the given list of files to the music ID.

            Args:
                files(list): List of input music files paths.

            Returns:
                dict: Dictionary mapping the files to keys in the inner dictionary.
        """

        out = dict()

        for file in files:
            base = os.path.splitext(os.path.basename(file))[0].upper()
            template = re.sub(r'\W+', '', base)

            for key in self.musics.keys():
                if re.sub(r'\W+', '', key.upper()) in template:
                    out[file] = key
                    break

        return out

    def format(self, inDirectory, outDirectory):
        """ Format the specified directory music files with obtained metadata, and move the file
        to the specified directory.

            Args:
                inDirectory(str): Path to the targeted input directory. Should exist.
                outDirectory(str): Path to the targeted output directory. No existence obligation.
        """

        # List the targeted music files
        files = [os.path.join(inDirectory, m) for m in os.listdir(inDirectory)
                 if os.path.splitext(m)[1] in MusicConfig.extensions]
        associations = self.associateFilesToInfos(files)

        if not files: return

        if not os.path.exists(outDirectory):
            os.makedirs(outDirectory)

        # Create images file
        if self.image is not None:
            plt.imsave(os.path.join(outDirectory, 'cover.png'), self.image)
        if self.artistImage is not None:
            plt.imsave(os.path.join(os.path.dirname(outDirectory), 'artist.png'), self.artistImage)
            pop = os.popen('attrib +h ' + os.path.abspath(
                os.path.join(os.path.dirname(outDirectory), 'artist.png')))
            pop.read(); pop.close()

        for file in files:

            path = os.path.join(outDirectory, os.path.dirname(os.path.relpath(file, inDirectory)))
            path = os.path.join(path, associations[file] + '.flac')
            shutil.copy(file, path)
            music = FLAC(path)
            infos = self.musics[associations[file]]

            music['title'] = [associations[file]]
            music['album'] = [self.album]
            music['albumartist'] = [self.artist]
            music['artist'] = [a.title() for a in infos['artists']]
            music['date'] = [infos['date']]
            music['tracknumber'] = [str(infos['track'])]
            music['discnumber'] = [str(infos['disc'])]
            music['genre'] = [genre.title() for genre in infos['genres']]

            picture = Picture()
            with open(os.path.join(outDirectory, 'cover.png'), 'rb') as file:
                picture.data = file.read()

            picture.type = PictureType.COVER_FRONT
            picture.mime = u"image/png"
            picture.width = self.image.shape[0]
            picture.height = self.image.shape[1]
            picture.depth = 8 if type(self.image.dtype) == 'uint8' else 16

            music.add_picture(picture)
            music.save()

        # Hide cover image
        pop = os.popen('attrib +h ' + os.path.abspath(os.path.join(outDirectory, 'cover.png')))
        pop.read(); pop.close()
