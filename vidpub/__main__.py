import datetime
import itertools
import os
import pathlib

import fuzzywuzzy.fuzz
import pytz
import requests
import tqdm

from apiclient.discovery import build
from apiclient.http import MediaInMemoryUpload
from google_auth_oauthlib.flow import InstalledAppFlow

from .info import Conference, ConferenceInfoSource


YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

VIDEO_ROOT = pathlib.Path(os.environ["VIDEO_ROOT"]).resolve()
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

FIRST_DATE = datetime.date(
    int(os.environ["YEAR"]), int(os.environ["MONTH"]), int(os.environ["DAY"])
)

CONFERENCE_NAME = f"PyCon Taiwan {FIRST_DATE.year}"

TIMEZONE_TAIPEI = pytz.timezone("Asia/Taipei")


def build_body(session):
    return {
        "snippet": {
            "title": session.render_video_title(),
            "description": session.render_video_description(),
            "tags": [
                session.conference.name,
                "PyCon Taiwan",
                "PyCon",
                "Python",
            ],
            "categoryId": "28",
        },
        "status": {"privacyStatus": "unlisted", "publishAt": None},
    }


def choose_video(session):
    """Look through the file list and choose the one that "looks most like it".
    """
    return max(
        path
        for path in VIDEO_PATHS
        if fuzzywuzzy.fuzz.ratio(session.title, path.stem) > 70
    )


source = ConferenceInfoSource(
    requests.get(os.environ["URL"]).json(),
    Conference(CONFERENCE_NAME, FIRST_DATE, TIMEZONE_TAIPEI),
)

flow = InstalledAppFlow.from_client_secrets_file(
    os.environ["OAUTH2_CLIENT_SECRET"], scopes=[YOUTUBE_UPLOAD_SCOPE]
)
credentials = flow.run_console()
youtube = build("youtube", "v3", credentials=credentials)


for session in source.iter_sessions():
    body = build_body(session)
    try:
        vid_path = choose_video(session)
    except ValueError:
        print(f"No match, ignoring {session!r}")
        continue

    print(f"Uploading {session!r}")
    print(f"    {vid_path}")
    media = MediaInMemoryUpload(vid_path.read_bytes(), resumable=True)
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
