# this_file: src/fontlab_fontport/ufo_features.py
# SPDX-License-Identifier: Apache-2.0
"""Lossless UFO feature source slices, independent of native history parsing.

This boundary identifies named declarations without compiling their bodies.
Ambiguous boundaries remain one opaque prefix and permit only exact no-ops.
"""
from collections.abc import Mapping
from typing import Any

from .info import _text


def _space_end(text: str, index: int) -> int:
    """Skip only whitespace and line comments, preserving the source itself."""
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text[index] == '#':
            while index < len(text) and text[index] not in '\r\n':
                index += 1
        else:
            break
    return index


def _tokens(text: str) -> tuple[list[tuple[str, int, bool]], str | None]:
    """Return boundary tokens; quoted text and include filenames stay inert."""
    tokens = []
    index = 0
    while (index := _space_end(text, index)) < len(text):
        start = index
        char = text[index]
        if char == '"':
            end = text.find('"', index + 1)
            if end < 0:
                return [], 'unterminated quoted text'
            tokens.append((text[index:end + 1], start, False))
            index = end + 1
            continue
        if char in '{}();':
            tokens.append((char, start, False))
            index += 1
            continue
        while index < len(text) and not text[index].isspace() and text[index] not in '#"{}();':
            index += 1
        word = text[start:index]
        after = _space_end(text, index)
        if word == 'include' and text[after:after + 1] == '(':
            end = text.find(')', after + 1)
            if end < 0:
                return [], 'unterminated include filename'
            tokens.append((text[start:end + 1], start, False))
            index = end + 1
        else:
            tokens.append((word, start, not word.startswith(('@', '\\'))))
    return tokens, None


def _tag(tag: str) -> bool:
    return len(tag) == 4 and all('!' <= char <= '~' for char in tag)


def _partition(text: str) -> tuple[dict[str, Any], str | None]:
    """Use raw offsets for supported boundaries or retain the entire prefix."""
    _text(text, 'feature source')
    opaque = {'prefix': text, 'features': []}
    tokens, reason = _tokens(text)
    if reason:
        return opaque, reason
    starts = []
    braces = []
    feature_open = -1
    statement_start = True
    for index, (word, offset, bare) in enumerate(tokens):
        following = tokens[index + 1:index + 3]
        declaration = len(following) == 2 and following[0][2] and following[1][0] == '{'
        if bare and word in ('anon', 'anonymous') and not braces and declaration:
            return opaque, 'anonymous source block'
        if bare and word == 'feature':
            if declaration:
                tag, _, _ = following[0]
                if not _tag(tag):
                    return opaque, 'unsupported feature tag'
                if braces:
                    return opaque, 'nested feature declaration'
                starts.append((tag, offset))
                feature_open = index + 2
            elif statement_start and not (len(following) == 2 and following[0][2] and following[1][0] == ';'):
                return opaque, 'incomplete feature header'
        if word == '{':
            braces.append(index == feature_open)
        elif word == '}':
            if not braces:
                return opaque, 'unmatched closing brace'
            braces.pop()
        statement_start = word in '{};'
    if braces and not braces[0]:
        return opaque, 'unterminated prefix brace region'
    if not starts:
        return opaque, None
    ends = [offset for _, offset in starts[1:]] + [len(text)]
    rows = [(tag, text[start:end]) for (tag, start), end in zip(starts, ends, strict=False)]
    return {'prefix': text[:starts[0][1]], 'features': rows}, None


def read_blocks(text: str) -> dict[str, Any]:
    """Return detached ordered raw slices, including duplicate named tags."""
    return _partition(text)[0]


def _requested(values: Mapping[str, Any]) -> dict[str, Any]:
    """Validate structured input without coercion or native staging rules."""
    if not isinstance(values, Mapping):
        raise TypeError('feature blocks require a mapping')
    if set(values) != {'prefix', 'features'}:
        raise ValueError('feature blocks require exactly prefix and features')
    prefix, features = values['prefix'], values['features']
    _text(prefix, 'feature prefix')
    if not isinstance(features, (list, tuple)):
        raise TypeError('features require an ordered list or tuple')
    rows = []
    for pair in features:
        if not isinstance(pair, (list, tuple)):
            raise TypeError('feature rows require pairs')
        if len(pair) != 2:
            raise ValueError('feature rows require exactly tag and source')
        tag, code = pair
        _text(tag, 'feature tag')
        _text(code, 'feature code')
        if not _tag(tag):
            raise ValueError('feature tags require four printable ASCII characters')
        rows.append((tag, code))
    return {'prefix': prefix, 'features': rows}


def stage_blocks(current: str, values: Mapping[str, Any]) -> str | None:
    """Return exact proposed text, or None for a true representation no-op.

    Callers must assign only a non-None result. Unsupported boundaries and
    changed segmentation raise before any backend mutation can begin.
    """
    requested = _requested(values)
    original, reason = _partition(current)
    if requested == original:
        return None
    if reason:
        raise ValueError(f'unsupported current feature source: {reason}')
    proposed = requested['prefix'] + ''.join(code for _, code in requested['features'])
    observed, reason = _partition(proposed)
    if reason:
        raise ValueError(f'unsupported requested feature source: {reason}')
    if observed != requested:
        raise ValueError('requested feature partition does not match raw source boundaries')
    return proposed
