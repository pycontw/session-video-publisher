import datetime
import pathlib
import string
from typing import Dict, List, Union

import fuzzywuzzy.fuzz
import pytz

from .info import Session


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


def get_match_ratio(session: Session, target_string: str) -> float:
    return fuzzywuzzy.fuzz.ratio(session.title, target_string)


def choose_video(
    session: Session, source: List[Union[pathlib.Path, Dict]], strategy: str
) -> str:
    """Look through the file list and choose the one that "looks most like it"."""
    choose_video_strategy = {
        "title": lambda source: max(
            (get_match_ratio(session, p["title"]), p["vid"]) for p in source
        ),
        "path": lambda source: max(
            (get_match_ratio(session, p.stem), p.stem) for p in source
        ),
    }
    if strategy not in choose_video_strategy:
        raise ValueError("strategy should be 'title' or 'path'")
    score, match = choose_video_strategy[strategy](source)
    if score < 70:
        raise ValueError("no match")
    return match
