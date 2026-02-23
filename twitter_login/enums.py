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
