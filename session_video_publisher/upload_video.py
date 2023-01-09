import datetime
import functools
import io
import itertools
import os
import pathlib
import string

import apiclient.http
import fuzzywuzzy.fuzz
import pytz
import requests
import tqdm
from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from .info import Conference, ConferenceInfoSource, Session

# Video publisher variables
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

FIRST_DATE = datetime.date(
    int(os.environ["YEAR"]), int(os.environ["MONTH"]), int(os.environ["DAY"])
)

CONFERENCE_NAME = f"PyCon Taiwan {FIRST_DATE.year}"

TIMEZONE_TAIPEI = pytz.timezone("Asia/Taipei")


def guess_language(s: str) -> str:
    """Guess language of a string.

    The only two possible return values are `zh-hant` and `en`.

    Nothing scientific, just a vaguely educated guess. If more than half of the
    string is ASCII, probably English; otherwise we assume it's Chinese.
    """
    if sum(c in string.ascii_letters for c in s) > len(s) / 2:
        return "en"
    return "zh-hant"


def build_body(session: Session) -> dict:
    title = session.render_video_title()

    return {
        "snippet": {
            "title": title,
            "description": session.render_video_description(),
            "tags": [
                session.conference.name,
                "PyCon Taiwan",
                "PyCon",
                "Python",
            ],
            "defaultAudioLanguage": session.lang,
            "defaultLanguage": guess_language(title),
            "categoryId": "28",
        },
        "status": {
            "license": "creativeCommon",
            "privacyStatus": "unlisted",
            "publishAt": None,
        },
        "recordingDetails": {
            "recordingDate": format_datetime_for_google(session.start)
        },
    }


def format_datetime_for_google(dt: datetime.datetime) -> str:
    """Format a datetime into ISO format for Google API.

    Google API is weirdly strict on the format here. It REQUIRES exactly
    three digits of milliseconds, and only accepts "Z" suffix (not +00:00),
    so we need to roll our own formatting instead relying on `isoformat()`.
    """
    return dt.astimezone(pytz.utc).strftime(r"%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def get_match_ratio(session: Session, path: pathlib.Path) -> float:
    return fuzzywuzzy.fuzz.ratio(session.title, path.stem)


def choose_video(session: Session, video_paths: list) -> pathlib.Path:
    """Look through the file list and choose the one that "looks most like it"."""
    score, match = max((get_match_ratio(session, p), p) for p in video_paths)
    if score < 70:
        raise ValueError("no match")
    return match


def media_batch_reader(file_path, chuncksize=64 * (1 << 20)):
    print(f"Reading Vedio from:\n\t{file_path}")
    out = io.BytesIO()
    total = file_path.stat().st_size // chuncksize
    with open(file_path, "rb") as f:
        for block in tqdm.tqdm(
            functools.partial(f.read, chuncksize), total=total
        ):
            out.write(block)
    return out.getvalue()


def upload_video():
    print("Uploading videos...")

    # build youtube connection
    flow = InstalledAppFlow.from_client_secrets_file(
        os.environ["OAUTH2_CLIENT_SECRET"], scopes=[YOUTUBE_UPLOAD_SCOPE]
    )
    credentials = flow.run_console()

    youtube = build("youtube", "v3", credentials=credentials)

    # upload video
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

    source = ConferenceInfoSource(
        requests.get(os.environ["URL"]).json(),
        Conference(CONFERENCE_NAME, FIRST_DATE, TIMEZONE_TAIPEI),
    )

    for session in source.iter_sessions():
        body = build_body(session)
        try:
            vid_path = choose_video(session, VIDEO_PATHS)
        except ValueError:
            print(f"No match, ignoring {session.title}")
            continue

        print(f"Uploading {session.title}")
        print(f"    {vid_path}")

        media = apiclient.http.MediaInMemoryUpload(
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
