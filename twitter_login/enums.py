from enum import Enum


class UserState(str, Enum):
    NORMAL = 'normal'
    SUSPENDED = 'suspended'
    NOT_LOGGED_IN = 'not_logged_in'


class SubtaskID(str, Enum):
    LOGIN_JS_INSTRUMENTATION_SUBTASK = 'LoginJsInstrumentationSubtask'
    LOGIN_ENTER_USER_IDENTIFIER_SSO = 'LoginEnterUserIdentifierSSO'
    LOGIN_ENTER_ALTERNATE_IDENTIFIER_SUBTASK = 'LoginEnterAlternateIdentifierSubtask'
    LOGIN_ENTER_PASSWORD = 'LoginEnterPassword'
    LOGIN_TWO_FACTOR_AUTH_CHALLENGE = 'LoginTwoFactorAuthChallenge'
    LOGIN_ACID = 'LoginAcid'
    LOGIN_SUCCESS_SUBTASK = 'LoginSuccessSubtask'
    DENY_LOGIN_SUBTASK = 'DenyLoginSubtask'


class MediaStatus(str, Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class MediaCategory(str, Enum):
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
