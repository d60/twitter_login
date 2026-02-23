class TwitterException(Exception):
    ...


class HTTPError(TwitterException):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f'{status_code}: {message}')


class LoginError(TwitterException):
    ...


class DenyLoginSubtaskError(LoginError):
    ...


class AccountError(TwitterException):
    ...


class AccountSuspended(AccountError):
    ...


class NotLoggedIn(AccountError):
    ...
