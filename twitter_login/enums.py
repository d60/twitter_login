from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class UserState(StrEnum):
    NORMAL = 'normal'
    SUSPENDED = 'suspended'
    NOT_LOGGED_IN = 'not_logged_in'


class SubtaskID(StrEnum):
    LOGIN_JS_INSTRUMENTATION_SUBTASK = 'LoginJsInstrumentationSubtask'
    LOGIN_ENTER_USER_IDENTIFIER_SSO = 'LoginEnterUserIdentifierSSO'
    LOGIN_ENTER_ALTERNATE_IDENTIFIER_SUBTASK = 'LoginEnterAlternateIdentifierSubtask'
    LOGIN_ENTER_PASSWORD = 'LoginEnterPassword'
    LOGIN_TWO_FACTOR_AUTH_CHALLENGE = 'LoginTwoFactorAuthChallenge'
    LOGIN_ACID = 'LoginAcid'
    LOGIN_SUCCESS_SUBTASK = 'LoginSuccessSubtask'
    DENY_LOGIN_SUBTASK = 'DenyLoginSubtask'


class MediaState(StrEnum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class MediaCategory(StrEnum):
    AMPLIFY_VIDEO = 'amplify_video'
    COMMUNITY_BANNER = 'community_banner_image'
    LIST_BANNER = 'list_banner_image'
    TWEET_IMAGE = 'tweet_image'
    TWEET_VIDEO = 'tweet_video'
    TWEET_GIF = 'tweet_gif'
    DM_IMAGE = 'dm_image'
    DM_VIDEO = 'dm_video'
    DM_GIF = 'dm_gif'
    SUBTITLES = 'subtitles'
    PROFILE_BANNER = 'banner_image'
    CARD_IMAGE = 'card_image'


class SensitiveMediaWarning(StrEnum):
    ADULT_CONTENT = 'adult_content'
    GRAPHIC_VIOLENCE = 'graphic_violence'
    OTHER = 'other'


class BatchCompose(StrEnum):
    SINGLE_TWEET = 'off'
    FIRST_TWEET = 'first'
    SUBSEQUENT_TWEET = 'subsequent'


class ConversationControl(StrEnum):
    COMMUNITY = 'Community'
    BY_INVITATION = 'ByInvitation'
    SUBSCRIBERS = 'Subscribers'
    VERIFIED = 'Verified'
    PREMIUM = 'Premium'


class SearchTimelineParam(StrEnum):
    IMAGE = 'image'
    LIST = 'list'
    LIVE = 'live'
    MEDIA = 'media'
    TOP = 'top'
    USER = 'user'
    VIDEO = 'video'


class SearchTimelineProduct(StrEnum):
    IMAGE = 'Photos'
    LIST = 'Lists'
    MEDIA = 'Media'
    TOP = 'Top'
    USER = 'People'
    VIDEO = 'Videos'
    LIVE = 'Latest'


SEARCH_TIMELINE_PRODUCT_TO_PARAM = {
    SearchTimelineProduct.IMAGE: SearchTimelineParam.IMAGE,
    SearchTimelineProduct.LIST: SearchTimelineParam.LIST,
    SearchTimelineProduct.MEDIA: SearchTimelineParam.MEDIA,
    SearchTimelineProduct.TOP: SearchTimelineParam.TOP,
    SearchTimelineProduct.USER: SearchTimelineParam.USER,
    SearchTimelineProduct.VIDEO: SearchTimelineParam.VIDEO,
    SearchTimelineProduct.LIVE: SearchTimelineParam.LIVE
}


class SearchTimelineQuerySource(StrEnum):
    ADVANCED_SEARCH_PAGE = 'advanced_search_page'
    CASHTAG_CLICK = 'cashtag_click'
    HASHTAG_CLICK = 'hashtag_click'
    PROMOTED_TREND_CLICK = 'promoted_trend_click'
    RECENT_SEARCH_CLICK = 'recent_search_click'
    RELATED_QUERY_CLICK = 'related_query_click'
    SPELLING_CORRECTION_CLICK = 'spelling_correction_click'
    SPELLING_CORRECTION_REVERT_CLICK = 'spelling_suggestion_revert_click'
    SPELLING_EXPANSION_CLICK = 'spelling_expansion_click'
    SPELLING_EXPANSION_REVERT_CLICK = 'spelling_expansion_revert_click'
    SPELLING_SUGGESTION_CLICK = 'spelling_suggestion_click'
    TREND_CLICK = 'trend_click'
    TREND_VIEW = 'trend_view'
    TYPEAHEAD_CLICK = 'typeahead_click'
    TYPED = 'typed_query'
    TV_SEARCH = 'TvSearch'
    TWEET_DETAIL_QUOTE_TWEET = 'tdqt'
    TWEET_DETAIL_SIMILAR_POST = 'tweet_detail_similar_posts'


class InstructionType(StrEnum):
    # Timeline
    TIMELINE_ADD_ENTRIES = 'TimelineAddEntries'
    TIMELINE_REMOVE_ENTRIES = 'TimelineRemoveEntries'
    TIMELINE_REPLACE_ENTRY = 'TimelineReplaceEntry'
    TIMELINE_ADD_TO_MODULE = 'TimelineAddToModule'
    TIMELINE_PIN_ENTRY = 'TimelinePinEntry'
    TIMELINE_SHOW_COVER = 'TimelineShowCover'
    TIMELINE_TERMINATE_TIMELINE = 'TimelineTerminateTimeline'
    TIMELINE_CLEAR_CACHE = 'TimelineClearCache'
    TIMELINE_SHOW_ALERT = 'TimelineShowAlert'
    TIMELINE_NAVIGATION = 'TimelineNavigation'
    TIMELINE_CLEAR_ENTRIES_UNREAD_STATE = 'TimelineClearEntriesUnreadState'
    TIMELINE_MARK_ENTRIES_UNREAD_GREATER_THAN_SORT_INDEX = 'TimelineMarkEntriesUnreadGreaterThanSortIndex'
