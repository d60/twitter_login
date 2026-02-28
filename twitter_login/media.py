import asyncio
import hashlib
import mimetypes
from abc import ABC, abstractmethod
from contextlib import contextmanager
from io import BufferedIOBase, BytesIO
from logging import getLogger
from pathlib import Path

from .api import API
from .enums import MediaCategory
from .http import load_json_response

logger = getLogger(__name__)


IMAGE_CATEGORIES = [
    MediaCategory.COMMUNITY_BANNER,
    MediaCategory.LIST_BANNER,
    MediaCategory.TWEET_IMAGE,
    MediaCategory.DM_IMAGE,
    MediaCategory.PROFILE_BANNER,
    MediaCategory.CARD_IMAGE
]
VIDEO_CATEGORIES = [
    MediaCategory.AMPLIFY_VIDEO,
    MediaCategory.TWEET_VIDEO,
    MediaCategory.DM_VIDEO
]
GIF_CATEGORIES = [MediaCategory.TWEET_GIF, MediaCategory.DM_GIF]
SUBTITLE_CATEGORIES = [MediaCategory.SUBTITLES]

# supported mimetypes
IMAGE_MIMETYPES = ['image/jpeg', 'image/png', 'image/webp']
GIF_MIMETYPES = ['image/gif']
VIDEO_MIMETYPES = ['video/mp4', 'video/quicktime']
SUBTITLE_MIMETYPES = ['text/plain charset=utf-8']

CATEGORIES_MIMETYPES_MAPPING = [
    (IMAGE_CATEGORIES, IMAGE_MIMETYPES),
    (VIDEO_CATEGORIES, VIDEO_MIMETYPES),
    (GIF_CATEGORIES, GIF_MIMETYPES),
    (SUBTITLE_CATEGORIES, SUBTITLE_MIMETYPES)
]

MIN_SEGMENT_BYTES = 4194304  # optimized_sru_parameters_min_segment_bytes
MAX_SEGMENT_BYTES = 8387584  # optimized_sru_parameters_max_segment_bytes

media_mimetypes = mimetypes.MimeTypes()
media_mimetypes.add_type('image/webp', '.webp')


def validate_mimetype(mimetype, media_category):
    match = next(
        filter(
            lambda x: media_category in x[0],
            CATEGORIES_MIMETYPES_MAPPING
        ), None
    )
    if match is None:
        raise ValueError(f'Unknown media category: "{media_category}"')

    mimetypes = match[1]
    if mimetype not in mimetypes:
        raise ValueError(
            f'Invalid mimetype "{mimetype}" for category '
            f'"{media_category}". Supported formats: {mimetypes}'
        )


def filetype_guess_mimetype(source):
    """
    Use filetype library to determine totalbytes for bytes or bufferio.
    """
    try:
        import filetype
    except ModuleNotFoundError:
        raise ImportError(
            'The "filetype" library is required to guess mimetypes from bytes or buffers. '
            'Please install filetype or provide the "mimetype" argument explicitly.'
        )
    mime = filetype.guess_mime(source)
    if not mime:
        raise ValueError('Could not determine mimetype.')
    return mime


class BaseSource(ABC):
    def __init__(self, source) -> None:
        self.source = source
        self.opened = False

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def get_mimetype(self) -> str:
        pass

    @abstractmethod
    def as_buffer(self) -> BufferedIOBase:
        pass

    @contextmanager
    def normalize(self):
        try:
            buf = self.as_buffer()
            yield buf
        finally:
            if self.opened:
                buf.close()
                self.opened = False


class PathSource(BaseSource):
    def __init__(self, source: str | Path) -> None:
        if isinstance(source, str):
            source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f'"{source}" not found.')
        super().__init__(source)

    def get_size(self):
        return self.source.stat().st_size

    def get_mimetype(self):
        mime = media_mimetypes.guess_type(self.source)[0]
        if not mime:
            raise ValueError('Could not determine mimetype.')
        return mime

    def as_buffer(self):
        self.opened = True
        return self.source.open('rb')


class BytesSource(BaseSource):
    source: bytes

    def get_size(self):
        return len(self.source)

    def get_mimetype(self):
        return filetype_guess_mimetype(self.source)

    def as_buffer(self):
        self.opened = True
        return BytesIO(self.source)


class BufferIOSource(BaseSource):
    source: BufferedIOBase

    def get_size(self):
        pos = self.source.tell()
        try:
            self.source.seek(0, 2)
            return self.source.tell()
        finally:
            self.source.seek(pos)

    def get_mimetype(self) -> str:
        pos = self.source.tell()
        try:
            self.source.seek(0)
            return filetype_guess_mimetype(self.source)
        finally:
            self.source.seek(pos)

    def as_buffer(self):
        self.source.seek(0)
        return self.source


def create_source(source) -> BaseSource:
    if isinstance(source, (str, Path)):
        return PathSource(source)
    elif isinstance(source, bytes):
        return BytesSource(source)
    elif isinstance(source, BufferedIOBase):
        return BufferIOSource(source)
    else:
        raise TypeError(f'Unsupported source type: "{source.__class__.__name__}"')


