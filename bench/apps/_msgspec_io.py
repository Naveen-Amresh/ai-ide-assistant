"""msgspec request model, decoder and encoder shared by the non-ASGI-framework apps."""

from typing import Annotated

import msgspec


class ItemIn(msgspec.Struct):
    name: Annotated[str, msgspec.Meta(min_length=1, max_length=100)]
    price: Annotated[float, msgspec.Meta(gt=0)]
    quantity: Annotated[int, msgspec.Meta(ge=0)]
    tags: list[str] = []


decode_item = msgspec.json.Decoder(ItemIn).decode
encode = msgspec.json.Encoder().encode
HELLO = encode({"message": "Hello, World!"})
ValidationError = msgspec.ValidationError
DecodeError = msgspec.DecodeError
