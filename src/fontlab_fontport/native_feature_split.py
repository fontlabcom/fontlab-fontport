# this_file: src/fontlab_fontport/native_feature_split.py
"""Pure simulation of FontGate's whole-text feature history reader.

Source: FontGate/opentype/l_fea.cpp:3037–3070,3362–3560 and
layout.cpp:741–749. Work on UTF-8 byte offsets, as the native char* code does.
This is a tokenizer/storage simulation, not an FEA grammar or compiler.
"""

_DELIMITERS = b" \t\n\r[];,'\\-={"


def _strtok(buffer: bytearray, cursor: int | None, delimiters: bytes):
    """Return token bounds/continuation, replacing its delimiter with NUL."""
    if cursor is None or cursor >= len(buffer):
        return None
    while buffer[cursor] in delimiters:
        cursor += 1
    if buffer[cursor] == 0:
        return None
    end = cursor
    while buffer[end] and buffer[end] not in delimiters:
        end += 1
    following = end + 1 if buffer[end] else None
    buffer[end] = 0
    return cursor, end, following


def _strstrtok(buffer: bytearray, start: int, search: bytes) -> int | None:
    """Mirror native comment-mode selection and destructive strtok searches."""
    tail = buffer.index(0, start)
    if tail - start <= 1:
        return None
    cursor, probe, first = start, start, True
    while True:
        while buffer[probe] in _DELIMITERS and probe < tail - 1:
            probe += 1
        if first:
            cursor, first = probe, False
        delimiters = b"\r\n" if buffer[probe] == ord("#") else _DELIMITERS
        token = _strtok(buffer, cursor, delimiters)
        if token is None:
            return None
        position, end, cursor = token
        if buffer[position:end] == search:
            return position
        probe = end + 1


def _without_name_table(source: bytes) -> bytes:
    """loadTablesTextInfo extracts the first non-commented table name region."""
    output, in_table = [], False
    # getline uses LF only (CR remains data), with source.size() as its limit.
    pieces = source.split(b"\n")
    lines = [
        piece + (b"\n" if index < len(pieces) - 1 else b"")
        for index, piece in enumerate(pieces)
    ]
    if len(lines) == 1 and source:
        lines[0] = source[:-1]  # Native getline's size-1 limit on a single line.
    for index, line in enumerate(lines):
        stripped = line.strip(b" \t\r\n")
        if stripped and not stripped.startswith(b"#"):
            if not in_table and b"table name" in stripped:
                in_table = True
            if in_table and b"} name;" in stripped:
                # A full single-line getline sets failbit at size-1. The
                # subsequent rdbuf() still emits its unread final source byte.
                unread = source[-1:] if len(lines) == 1 else b""
                return b"".join(output + lines[index + 1 :]) + unread
        if not in_table:
            output.append(line)
    return b"".join(output)


def _stored_text(source: bytes) -> str:
    """FeaTextBlock appends LF to every nonempty fragment lacking final LF."""
    if source and not source.endswith(b"\n"):
        source += b"\n"
    return source.decode("utf-8")


def split_history_text(text: str) -> dict:
    """Return the prefix/ordered codes reconstructed by native history loading.

    Comments are line tokens. After a header, the first matching tag token is
    sought before searching for another feature keyword. Body references are
    therefore not split points. Duplicate tags keep the first block; aalt moves
    to the front, exactly as putTextBlock(..., rewrite=false) does.
    """
    source = _without_name_table(text.encode("utf-8"))
    if b"\0" in source:
        raise ValueError("Native feature history cannot contain NUL")
    buffer = bytearray(source + b"\0\0")
    token = _strstrtok(buffer, 0, b"feature")
    prefix_bytes = source[:token] if token is not None else source
    # Native plain char is signed on the target host; data_present tests > 32.
    prefix = (
        _stored_text(prefix_bytes) if any(32 < c < 128 for c in prefix_bytes) else ""
    )
    features, seen = [], set()
    while token is not None:
        begin, header_start = token, token + 8
        header = _strtok(buffer, header_start, _DELIMITERS)
        if header is None:
            raise ValueError(f"Native feature header has no tag at byte {begin}")
        position, end, _ = header
        tag = bytes(buffer[position:end])
        if len(tag) < 5:
            closing = _strstrtok(buffer, header_start + len(tag) + 1, tag)
            token = (
                None
                if closing is None
                else _strstrtok(buffer, closing + len(tag) + 1, b"feature")
            )
        else:
            token = _strstrtok(buffer, header_start, b"feature")
        if tag not in seen:
            pair = (tag.decode("utf-8"), _stored_text(source[begin:token]))
            features.insert(0, pair) if tag == b"aalt" else features.append(pair)
            seen.add(tag)
    return {"prefix": prefix, "features": features}