def get_video_duration_ms(source: BufferedIOBase) -> float | int:
    try:
        import av
    except ModuleNotFoundError:
        logger.warning('Skipping video duration detection: PyAV is required to determine video duration.')
        return
    with av.open(source) as container:
        if container.duration:
            duration_ms = float(container.duration / av.time_base) * 1000
            if duration_ms.is_integer():
                duration_ms = int(duration_ms)
            logger.info(f'Video duration ms: {duration_ms}')
            return duration_ms

    logger.warning('Failed to determine video duration.')


class MediaUploader:
    def __init__(
        self,
        api: API,
        source: str | Path | bytes | BufferedIOBase,
        media_category: MediaCategory,
        mimetype: str | None = None,
        concurrency: int = 6,
        enable_video_duration: bool = True
    ) -> None:
        self.api = api
        self.media_category = media_category
        self.source = create_source(source)
        self.mimetype = mimetype or self.source.get_mimetype()
        validate_mimetype(self.mimetype, media_category)
        self.total_bytes = self.source.get_size()
        self.concurrency = concurrency
        self.enable_video_duration = enable_video_duration

    async def init(self):
        video_duration_ms = None
        if self.media_category in VIDEO_CATEGORIES and self.enable_video_duration:
            with self.source.normalize() as buf:
                # get video duration for video using PyAV
                # not required but it's recommend to add it to imitate the original behavior.
                video_duration_ms = get_video_duration_ms(buf)
        response = await self.api.v11.upload_media_init(
            total_bytes=self.total_bytes,
            media_type=self.mimetype,
            video_duration_ms=video_duration_ms,
            media_category=self.media_category
        )
        payload = load_json_response(response)
        media_id = payload.get('media_id_string')
        if not media_id:
            raise ValueError(f'media_id not found. Response: "{payload}"')
        return media_id

    def segments(self):
        # generates segments
        with self.source.normalize() as buf:
            # The maximum size of the first segment is 4MB.
            segment = buf.read(MIN_SEGMENT_BYTES)
            if not segment:
                return
            yield 0, segment
            i = 1
            while True:
                segment = buf.read(MAX_SEGMENT_BYTES)
                if not segment:
                    break
                yield i, segment
                i += 1

    async def append_segments(self, media_id):
        # calclate md5 for images finalizing
        hasher = hashlib.md5() if self.media_category in IMAGE_CATEGORIES else None

        segments = self.segments()
        nxt = next(segments, None)
        if not nxt:
            raise ValueError('Cannot upload empty data.')
        _, segment = nxt
        if hasher:
            hasher.update(segment)
        # upload first segment synchronously to imitate the original behavior.
        await self.api.v11.upload_media_append(
            media_id=media_id,
            segment_index=0,
            data=segment
        )
        logger.info(f'Uploaded first segment, size={len(segment)}')

        sem = asyncio.Semaphore(self.concurrency)
        tasks = set()
        exception = None
        error_event = asyncio.Event()

        async def _upload_segment(index, segment):
            logger.info(f'Uploading segment {index}, size={len(segment)}')
            try:
                await self.api.v11.upload_media_append(
                    media_id=media_id,
                    segment_index=index,
                    data=segment
                )
                logger.info(f'Uploaded segment {index}')
            finally:
                sem.release()

        def _done_callback(task):
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                # set error event
                nonlocal exception
                if not exception:
                    exception = e
                error_event.set()
                logger.info(f'error occured in task {task.get_name()}')
                for t in list(tasks):
                    if not t.done():
                        logger.info(f'canceled task {t.get_name()}')
                        t.cancel()
            finally:
                tasks.discard(task)

        async def _uploader():
            while True:
                await sem.acquire()  # wait for semaphore released
                if error_event.is_set():
                    sem.release()
                    logger.info('Aborting segment submission loop due to error event.')
                    break
                nxt = next(segments, None)
                if not nxt:
                    break

                i, segment = nxt
                if hasher:
                    hasher.update(segment)
                task = asyncio.create_task(_upload_segment(i, segment))
                tasks.add(task)
                task.add_done_callback(_done_callback)

            if tasks:
                await asyncio.gather(*tasks)

        # wait for upload task done or error event set
        _, pending = await asyncio.wait(
            [
                asyncio.create_task(_uploader()),
                asyncio.create_task(error_event.wait())
            ],
            return_when=asyncio.FIRST_COMPLETED
        )
        for p in pending:
            p.cancel()

        if error_event.is_set():
            # raise the error if error_event.wait() finishes first.
            raise exception

        if hasher:
            return hasher.hexdigest()

    async def finalize(self, media_id, md5):
        allow_async = None
        if self.media_category in VIDEO_CATEGORIES:
            # unknown paramter for videos
            allow_async = True
        response = await self.api.v11.upload_media_finalize(
            media_id=media_id,
            original_md5=md5,
            allow_async=allow_async
        )
        return load_json_response(response)
