"""Crop letterbox from videos fixed by dvd540fix.

This assumes the input video is of dimension 720x540.

Example usage:

    python dvd540crop.py 自製高擴充性機器學習系統 --height=480 --top=40
"""

import argparse
import os
import pathlib
import subprocess

i_dir = pathlib.Path(os.environ["VIDEO_ROOT"], "in")
o_dir = pathlib.Path(os.environ["VIDEO_ROOT"], "out")

o_dir.mkdir(parents=True, exist_ok=True)

input_mapping = {i_path.stem: i_path for i_path in i_dir.glob("*.avi")}


parser = argparse.ArgumentParser()
parser.add_argument(
    "filename",
    type=str,
    choices=list(input_mapping.keys()),
    help="Input filename, not including extension",
)
parser.add_argument(
    "--top", type=int, required=True, help="Top letterbox to crop"
)
parser.add_argument(
    "--height", type=int, required=True, help="Height of cropped video"
)
parser.add_argument(
    "--threads",
    "--thread",
    type=str,
    default="auto",
    help="Threads to use (passed directly to FFmpeg)",
)
options = parser.parse_args()


i_path = input_mapping[options.filename]
o_path = o_dir.joinpath(f"{i_path.stem}.mp4")
subprocess.run(
    f'ffmpeg -i "{i_path}" -threads {options.threads} '
    f'-filter:v "crop=720:{options.height}:0:{options.top}" '
    f'-codec:v libx264 -crf 0 -preset veryslow "{o_path}"',
    shell=True,
    check=True,
)
