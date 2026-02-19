def default_two_fa_handler():
    return input(f'Enter 2FA code: ')


def default_email_confirmation_handler():
    return input(f'Enter email confirmation code: ')


class SecretTwoFAHandler:
    def __init__(self, secret) -> None:
        self.secret = secret

    def __call__(self) -> str:
        from pyotp import TOTP
        return TOTP(self.secret).now()
