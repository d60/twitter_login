from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from curl_cffi import CurlMime

from ..headers import FetchDest, HeadersConfig
from .utils import UNSET, remove_unset

if TYPE_CHECKING:
    from ..http import HTTPClient

logger = getLogger(__name__)


class V11Client:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    async def onboarding_task(self, data, params = None):
        headers_config = HeadersConfig.general_api(referer='https://x.com/', extra_headers={
            'x-guest-token': self.http.guest_token,
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en'
        })
        return await self.http.post(
            'https://api.x.com/1.1/onboarding/task.json',
            headers_config,
            params=params,
            json=data
        )

    async def onboarding_sso_init(self, provider):
        headers_config = HeadersConfig.general_api(referer='https://x.com/', extra_headers={
            'x-guest-token': self.http.guest_token,
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en'
        })
        data = {'provider': provider}
        return await self.http.post(
            'https://api.x.com/1.1/onboarding/sso_init.json',
            headers_config,
            json=data,
        )

    async def _upload_media(self, method, **kwargs):
        headers_config = HeadersConfig(
            dest=FetchDest.FETCH,
            referer='https://x.com/',
            extra_headers={
                'x-twitter-auth-type': 'OAuth2Session'
            }
        )
        return await self.http.request(method, 'https://upload.x.com/i/media/upload.json', headers_config, **kwargs)

    async def upload_media_init(self, *, total_bytes, media_type, video_duration_ms, media_category):
        """
        Params:
            total_bytes:
                bytes size of madia (File.size file interface API)
            media_type:
                mimetype (File.type file interface API)
            video_duration_ms:
                (Not required)
                HTMLVideoElement.duration*1000
            media_category:
                Omit when uploading a profile picture. (Not required)
                "amplify_video"          - tweet video (duration < 10 minutes (media_async_upload_amplify_duration_threshold))
                "community_banner_image" - community banner
                "list_banner_image"      - list banner
                "tweet_image"            - tweet image
                "tweet_gif"              - tweet gif
                "dm_video"               - maybe for tweet videos longer than 10 minutes (premium feature)
                "subtitles"              - subtitles (.srt file)
                "banner_image"           - profile banner image
                "card_image"             - poll image

                "tweet_video"
                "dm_image"
                "dm_gif"

            caption : "text/plain charset=utf-8"
            image   : "image/jpeg", "image/png", "image/webp"
            gif     : "image/gif"
            video   : "video/mp4", "video/quicktime"
        """
        params = remove_unset({
            'command': 'INIT',
            'total_bytes': total_bytes,
            'media_type': media_type,
            'video_duration_ms': video_duration_ms or UNSET,
            'media_category': media_category
        })
        logger.info(params)
        return await self._upload_media('POST', params=params)

    async def upload_media_append(self, *, media_id, segment_index, data):
        params = {
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': segment_index
        }
        mp = CurlMime()
        mp.addpart(
            name='media',
            content_type='application/octet-stream',
            filename='blob',
            data=data
        )
        return await self._upload_media('POST', params=params, multipart=mp)

    async def upload_media_finalize(self, *, media_id, original_md5, allow_async):
        params = remove_unset({
            'command': 'FINALIZE',
            'media_id': media_id,
            'original_md5': original_md5 or UNSET,
            'allow_async': allow_async or UNSET
        })
        logger.info(params)
        return await self._upload_media('POST', params=params)

    async def upload_media_status(self, *, media_id):
        params = {
            'command': 'STATUS',
            'media_id': media_id
        }
        return await self._upload_media('GET', params=params)

    async def media_metadata_create(self, *, media_id, alt_text, sensitive_media_warning, allow_download_status, grok_actions):
        """
        media_id
            str
        alt_text
            text: str
        sensitive_media_warning
            options: ["adult_content", "graphic_violence", "other"]
        allow_download_status
            allow_download: bool
        grok_actions
            block_grok_edit: bool
        """
        headers_config = HeadersConfig.general_api(
            referer='https://x.com/compose/post',
            extra_headers={
                'x-twitter-active-user': 'yes',
                'x-twitter-auth-type': 'OAuth2Session',
                'x-twitter-client-language': 'en'
            }
        )
        data = remove_unset({
            'media_id': media_id,
            'alt_text': alt_text or UNSET,
            'sensitive_media_warning': UNSET if sensitive_media_warning is None else sensitive_media_warning,
            'allow_download_status': allow_download_status or UNSET,
            'grok_actions': grok_actions or UNSET
        })
        return await self.http.post('https://x.com/i/api/1.1/media/metadata/create.json', headers_config, json=data)

    async def media_subtitles_create(self, *, media_id, media_category, subtitle_info):
        """
        All supported languages: https://x.com/i/api/graphql/fZ5uZVeledO5SAseKnmTUg/SupportedLanguages?variables=%7B%7D
        subtitles: [{media_id: "2028725106865033216", language_code: "en", display_name: "English"}]
        """
        headers_config = HeadersConfig.general_api(
            referer='https://x.com/compose/post',
            extra_headers={
                'x-twitter-active-user': 'yes',
                'x-twitter-auth-type': 'OAuth2Session',
                'x-twitter-client-language': 'en'
            }
        )
        data = {
            'media_id': media_id,
            'media_category': media_category,
            'subtitle_info': subtitle_info
        }
        return await self.http.post('https://x.com/i/api/1.1/media/subtitles/create.json', headers_config, json=data)
