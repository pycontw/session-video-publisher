import functools
import io
import itertools
import pathlib

import googleapiclient.http
import requests
import tqdm
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .common import build_body, choose_video
from .config import ConfigUpload as Config
from .info import Conference, ConferenceInfoSource


def media_batch_reader(file_path, chunk_size=64 * (1 << 20)):
    print(f"Reading video from:\n\t{file_path}")
    out = io.BytesIO()
    total = file_path.stat().st_size // chunk_size
    with open(file_path, "rb") as f:
        for block in tqdm.tqdm(
            functools.partial(f.read, chunk_size), total=total
        ):
            out.write(block)
    return out.getvalue()


def upload_video():
    Config.variable_check()

    print("Uploading videos...")

    # build youtube connection
    flow = InstalledAppFlow.from_client_secrets_file(
        Config.OAUTH2_CLIENT_SECRET, scopes=[Config.YOUTUBE_UPLOAD_SCOPE]
    )
    credentials = flow.run_console()

    youtube = build("youtube", "v3", credentials=credentials)

    # upload video
    VIDEO_ROOT = pathlib.Path(Config.VIDEO_ROOT).resolve()
    print(f"Reading video files from {VIDEO_ROOT}")

    VIDEO_PATHS = list(
        itertools.chain.from_iterable(
            VIDEO_ROOT.glob(f"*{ext}") for ext in (".avi", ".mp4")
        )
    )
    assert VIDEO_PATHS
    print(f"    {len(VIDEO_PATHS)} files loaded")

    DONE_DIR_PATH = VIDEO_ROOT.joinpath("done")
    DONE_DIR_PATH.mkdir(parents=True, exist_ok=True)

    source = ConferenceInfoSource(
        requests.get(Config.URL).json(),
        Conference(
            Config.CONFERENCE_NAME, Config.FIRST_DATE, Config.TIMEZONE_TAIPEI
        ),
    )

    for session in source.iter_sessions():
        body = build_body(session)
        try:
            vid_path = choose_video(session, VIDEO_PATHS, "path")
        except ValueError:
            print(f"No match, ignoring {session.title}")
            continue

        print(f"Uploading {session.title}")
        print(f"    {vid_path}")

        media = googleapiclient.http.MediaInMemoryUpload(
            media_batch_reader(vid_path), resumable=True
        )
        request = youtube.videos().insert(
            part=",".join(body.keys()), body=body, media_body=media
        )

        with tqdm.tqdm(total=100, ascii=True) as progressbar:
            prev = 0
            while True:
                status, response = request.next_chunk()
                if status:
                    curr = int(status.progress() * 100)
                    progressbar.update(curr - prev)
                    prev = curr
                if response:
                    break
        print(f"    Done, as: https://youtu.be/{response['id']}")

        new_name = DONE_DIR_PATH.joinpath(vid_path.name)
        print(f"    {vid_path} -> {new_name}")
        vid_path.rename(new_name)
