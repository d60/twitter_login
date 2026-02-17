import asyncio

import config
from twitter_login.login import Login


async def main():
    login = Login()
    await login.login(
        [config.USER_NAME, config.EMAIL], config.PASSWORD, 'cookies.json', config.TOTP
    )


asyncio.run(main())
