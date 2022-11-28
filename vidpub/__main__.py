import argparse

from .upload_video import upload_video
from .update_video import update_video
from .generate_playlist import generate_playlist


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
        "--update_desc",
        action="store_true",
        help="Update video description in YouTube channel",
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

    if options.update_desc:
        update_video()

    if options.playlist:
        generate_playlist(options.output_dir)


if __name__ == "__main__":
    main()
