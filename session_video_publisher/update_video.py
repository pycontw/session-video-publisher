import datetime
import os
import string

import fuzzywuzzy.fuzz
import pytz
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .info import Conference, ConferenceInfoSource, Session

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
                "pyconapac2022",
                "pycontw",
                "python",
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


def get_match_ratio(session: Session, title: str) -> float:
    return fuzzywuzzy.fuzz.ratio(session.title, title)


def choose_video(session: Session, videos: list) -> str:
    """Look through the file list and choose the one that "looks most like it"."""
    score, match = max(
        (get_match_ratio(session, video["title"]), video["vid"])
        for video in videos
    )
    if score < 40:
        raise ValueError("no match")
    return match


def update_video():
    print(f"Update videos...")
    YOUTUBE_UPDATE_SCOPE = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    # build youtube connection
    flow = InstalledAppFlow.from_client_secrets_file(
        os.environ["OAUTH2_CLIENT_SECRET"], scopes=YOUTUBE_UPDATE_SCOPE
    )
    credentials = flow.run_console()
    youtube = build("youtube", "v3", credentials=credentials)

    request = youtube.playlists().list(
        part="contentDetails, snippet, id",
        id=[os.environ["PLAYLIST_ID"]],
        maxResults=1,
    )

    response = request.execute()

    playlist = response["items"][0]
    playlist_id = playlist["id"]
    playlist_video_num = int(playlist["contentDetails"]["itemCount"])

    pl_request = youtube.playlistItems().list(
        part="snippet", playlistId=playlist_id, maxResults=playlist_video_num
    )

    pl_response = pl_request.execute()

    video_records = []

    for video in pl_response["items"]:
        data = {}
        vid = video["snippet"]["resourceId"]["videoId"]
        data["vid"] = vid
        data["description"] = video["snippet"]["description"]
        data["title"] = video["snippet"]["title"]
        data["thumbnail_url"] = video["snippet"]["thumbnails"]["high"]["url"]
        data["videos"] = [
            {
                "type": "youtube",
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        ]

        video_records.append(data)

    source = ConferenceInfoSource(
        requests.get(os.environ["URL"]).json(),
        Conference(CONFERENCE_NAME, FIRST_DATE, TIMEZONE_TAIPEI),
    )

    for session in source.iter_sessions():
        body = build_body(session)
        try:
            vid = choose_video(session, video_records)
        except ValueError:
            print(f"No match, ignoring {session.title}")
            continue
        print(f"Updating {vid} with {body}")

        request = youtube.videos().update(
            part="snippet,status,recordingDetails",
            body={**body, "id": vid},
        )
        response = request.execute()
