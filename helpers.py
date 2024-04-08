import base64
import datetime
from dataclasses import dataclass

import httpx


@dataclass
class Project:
    contract_addr: str
    start_idx: int
    end_idx: int
    name: str = ""

    def __init__(self, address: str, start: int, end: int):
        self.contract_addr = address
        self.start_idx = start
        self.end_idx = end

    def name_override(self, name: str) -> "Project":
        self.name = name
        return self


def encode_base64(string: str) -> str:
    return base64.b64encode(string.encode()).decode()


def get_url(rest_api_url: str, contract_addr: str, idx) -> str:
    value = '{"owner_of":{"token_id":"TOKEN"}}'.replace("TOKEN", str(idx))
    query = encode_base64(value).replace("=", "%3D")
    return f"""{rest_api_url}/cosmwasm/wasm/v1/contract/{contract_addr}/smart/{query}"""


def get_contract_info(rest_api_url: str, contract_addr: str) -> dict:
    if rest_api_url.endswith("/"):
        rest_api_url = rest_api_url[:-1]

    response = httpx.get(
        f"""{rest_api_url}/cosmwasm/wasm/v1/contract/{contract_addr}""",
        headers={
            "accept": "application/json",
        },
    )
    return response.json()


def fmt_time(now: datetime, format: str = "%Y_%b_%d_%H-%M-%S") -> str:
    """
    default format: 2024_apr_08_01-19-26
    """
    return now.strftime(format)
