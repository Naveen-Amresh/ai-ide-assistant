"""FastAPI + msgspec (decode/validate and encode) + asyncpg: the fastest FastAPI stack on 3.15t."""

from typing import Annotated

import msgspec

from apps._fastapi_raw import build


class ItemIn(msgspec.Struct):
    name: Annotated[str, msgspec.Meta(min_length=1, max_length=100)]
    price: Annotated[float, msgspec.Meta(gt=0)]
    quantity: Annotated[int, msgspec.Meta(ge=0)]
    tags: list[str] = []


_decoder = msgspec.json.Decoder(ItemIn)
_encoder = msgspec.json.Encoder()


def _parse(body: bytes) -> ItemIn:
    try:
        return _decoder.decode(body)
    except msgspec.ValidationError as exc:
        raise ValueError(str(exc)) from exc


# msgspec encodes datetime natively, so rows only need dict(), no isoformat() pass.
app = build("fastapi-msgspec", _encoder.encode, parse=_parse, to_obj=dict)
