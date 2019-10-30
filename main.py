""" Python script for formatting music files metadata in targeted directory.

The specified directory must be some kind of archives folder where musics are sorted in
subdirectories per album release. Metadat are currently extracted from the Spotify API for
developers.

Author: Stevy KIMPE
Date: 2019, October 29th
"""

import argparse, os, shutil, sys

from metadata.spotify import AlbumMetaData


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='../../*', type=str, help='Input music library folder. ' +
                        'By default, it takes any other folders of the parent directory other ' +
                        'than the `Archives` one.')
    parser.add_argument('--output', default='../../Archives', type=str, help='Output library folder.')
    args = parser.parse_args()

    assert os.path.exists(os.path.dirname(args.output))

    inLibrary = args.input
    if inLibrary == '../../*':
        possibilities = list(filter(lambda f: 'Archives' not in f and 'Programs' not in f, os.listdir('../..')))
        if possibilities: inLibrary = os.path.join('../..', possibilities[0])
        else: sys.exit()

    for directory, _, files in os.walk(inLibrary):
        if not files:
            album = os.path.basename(directory)
            artist = os.path.basename(os.path.dirname(directory))
            AlbumMetaData(album, artist).format(directory,
                os.path.join(args.output, os.path.relpath(directory, inLibrary))
            )

    for content in os.listdir(inLibrary):
        shutil.rmtree(os.path.join(inLibrary, content), ignore_errors=True)
