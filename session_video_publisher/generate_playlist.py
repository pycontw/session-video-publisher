from .config import ConfigGenerate as Config
from slugify import slugify
from googleapiclient.discovery import build
import os
import json
import datetime


def extract_info(description: str):
    speaker = []
    recorded_day = ""

    lines = description.split("\n")

    for line in lines:
        if line.strip().lower().startswith("day"):
            day = int(line.strip().lower().split(",")[0].strip().split(" ")[1])
            recorded_day = str(
                Config.FIRST_DATE + datetime.timedelta(days=day - 1)
            )
        elif line.strip().lower().startswith("speaker"):
            speaker.append(line.strip().split(":")[1].strip())
        else:
            pass

    return speaker, recorded_day


def process_page_response(pl_response):
    video_records = {}

    for video in pl_response["items"]:
        vid = video["snippet"]["resourceId"]["videoId"]
        data = {}

        data["description"] = video["snippet"]["description"]
        data["speakers"], data["recorded"] = extract_info(
            video["snippet"]["description"]
        )
        data["title"] = video["snippet"]["title"]
        data["thumbnail_url"] = video["snippet"]["thumbnails"]["high"]["url"]
        data["videos"] = [
            {
                "type": "youtube",
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        ]

        video_records[vid] = {"data": data}

    return video_records


def generate_playlist(output_dir: str):
    Config.variable_check()

    print("Generating playlist information...")

    # build youtube connection
    youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)

    # generate playlist
    playlist_id = ""
    playlist_video_num = 0

    # get specified playlist of the channel
    if Config.PLAYLIST_ID:
        request = youtube.playlists().list(
            part="contentDetails, snippet",
            id=[Config.PLAYLIST_ID],
            maxResults=1,
        )

        response = request.execute()

        print(response)
        playlist = response["items"][0]

        playlist_id = playlist["id"]
        playlist_video_num = int(playlist["contentDetails"]["itemCount"])

        print(f"Playlist ID = {playlist_id}")
        print(f"Playlist title = {playlist['snippet']['title']}")
        print(f"Playlist Video numbers = {playlist_video_num}")

    elif Config.PLAYLIST_TITLE and not Config.PLAYLIST_ID:
        request = youtube.playlists().list(
            part="contentDetails, snippet",
            channelId=Config.CHANNEL_ID,
            maxResults=10,
        )

        response = request.execute()

        # find the target playlist from .env setting
        for playlist in response["items"]:
            if (
                Config.PLAYLIST_TITLE.strip().lower()
                in playlist["snippet"]["title"].strip().lower()
            ):
                playlist_id = playlist["id"]
                playlist_video_num = int(
                    playlist["contentDetails"]["itemCount"]
                )

                print(f"Playlist ID = {playlist_id}")
                print(f"Playlist title = {playlist['snippet']['title']}")
                print(f"Playlist Video numbers = {playlist_video_num}")
    else:
        print("[Warning] The video number exceeds maximum limit.")

    if playlist_video_num > Config.MAX_RESULT_LIMIT:
        print(
            "[Warning] The video number exceeds maximum limit, please set MAX_RESULT_LIMIT to larger value."
        )

    video_records = {}

    next_page_token = None

    while True:
        pl_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=Config.MAX_RESULT_LIMIT,
            pageToken=next_page_token,
        )

        pl_response = pl_request.execute()

        for video in pl_response["items"]:
            vid = video["snippet"]["resourceId"]["videoId"]
            data = {}

            data["description"] = video["snippet"]["description"]
            data["speakers"], data["recorded"] = extract_info(
                video["snippet"]["description"]
            )
            data["title"] = video["snippet"]["title"]
            data["thumbnail_url"] = video["snippet"]["thumbnails"]["high"]["url"]
            data["videos"] = [{"type": "youtube", "url": f"https://www.youtube.com/watch?v={vid}", }]

            video_records[vid] = {"data": data}

        next_page_token = pl_response.get("nextPageToken")

        if not next_page_token:
            break

    print(f"Number of items returned: {len(video_records)}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for key in video_records.keys():
        file_name = (
            f"{video_records[key]['data']['title'].lower().strip()}".replace(
                ":", ""
            ).replace(" ", "-")
        )
        file_name = slugify(file_name)
        data = video_records[key]["data"]

        with open(
            os.path.join(output_dir, f"{file_name}.json"), "w"
        ) as json_file:
            json.dump(data, json_file, indent=4)
        print(file_name)
