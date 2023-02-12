import datetime
import os

import pytz


class Config:
    YEAR = os.environ.get("YEAR")
    MONTH = os.environ.get("MONTH")
    DAY = os.environ.get("DAY")
    FIRST_DATE = datetime.date(int(YEAR), int(MONTH), int(DAY))

    @classmethod
    def variable_check(cls):
        assert (
            cls.YEAR
        ), "envvar YEAR missing, please specify it in the .env file"
        assert (
            cls.MONTH
        ), "envvar MONTH missing, please specify it in the .env file"
        assert (
            cls.DAY
        ), "envvar DAY missing, please specify it in the .env file"


class ConfigGenerate(Config):
    YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
    CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
    PLAYLIST_TITLE = os.environ.get("PLAYLIST_TITLE", "")
    PLAYLIST_ID = os.environ.get("PLAYLIST_ID", "")
    MAX_RESULT_LIMIT = 100

    @classmethod
    def variable_check(cls):
        Config.variable_check()
        assert (
            cls.YOUTUBE_API_KEY
        ), "envvar YOUTUBE_API_KEY missing, please specify it in the .env file"


class ConfigUpload(Config):
    OAUTH2_CLIENT_SECRET = os.environ.get("OAUTH2_CLIENT_SECRET")
    URL = os.environ.get("URL")
    VIDEO_ROOT = os.environ.get("VIDEO_ROOT")
    CONFERENCE_NAME = f"PyCon Taiwan {Config.YEAR}"
    TIMEZONE_TAIPEI = pytz.timezone("Asia/Taipei")
    YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

    @classmethod
    def variable_check(cls):
        Config.variable_check()
        assert (
            cls.OAUTH2_CLIENT_SECRET
        ), "envvar OAUTH2_CLIENT_SECRET missing, please specify it in the .env file"
        assert (
            cls.URL
        ), "envvar URL missing, please specify it in the .env file"
        assert (
            cls.VIDEO_ROOT
        ), "envvar VIDEO_ROOT missing, please specify it in the .env file"


class ConfigUpdate(Config):
    OAUTH2_CLIENT_SECRET = os.environ.get("OAUTH2_CLIENT_SECRET")
    URL = os.environ.get("URL")
    PLAYLIST_ID = os.environ.get("PLAYLIST_ID")
    CONFERENCE_NAME = f"PyCon Taiwan {Config.YEAR}"
    TIMEZONE_TAIPEI = pytz.timezone("Asia/Taipei")

    @classmethod
    def variable_check(cls):
        Config.variable_check()
        assert (
            cls.OAUTH2_CLIENT_SECRET
        ), "envvar OAUTH2_CLIENT_SECRET missing, please specify it in the .env file"
        assert (
            cls.URL
        ), "envvar URL missing, please specify it in the .env file"
        assert (
            cls.PLAYLIST_ID
        ), "envvar PLAYLIST_ID missing, please specify it in the .env file"
