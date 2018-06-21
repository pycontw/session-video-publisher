import datetime
import pathlib

import dateutil.parser
import google.auth
import requests

from apiclient.discovery import build
from apiclient.http import MediaFileUpload


YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'


def build_title(info):
    return f"{info['subject']} – {info['speaker']['name']} – PyCon Taiwan 2018"


def build_slot(info):
    start = dateutil.parser.parse(info['start'])
    if (start.date() - datetime.date(2018, 6, 1)).total_seconds() > 100:
        day = 2
    else:
        day = 1
    return f'Day {day}, {info["room"]}'


def build_description(info):
    slot = build_slot(info)
    return f"{slot}\n\n{info['summary']}\n\nSlides: {info['slides']}"


def build_body(info):
    return {
        'snippet': {
            'title': build_title(info),
            'description': build_description(info),
            'tags': 'PyCon Taiwan, PyCon Taiwan 2018, PyConTW, Python, PyCon',
            'categoryId': 28,
        },
        'status': {
            'privacyStatus': 'unlisted',
        },
    }


def choose_video(info):
    dirpath = pathlib.Path('C:\\Users\\uranusjr\\Downloads')
    for path in dirpath.glob('*.mp4'):
        if path.stem.endswith(info['subject']):
            return path


resp = requests.get('https://tw.pycon.org/2018/ccip/')
info_list = resp.json()

cred, slug = google.auth.default(scopes=[YOUTUBE_SCOPE])
youtube = build('youtube', 'v3', credentials=cred)

for info in info_list:
    if info['room'] != 'R0':
        continue
    body = build_body(info)
    vid_path = choose_video(info)
    if not vid_path:
        continue
    media = MediaFileUpload(str(vid_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part='snippet,status',
        body=build_body(info),
        media_body=media,
    )

    response = None
    print(f'Uploading {info["subject"]}')
    while not response:
        status, response = request.next_chunk()
    assert status % 100 == 2
    print(f'Uploaded as {response["id"]}')
    
    new_name = vid_path.parent.joinpath('done', vid_path.name)
    print(f'{vid_path} -> {new_name}')
    vid_path.rename(new_name)
