import argparse

from .generate_playlist import generate_playlist
from .upload_video import upload_video


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Upload videos to YouTube channel",
    )
    parser.add_argument(
        "-p",
        "--playlist",
        action="store_true",
        help="Generate playlist information in json files",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default="./videos",
        help="Output path of video information",
    )
    return parser.parse_args(argv)


def main(argv=None):
    options = parse_args(argv)

    if options.upload:
        upload_video()

    if options.playlist:
        generate_playlist(options.output_dir)


if __name__ == "__main__":
    main()
