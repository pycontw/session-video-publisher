import dataclasses
import datetime
import typing

import dateutil.parser


@dataclasses.dataclass()
class Speaker:
    data: dict

    def render(self) -> str:
        data = self.data["en"]
        return f"Speaker: {data['name']}\n\n{data['bio']}"


@dataclasses.dataclass()
class Conference:
    name: str
    day1: datetime.date
    timezone: datetime.tzinfo


# YouTube video title has a 100-character restriction.
VIDEO_TITLE_LIMIT = 100


@dataclasses.dataclass()
class Session:
    conference: Conference
    title: str
    description: str
    start: datetime.datetime
    end: datetime.datetime
    slides: typing.Optional[str]
    speakers: typing.List[Speaker]
    room: str
    lang: str

    def __repr__(self):
        return f"<Session {self.title!r}>"

    def render_video_title(self) -> str:
        suffix = f" – {self.conference.name}"
        if len(self.title) + len(suffix) <= VIDEO_TITLE_LIMIT:
            return self.title + suffix
        title_limit = VIDEO_TITLE_LIMIT - len(suffix)
        return self.title[:title_limit] + suffix

    def _render_slot(self) -> str:
        # Fuzzy-match days. Don't be too strict because of leap seconds.
        d_secs = (self.start.date() - self.conference.day1).total_seconds()
        if d_secs > 47 * 60 * 60:
            day = 3
        elif d_secs > 23 * 60 * 60:
            day = 2
        else:
            day = 1

        # Much simpler than messing with strftime().
        start = str(self.start.astimezone(self.conference.timezone).time())[:5]
        end = str(self.end.astimezone(self.conference.timezone).time())[:5]

        if self.room not in ("R0", "R1", "R2", "R3"):
            return f"Day {day}, {start}–{end}"
        return f"Day {day}, {self.room} {start}–{end}"

    def render_video_description(self) -> str:
        if self.slides:
            slides_line = f"Slides: {self.slides}"
        else:
            slides_line = "Slides not uploaded by the speaker."
        return "\n\n".join(
            [
                self._render_slot(),
                self.description,
                slides_line,
                "\n\n".join(speaker.render() for speaker in self.speakers),
            ]
        )


class ConferenceInfoSource:
    _confernece: Conference
    _rooms: typing.Dict[str, str]
    _speakers: typing.Dict[str, Speaker]
    _session_data: typing.List[dict]

    def __init__(self, data: dict, confernece: Conference):
        self._confernece = confernece
        self._rooms = {d["id"]: d["en"]["name"] for d in data["rooms"]}
        self._speakers = {d["id"]: Speaker(d) for d in data["speakers"]}
        self._session_data = data["sessions"]

    def iter_sessions(self) -> typing.Iterator[Session]:
        for data in self._session_data:
            if data["type"] not in ("talk", "keynote"):
                continue

            title = data["en"]["title"]
            if data["type"] == "keynote":
                title = f"Keynote: {title}"
                lang = "en"
            elif "lng-ENEN" in data["tags"]:
                lang = "en"
            else:
                lang = "zh-hant"

            yield Session(
                conference=self._confernece,
                title=title,
                description=data["en"]["description"],
                start=dateutil.parser.parse(data["start"]),
                end=dateutil.parser.parse(data["end"]),
                slides=data["slide"] or None,
                speakers=[self._speakers[key] for key in data["speakers"]],
                room=self._rooms[data["room"]],
                lang=lang,
            )
