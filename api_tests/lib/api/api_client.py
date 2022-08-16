import os
from pathlib import Path

import requests
from dotenv import load_dotenv

config_dir = Path(__file__).parent.parent.parent
dotenv_file = config_dir / f'.env'

load_dotenv(dotenv_file)
BASE_URL = os.environ.get("BASE_URL")
default_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


class ApiRequest:
    def __init__(self, path: str, method: str, headers=None):
        if headers is None:
            headers = default_headers
        self._path = path
        self._method = method
        self._headers = headers

    def request(self, params):
        url = BASE_URL + self._path
        headers = self._headers
        print('url: ' + url)
        print('params')
        print(params)
        return requests.request(
            method=self._method,
            url=url,
            params=params,
            headers=headers,
        )

    def request_with_formdata(self, payload):
        url = BASE_URL + self._path
        print('url: ' + url)
        print('payload')
        print(payload)
        return requests.request(
            method=self._method,
            url=url,
            data=payload,
            files=payload
        )