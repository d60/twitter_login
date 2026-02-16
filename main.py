import asyncio

import config
from twitter_login.login import Login


async def main():
    login = Login()
    await login.login([config.EMAIL, config.USER_NAME], config.PASSWORD, 'cookies.json')

asyncio.run(main())


