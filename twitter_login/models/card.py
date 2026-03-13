from enum import Enum

from .base import model


class CardName(str, Enum):
    AMPLIFY = 'amplify'
    APP = 'app'  # app sharing
    AUDIOSPACE = '3691233323:audiospace'  # audio space card
    BROADCAST = '745291183405076480:broadcast'  # live broadcast
    DIRECT_STORE_LINK_APP = 'direct_store_link_app'
    DEVELOPER_BUILT_CARD = 'DeveloperCard'
    DEVELOPER_BUILT_CARD_DEPRECATED = 'DeveloperCardDeprecated'
    FOLLOWER_CARD = 'FollowerCard'
    IMAGE_DIRECT_MESSAGE = '2586390716:image_direct_message'
    LIVE_EVENT = '745291183405076480:live_event'  # Moments deprecated
    MESSAGE_ME = '2586390716:message_me'  # the "send us a private message" button
    MOMENT = '3260518932:moment'
    NEWSLETTER_ISSUE = '3337203208:newsletter_issue'
    NEWSLETTER_PUBLICATION = '3337203208:newsletter_publication'
    NOTE = '1493954797359222784:note'
    PERISCOPE_BROADCAST = '3691233323:periscope_broadcast'  # Periscope live
    PLAYER = 'player'  # video player for example YouTube
    POLL_2_CHOICE_TEXT = 'poll2choice_text_only'  # poll
    POLL_3_CHOICE_TEXT = 'poll3choice_text_only'  # poll
    POLL_4_CHOICE_TEXT = 'poll4choice_text_only'  # poll
    POLL_2_CHOICE_IMAGE = 'poll2choice_image'  # poll
    POLL_3_CHOICE_IMAGE = 'poll3choice_image'  # poll
    POLL_4_CHOICE_IMAGE = 'poll4choice_image'  # poll
    POLL_2_CHOICE_VIDEO = 'poll2choice_video'  # poll
    POLL_3_CHOICE_VIDEO = 'poll3choice_video'  # poll
    POLL_4_CHOICE_VIDEO = 'poll4choice_video'  # poll
    IMAGE_POLL = '1906814671912599552:poll_choice_images'  # poll
    PROMO_IMAGE_CONVO = 'promo_image_convo'  # https://business.x.com/en/help/campaign-setup/conversation-buttons
    PROMO_VIDEO_CONVO = 'promo_video_convo'  # https://business.x.com/en/help/campaign-setup/conversation-buttons
    SUMMARY = 'summary'  # normal summary
    SUMMARY_LARGE_IMAGE = 'summary_large_image'  # summary with large image
    UNIFIED_CARD = 'unified_card'  # sharing grok, list, trends, etc.
    VIDEO_DIRECT_MESSAGE = '2586390716:video_direct_message'

POLL_NAMES = [
    CardName.POLL_2_CHOICE_TEXT,
    CardName.POLL_3_CHOICE_TEXT,
    CardName.POLL_4_CHOICE_TEXT,
    CardName.POLL_2_CHOICE_IMAGE,
    CardName.POLL_3_CHOICE_IMAGE,
    CardName.POLL_4_CHOICE_IMAGE,
    CardName.POLL_2_CHOICE_VIDEO,
    CardName.POLL_3_CHOICE_VIDEO,
    CardName.POLL_4_CHOICE_VIDEO,
    CardName.IMAGE_POLL
]


@model(reprs=('id', 'name'))
class Card:
    id: str
    name: str
    url: str
    values: dict[str, dict]

    @classmethod
    def _from_payload(cls, payload: dict):
        legacy = payload.get('legacy', {})
        values_dict = {
            v['key']: v['value']
            for v in legacy.get('binding_values', [])
        }
        return cls(
            id=payload.get('rest_id'),
            name=legacy.get('name'),
            url=legacy.get('url'),
            values=values_dict
        )
