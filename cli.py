import argparse
from netease_to_spotify import NeteaseToSpotify
import sys

def main(ids = None):
    app = NeteaseToSpotify()
    app.migrate(ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", nargs="+", help="网易云音乐歌单id, 如114115123", required=False)
    args = parser.parse_args()
    main(args.list)