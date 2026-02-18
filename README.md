Use example of https://github.com/d60/twitter_castle_token


```python
import asyncio

import config
from twitter_login.login import Login


async def main():
    login = Login()
    await login.login(
        ['your_username', 'email@example.com'], 'password1234', 'cookies.json', 'your TOTP secret (optional)'
    )


asyncio.run(main())
```
