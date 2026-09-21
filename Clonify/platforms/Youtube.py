import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
import aiohttp

# YouTube download API (same style as the reference Youtube.py)
# Keep secrets in environment variables; never hard-code API keys in source.
SHRUTI_API_URL = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site").rstrip("/")
SHRUTI_API_KEY = os.environ.get("SHRUTI_API_KEY", "").strip()

# Official YouTube Data API v3: metadata/search/playlist only.
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
YOUTUBE_DATA_API = "https://www.googleapis.com/youtube/v3"

DOWNLOAD_DIR = "downloads"


def _video_id(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([A-Za-z0-9_-]{11})", value)
    if m:
        return m.group(1)
    return value if re.fullmatch(r"[A-Za-z0-9_-]{11}", value) else None


def _valid_file(path: str | None, minimum: int = 4096) -> bool:
    try:
        return bool(path and os.path.isfile(path) and os.path.getsize(path) >= minimum)
    except OSError:
        return False


async def _download_api(link: str, media_type: str) -> str | None:
    """Download a finite YouTube media file through the configured API.

    The API response is treated as a binary media response, not as a remote
    playback URL. This guarantees PyTgCalls receives a real local file.
    """
    if not SHRUTI_API_KEY:
        return None
    vid = _video_id(link) or link.strip()
    if not vid:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if media_type == "video" else "mp3"
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", vid)[:80]
    path = os.path.join(DOWNLOAD_DIR, f"{safe}.{ext}")
    if _valid_file(path):
        return path

    timeout = aiohttp.ClientTimeout(total=600 if media_type == "video" else 300, connect=15, sock_read=60)
    headers = {"User-Agent": "NOBITA-CLONE-MUSIX/1.0", "Accept": "*/*"}
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={"url": vid, "type": media_type, "api_key": SHRUTI_API_KEY},
            ) as resp:
                if resp.status != 200:
                    return None
                content_type = (resp.headers.get("Content-Type") or "").lower()
                with open(path, "wb") as out:
                    async for chunk in resp.content.iter_chunked(131072):
                        if chunk:
                            out.write(chunk)

        if not _valid_file(path):
            try: os.remove(path)
            except OSError: pass
            return None

        # Do not accept obvious JSON/HTML error payloads as MP3/MP4.
        if any(x in content_type for x in ("application/json", "text/html", "text/plain")):
            raw = Path(path).read_bytes()[:512].lower()
            if any(x in raw for x in (b"error", b"invalid", b"unauthorized", b"failed")):
                try: os.remove(path)
                except OSError: pass
                return None
        return path
    except Exception:
        try: os.remove(path)
        except OSError: pass
        return None


async def download_song(link: str) -> str | None:
    return await _download_api(link, "audio")


async def download_video(link: str) -> str | None:
    return await _download_api(link, "video")



def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "audio", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "video", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=600)
            ) as resp:
                if resp.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def _data_search(self, query: str, limit: int = 10):
        if not YOUTUBE_API_KEY or not query:
            return []
        params = {
            "part": "snippet", "q": query, "type": "video",
            "maxResults": max(1, min(int(limit), 50)),
            "order": "relevance", "regionCode": "IN",
            "safeSearch": "moderate", "key": YOUTUBE_API_KEY,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=12, connect=5, sock_read=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{YOUTUBE_DATA_API}/search", params=params) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json(content_type=None)
            return data.get("items") or []
        except Exception:
            return []

    async def _data_video(self, video_id: str):
        if not YOUTUBE_API_KEY or not video_id:
            return None
        try:
            params = {
                "part": "snippet,contentDetails,statistics,liveStreamingDetails",
                "id": video_id, "key": YOUTUBE_API_KEY,
            }
            timeout = aiohttp.ClientTimeout(total=12, connect=5, sock_read=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{YOUTUBE_DATA_API}/videos", params=params) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json(content_type=None)
            items = data.get("items") or []
            return items[0] if items else None
        except Exception:
            return None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        vid = _video_id(link)
        if vid:
            item = await self._data_video(vid)
            if item:
                sn = item.get("snippet") or {}
                iso = str((item.get("contentDetails") or {}).get("duration") or "")
                m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
                sec = (int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)) if m else 0
                duration_min = f"{sec//3600}:{(sec%3600)//60:02d}:{sec%60:02d}" if sec >= 3600 else f"{sec//60}:{sec%60:02d}" if sec else "0:00"
                thumbs = sn.get("thumbnails") or {}
                thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url")
                return sn.get("title") or "YouTube", duration_min, sec, (thumb or "").split("?")[0], vid
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
            return title, duration_min, duration_sec, thumbnail, vidid
        raise ValueError("YouTube video not found")

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist_id = None
        m = re.search(r"[?&]list=([A-Za-z0-9_-]+)", link)
        if m:
            playlist_id = m.group(1)
        if YOUTUBE_API_KEY and playlist_id:
            try:
                params = {"part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": max(1, min(int(limit), 50)), "key": YOUTUBE_API_KEY}
                timeout = aiohttp.ClientTimeout(total=20, connect=5, sock_read=12)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{YOUTUBE_DATA_API}/playlistItems", params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            ids = []
                            for item in data.get("items") or []:
                                vid = str(((item.get("contentDetails") or {}).get("videoId") or ""))
                                if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                                    ids.append(vid)
                            if ids:
                                return ids[:max(1, int(limit))]
            except Exception:
                pass
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def search_many(self, query: str, limit: int = 10):
        tracks = []
        for item in await self._data_search(query, limit):
            vid = str(((item.get("id") or {}).get("videoId") or ""))
            if len(vid) != 11:
                continue
            sn = item.get("snippet") or {}
            thumbs = sn.get("thumbnails") or {}
            tracks.append({
                "title": (sn.get("title") or "YouTube")[:80],
                "link": self.base + vid,
                "vidid": vid,
                "duration_min": "",
                "thumb": ((thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url") or "").split("?")[0],
            })
        if tracks:
            return tracks[:limit]
        return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if _valid_file(downloaded_file):
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False


YouTube = YouTubeAPI()
