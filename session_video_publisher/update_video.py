import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .common import build_body, choose_video
from .config import ConfigUpdate as Config
from .info import Conference, ConferenceInfoSource


def update_video():
    Config.variable_check()

    print("Update videos...")
    YOUTUBE_UPDATE_SCOPE = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    # build youtube connection
    flow = InstalledAppFlow.from_client_secrets_file(
        Config.OAUTH2_CLIENT_SECRET, scopes=YOUTUBE_UPDATE_SCOPE
    )
    credentials = flow.run_console()
    youtube = build(
        "youtube",
        "v3",
        credentials=credentials,
        developerKey=Config.YOUTUBE_API_KEY,
    )

    request = youtube.playlists().list(
        part="contentDetails, snippet, id",
        id=[Config.PLAYLIST_ID],
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
        requests.get(Config.URL).json(),
        Conference(
            Config.CONFERENCE_NAME, Config.FIRST_DATE, Config.TIMEZONE_TAIPEI
        ),
    )

    for session in source.iter_sessions():
        body = build_body(session)
        try:
            vid = choose_video(session, video_records, "title")
        except ValueError:
            print(f"No match, ignoring {session.title}")
            continue
        print(f'Updating "{vid}" with "{body}"')

        request = youtube.videos().update(
            part="snippet,status,recordingDetails",
            body={**body, "id": vid},
        )
        response = request.execute()
