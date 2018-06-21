import datetime
import os
import shutil

import dateutil.parser
import fuzzywuzzy.fuzz
import requests
import tqdm

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'
YOUTUBE_UPLOAD_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'

VIDEO_PATHS = list(pathlib.Path(os.environ['VIDEO_ROOT']).glob('*.mp4'))


def build_title(info):
    return f"{info['subject']} – {info['speaker']['name']} – PyCon Taiwan 2018"


def build_slot(info):
    start = dateutil.parser.parse(info['start'])
    if (start.date() - datetime.date(2018, 6, 1)).total_seconds() > 100:
        day = 2
    else:
        day = 1
    return f"Day {day}, {info['room']}"


def build_description(info):
    slot = build_slot(info)
    return f"{slot}\n\n{info['summary']}\n\nSlides: {info['slides']}"


def build_body(info):
    return {
        'snippet': {
            'title': build_title(info),
            'description': build_description(info),
            'tags': [
                'PyCon Taiwan',
                'PyCon Taiwan 2018',
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
    matches = [
        path for path in VIDEO_PATHS
        if fuzzywuzzy.fuzz.ratio(info['subject'], path.stem) > 70
    ]
    if matches:
        return max(matches)
    return None


resp = requests.get('https://tw.pycon.org/2018/ccip/')
info_list = resp.json()

flow = InstalledAppFlow.from_client_secrets_file(
    os.environ['OAUTH2_CLIENT_SECRET'],
    scopes=[YOUTUBE_UPLOAD_SCOPE],
)
credentials = flow.run_console()
youtube = build('youtube', 'v3', credentials=credentials)

for info in info_list:
    if info['room'] != 'R0':
        continue
    body = build_body(info)
    vid_path = choose_video(info)
    if not vid_path:
        print(f"No match, ignoring {info['subject']}")
        continue
    print(f"Uploading {info['subject']}")
    print(f"    {vid_path}")
    media = MediaFileUpload(
        str(vid_path), chunksize=262144, resumable=True,
        mimetype='application/octet-stream',
    )
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
    print(f"    Done, as {response['id']}")

    done = vid_path.parent.joinpath('done')
    done.mkdir(parents=True, exist_ok=True)
    new_name = done.joinpath(vid_path.name)
    print(f'    {vid_path} -> {new_name}')
    shutil.move(str(vid_path), str(new_name))
