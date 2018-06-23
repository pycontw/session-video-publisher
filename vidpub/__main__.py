import datetime
import itertools
import os
import pathlib

import dateutil.parser
import fuzzywuzzy.fuzz
import pytz
import requests
import tqdm

from apiclient.discovery import build
from apiclient.http import MediaInMemoryUpload
from google_auth_oauthlib.flow import InstalledAppFlow


YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'
YOUTUBE_UPLOAD_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'

VIDEO_ROOT = pathlib.Path(os.environ['VIDEO_ROOT']).resolve()
print(f"Reading video files from {VIDEO_ROOT}")

VIDEO_PATHS = list(itertools.chain.from_iterable(
    VIDEO_ROOT.glob(f'*{ext}')
    for ext in ('.avi', '.mp4')
))
assert VIDEO_PATHS
print(f"    {len(VIDEO_PATHS)} files loaded")

DONE_DIR_PATH = VIDEO_ROOT.joinpath('done')
DONE_DIR_PATH.mkdir(parents=True, exist_ok=True)

FIRST_DATE = datetime.date(
    int(os.environ['YEAR']),
    int(os.environ['MONTH']),
    int(os.environ['DAY']),
)

TIMEZONE_TAIPEI = pytz.timezone('Asia/Taipei')


def build_title(info):
    parts = [
        info['subject'],
        info['speaker']['name'],
        f"PyCon Taiwan {os.environ['YEAR']}",
    ]
    title = ' – '.join(parts)
    if len(title) > 100:    # YouTube has title length restriction.
        parts[0] = f"{parts[0][:50]} …"
        title = ' – '.join(parts)
    return title


def build_slot(info):
    start = dateutil.parser.parse(info['start'])
    end = dateutil.parser.parse(info['end'])

    # Fuzzy-match days. Don't be too strict because there may be leap seconds.
    d_secs = (start.date() - FIRST_DATE).total_seconds()
    if d_secs > 47 * 60 * 60:
        day = 3
    elif d_secs > 23 * 60 * 60:
        day = 2
    else:
        day = 1

    # Much simpler than messing with strftime().
    start = str(start.astimezone(TIMEZONE_TAIPEI).time())[:5]
    end = str(end.astimezone(TIMEZONE_TAIPEI).time())[:5]
    return f"Day {day}, {info['room']} {start}–{end}"


def build_description(info):
    slot = build_slot(info)
    if info.get('slides'):
        slides_line = f"Slides: {info['slides']}"
    else:
        slides_line = 'The speaker did not upload his slides.'
    return f"{slot}\n\n{info['summary']}\n\n{slides_line}"


def build_body(info):
    return {
        'snippet': {
            'title': build_title(info),
            'description': build_description(info),
            'tags': [
                'PyCon Taiwan',
                f"PyCon Taiwan {os.environ['YEAR']}",
                'Python',
                'PyCon',
            ],
            'categoryId': '28',
        },
        'status': {
            'privacyStatus': 'unlisted',
            'publishAt': None,
        },
    }


def choose_video(info):
    """Look through the file list and choose the one that "looks most like it".
    """
    return max(
        path for path in VIDEO_PATHS
        if fuzzywuzzy.fuzz.ratio(info['subject'], path.stem) > 70
    )


resp = requests.get(os.environ['URL'])
info_list = resp.json()

flow = InstalledAppFlow.from_client_secrets_file(
    os.environ['OAUTH2_CLIENT_SECRET'],
    scopes=[YOUTUBE_UPLOAD_SCOPE],
)
credentials = flow.run_console()
youtube = build('youtube', 'v3', credentials=credentials)


for info in info_list:
    body = build_body(info)
    try:
        vid_path = choose_video(info)
    except ValueError:
        print(f"No match, ignoring {info['subject']}")
        continue

    print(f"Uploading {info['subject']}")
    print(f"    {vid_path}")
    media = MediaInMemoryUpload(vid_path.read_bytes(), resumable=True)
    request = youtube.videos().insert(
        part=','.join(body.keys()), body=body,
        media_body=media,
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
    print(f'    {vid_path} -> {new_name}')
    vid_path.rename(new_name)
