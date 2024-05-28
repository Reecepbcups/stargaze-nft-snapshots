import base64
import datetime
import json
from dataclasses import dataclass

import httpx


@dataclass
class Project:
    contract_addr: str
    start_idx: int
    end_idx: int
    name: str = ""
    dao_voting_module: str = ""

    def __init__(self, address: str, start: int, end: int):
        self.contract_addr = address
        self.start_idx = start
        self.end_idx = end

    def name_override(self, name: str) -> "Project":
        self.name = name
        return self

    # starsd q wasm contract-state smart stars17fdkf8ccpuj2v677w3f246hwku5anwt5800wm0t7prrv5gn8r0ys298hl2 '{"dump_state":{}}'
    # - voting module
    def set_dao_voting_module(self, dao_addr: str) -> "Project":
        # starsd q wasm contract-state smart stars1yyl590s37cpdm3v25p4vjrzgtxjgm6rlkc0584gu898syqewcc0q4zllks '{"dump_state":{}}'
        self.dao_voting_module = dao_addr
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


fileFmt = "%Y_%b_%d"


def fmt_time(now: datetime, format: str = fileFmt) -> str:
    """
    default format: 2024_Apr_08
    """
    return now.astimezone(datetime.timezone.utc).strftime(format)


class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)
    """Container datatypes include primitives or other containers."""

    # MAX_WIDTH = 70
    """Maximum width of a container that might be put on a single line."""

    # MAX_ITEMS = 10
    """Maximum number of items in container that might be put on single line."""

    def __init__(self, *args, **kwargs):
        # using this class without indentation is pointless
        if kwargs.get("indent") is None:
            kwargs["indent"] = 4
        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            return self._encode_list(o)
        if isinstance(o, dict):
            return self._encode_object(o)
        if isinstance(o, float):  # Use scientific notation for floats
            return format(o, "g")
        return json.dumps(
            o,
            skipkeys=self.skipkeys,
            ensure_ascii=self.ensure_ascii,
            check_circular=self.check_circular,
            allow_nan=self.allow_nan,
            sort_keys=self.sort_keys,
            indent=self.indent,
            separators=(self.item_separator, self.key_separator),
            default=self.default if hasattr(self, "default") else None,
        )

    def _encode_list(self, o):
        if self._put_on_single_line(o):
            return "[" + ", ".join(self.encode(el) for el in o) + "]"
        self.indentation_level += 1
        output = [self.indent_str + self.encode(el) for el in o]
        self.indentation_level -= 1
        return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"

    def _encode_object(self, o):
        if not o:
            return "{}"

        # ensure keys are converted to strings
        o = {str(k) if k is not None else "null": v for k, v in o.items()}

        if self.sort_keys:
            o = dict(sorted(o.items(), key=lambda x: x[0]))

        if self._put_on_single_line(o):
            return (
                "{ "
                + ", ".join(
                    f"{json.dumps(k)}: {self.encode(el)}" for k, el in o.items()
                )
                + " }"
            )

        self.indentation_level += 1
        output = [
            f"{self.indent_str}{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()
        ]
        self.indentation_level -= 1

        return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"

    def iterencode(self, o, **kwargs):
        """Required to also work with `json.dump`."""
        return self.encode(o)

    def _put_on_single_line(self, o):
        return (
            self._primitives_only(o)
            # and len(o) <= self.MAX_ITEMS
            # and len(str(o)) - 2 <= self.MAX_WIDTH
        )

    def _primitives_only(self, o: list | tuple | dict):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        if isinstance(self.indent, int):
            return " " * (self.indentation_level * self.indent)
        elif isinstance(self.indent, str):
            return self.indentation_level * self.indent
        else:
            raise ValueError(
                f"indent must either be of type int or str (is: {type(self.indent)})"
            )
