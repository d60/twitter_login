from STPyV8 import JSError

from .api import API
from .castle_token import CastleToken
from .constants import INIT_FLOW_PAYLOAD
from .http import HTTPClient
from .ui_metrics import solve_ui_metrics


class LoginFlow:
    def __init__(self, http: HTTPClient, api: API, castle: CastleToken):
        self.http = http
        self.api = api
        self.flow_token = None
        self.subtasks = []
        self.subtask_inputs = {}
        self.castle = castle

    def get_subtask(self, subtask_id):
        return next(
            filter(
                lambda x: x.get('subtask_id') == subtask_id,
                self.subtasks
            ),
            None
        )

    def process_response(self, response):
        data = response.json()
        flow_token = data.get('flow_token')
        subtasks = data.get('subtasks')
        if flow_token is None:
            raise ValueError('flow_token not found in response.')
        if subtasks is None:
            raise ValueError('subtasks not found in response.')
        self.flow_token = flow_token
        self.subtasks = subtasks

    async def init_flow(self):
        data = INIT_FLOW_PAYLOAD
        response = await self.api.v11.onboarding_task(
            data, {'flow_name': 'login'}
        )
        self.process_response(response)

    async def execute_subtasks(self):
        subtask_inputs = [
            {'subtask_id': id, **data}
            for id, data in self.subtask_inputs.items()
        ]
        data = {
            'flow_token': self.flow_token,
            'subtask_inputs': subtask_inputs
        }
        response = await self.api.v11.onboarding_task(data)
        self.process_response(response)
        self.subtask_inputs.clear()

    async def LoginJsInstrumentationSubtask(self):
        subtask = self.get_subtask('LoginJsInstrumentationSubtask')
        js_url = subtask['js_instrumentation']['url']
        headers = self.http.build_headers(authorization=False)
        js_response = await self.http.get(js_url, headers=headers, use_transaction_id=False)
        ui_metrics = js_response.text
        try:
            answer = solve_ui_metrics(ui_metrics)
        except JSError as e:
            raise RuntimeError('An error occurred while solving ui metrics') from e

        self.subtask_inputs['LoginJsInstrumentationSubtask'] = {
            'js_instrumentation': {
                'response': answer,
                'link': 'next_link'
            }
        }

    def LoginEnterUserIdentifierSSO(self, user_identifier):
        self.subtask_inputs['LoginEnterUserIdentifierSSO'] = {
            'settings_list': {
                'setting_responses': [
                    {
                        'key': 'user_identifier',
                        'response_data': {
                            'text_data': {
                                'result': user_identifier
                            }
                        }
                    }
                ],
                'link': 'next_link',
                'castle_token': self.castle.create_token()
            }
        }

    def LoginEnterAlternateIdentifierSubtask(self, user_identifier):
        self.subtask_inputs['LoginEnterAlternateIdentifierSubtask'] = {
            'enter_text': {
                'link': 'next_link',
                'text': user_identifier,
                'castle_token': self.castle.create_token()
            }
        }

    def LoginEnterPassword(self, password):
        self.subtask_inputs['LoginEnterPassword'] = {
            'enter_password': {
                'password': password,
                'link': 'next_link',
                'castle_token': self.castle.create_token()
            }
        }

    def LoginTwoFactorAuthChallenge(self, totp_code):
        self.subtask_inputs['LoginTwoFactorAuthChallenge'] = {
            'enter_text': {
                'text': totp_code,
                'link': 'next_link',
                'castle_token': self.castle.create_token()
            }
        }

    def LoginAcid(self, confirmation_code):
        self.subtask_inputs['LoginAcid'] = {
            'enter_text': {
                'link': 'next_link',
                'text': confirmation_code,
                'castle_token': self.castle.create_token()
            }
        }

    async def sso_init(self):
        await self.api.v11.onboarding_sso_init('apple')
