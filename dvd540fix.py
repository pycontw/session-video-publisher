"""Call ffmpeg to convert DVD-quality recordings to 720x540 (instead of 480).

Why are they 720x480? Why is 720x540 correct? See explaination here:
https://www.picturestoexe.com/forums/topic/1412-why-is-dvd-video-720x540/

    [...] DVD standard for NTSC describes that screen resolution is 720x480
    for aspect ratio = 4:3, but when you divided this sides you will receive
    NOT 4:3, but 3:1! [sic, should be 3:2] But for playback DVD player will
    read the parameter which describes aspect ratio (4:3) and will enlarge
    picture vertically.
"""

import os
import pathlib
import subprocess

i_dir = pathlib.Path(os.environ["VIDEO_ROOT"], "in")
o_dir = pathlib.Path(os.environ["VIDEO_ROOT"], "out")


o_dir.mkdir(parents=True, exist_ok=True)
for i_path in i_dir.glob("*.avi"):
    o_path = o_dir.joinpath(i_path.name)
    print(str(o_path))
    subprocess.run(
        f'ffmpeg -i "{i_path}" -aspect "720:540" -c copy "{o_path}"',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True,
        check=True,
    )
