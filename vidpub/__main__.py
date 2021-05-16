# import argparse
import click
import datetime
import itertools
import json
import os
import pathlib
import string

import apiclient.http
import fuzzywuzzy.fuzz
import pytz
import requests
import tqdm

from .info import Conference, ConferenceInfoSource, Session
from slugify import slugify

# Video publisher variables
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

FIRST_DATE = datetime.date(
    int(os.environ["YEAR"]), int(os.environ["MONTH"]), int(os.environ["DAY"])
)

CONFERENCE_NAME = f"PyCon Taiwan {FIRST_DATE.year}"

TIMEZONE_TAIPEI = pytz.timezone("Asia/Taipei")


# Video data generator variables
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
PLAYLIST_TITLE = os.environ.get("PLAYLIST_TITLE", "")
PLAYLIST_ID = os.environ.get("PLAYLIST_ID", "")
CONFERENCE_DAY1 = os.environ.get("CONFERENCE_DAY1", "")

MAX_RESULT_LIMIT = 100


def guess_language(s: str) -> str:
    """Guess language of a string.

    The only two possible return values are `zh-hant` and `en`.

    Nothing scientific, just a vaguely educated guess. If more than half of the
    string is ASCII, probably English; othereise we assume it's Chinese.
    """
    if sum(c in string.ascii_letters for c in s) > len(s) / 2:
        return "en"
    return "zh-hant"


def format_datetime_for_google(dt: datetime.datetime) -> str:
    """Format a datetime into ISO format for Google API.

    Google API is wierdly strict on the format here. It REQUIRES exactly
    three digits of milliseconds, and only accepts "Z" suffix (not +00:00),
    so we need to roll our own formatting instead relying on `isoformat()`.
    """
    return dt.astimezone(pytz.utc).strftime(r"%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


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


def get_match_ratio(session: Session, path: pathlib.Path) -> float:
    return fuzzywuzzy.fuzz.ratio(session.title, path.stem)


def choose_video(session: Session, video_paths: list) -> pathlib.Path:
    """Look through the file list and choose the one that "looks most like it".
    """
    score, match = max((get_match_ratio(session, p), p) for p in video_paths)
    if score < 70:
        raise ValueError("no match")
    return match


def build_youtube(action: str):
    from apiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow

    if action == 'upload':
        flow = InstalledAppFlow.from_client_secrets_file(
            os.environ["OAUTH2_CLIENT_SECRET"], scopes=[YOUTUBE_UPLOAD_SCOPE]
        )
        credentials = flow.run_console()
        return build("youtube", "v3", credentials=credentials)

    elif action == 'generate':
        return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    else:
        raise ValueError(f"Does not supported action = {action}")

def compute_date(first_date: datetime.date, delta_days=0):
    conference_date = first_date + datetime.timedelta(days=delta_days)

    return str(conference_date)


def extract_info(description: str):

    speaker = []
    recorded_day = ''

    lines = description.split('\n')

    for line in lines:
        if line.strip().lower().startswith('day'):
            day = int(line.strip().lower().split(',')[0].strip().split(' ')[1])
            recorded_day = compute_date(FIRST_DATE, delta_days=day-1)
        elif line.strip().lower().startswith('speaker'):
            speaker.append(line.strip().split(':')[1].strip())
        else:
            pass

    return speaker, recorded_day

@click.command()
@click.option('-a', '--action', required=True, help='Actions to perform: upload or generate', \
                type=click.Choice(['upload', 'generate'], case_sensitive=False))
@click.option('-o', '--output_dir', default='./videos', help='Output video information path')

def main(action, output_dir):

    youtube = build_youtube(action)

    if action == 'upload':

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
                vid_path.read_bytes(), resumable=True
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

    elif action == 'generate':

        playlist_id = ''
        playlist_video_num = 0

        # get specified playlist of the channel
        if PLAYLIST_ID:
            request = youtube.playlists().list(
                part='contentDetails, snippet',
                id=[PLAYLIST_ID],
                maxResults=1
            )

            response = request.execute()

            print(response)
            playlist = response['items'][0]

            playlist_id = playlist['id']
            playlist_video_num = int(playlist['contentDetails']['itemCount'])

            print(f"Playlist ID = {playlist_id}")
            print(f"Playlist title = {playlist['snippet']['title']}")
            print(f"Playlist Video numbers = {playlist_video_num}")

        elif PLAYLIST_TITLE and not PLAYLIST_ID:
            request = youtube.playlists().list(
                part='contentDetails, snippet',
                channelId=CHANNEL_ID,
                maxResults=10
            )

            response = request.execute()

            # find the target playlist from .env setting
            for playlist in response['items']:
                if PLAYLIST_TITLE.strip().lower() in playlist['snippet']['title'].strip().lower():
                    playlist_id = playlist['id']
                    playlist_video_num = int(playlist['contentDetails']['itemCount'])

                    print(f"Playlist ID = {playlist_id}")
                    print(f"Playlist title = {playlist['snippet']['title']}")
                    print(f"Playlist Video numbers = {playlist_video_num}")
        else:
            print(f"[Warning] The video number exceeds maximum limit.")


        if playlist_video_num > MAX_RESULT_LIMIT:
            print(f"[Warning] The video number exceeds maximum limit, please set MAX_RESULT_LIMIT to larger value.")


        pl_request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=playlist_video_num
        )

        pl_response = pl_request.execute()

        video_records = {}

        for video in pl_response['items']:

            vid = video['snippet']['resourceId']['videoId']
            data = {}

            data['description'] = video['snippet']['description']
            data['speakers'], data['recorded'] = extract_info(video['snippet']['description'])
            data['title'] = video['snippet']['title']
            data['thumbnail_url'] = video['snippet']['thumbnails']['high']['url']
            data['videos'] = [{'type':'youtube', 'url': f"https://www.youtube.com/watch?v={vid}"}]

            video_records[vid] = {'data': data}

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for key in video_records.keys():
            file_name = f"{video_records[key]['data']['title'].lower().strip()}".replace(':', '').replace(' ', '-')
            file_name = slugify(file_name)
            data = video_records[key]['data']

            with open(os.path.join(output_dir, f"{file_name}.json"), 'w') as json_file:
                json.dump(data, json_file, indent=4)

            print(file_name)

    else:
        print(f"Does not supported action = {action}")


if __name__ == "__main__":
    main()
