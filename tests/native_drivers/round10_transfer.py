# this_file: tests/native_drivers/round10_transfer.py
"""Bound native JSON output by encoded size, never by glyph count."""

import base64
import hashlib
import json
from uuid import uuid4

CHUNK_SIZE = 8192
DIRECT_JSON_LIMIT = 12000  # Headroom for the host's outer JSON/string encoding.


def frame(value, storage):
    raw = json.dumps(value, ensure_ascii=True).encode("ascii")
    if len(raw) <= DIRECT_JSON_LIMIT:
        return value
    encoded = base64.b64encode(raw).decode("ascii")
    identifier = uuid4().hex
    storage[identifier] = encoded
    return {
        "_fontport_transfer": {
            "id": identifier,
            "length": len(encoded),
            "sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
        }
    }


def chunk(storage, identifier, offset):
    encoded = storage[identifier]
    if type(offset) is not int or not 0 <= offset < len(encoded):
        raise ValueError("Invalid transfer offset")
    return {"offset": offset, "data": encoded[offset : offset + CHUNK_SIZE]}


def decode(header, parts):
    encoded = "".join(parts)
    meta = header["_fontport_transfer"]
    if (
        len(encoded) != meta["length"]
        or hashlib.sha256(encoded.encode("ascii")).hexdigest() != meta["sha256"]
    ):
        raise ValueError("Incomplete/corrupt native transfer")
    return json.loads(base64.b64decode(encoded, validate=True))
