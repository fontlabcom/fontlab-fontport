# this_file: src/fontlab_fontport/lifetime.py
"""Check owner lifetime once per synchronous public operation."""

from contextvars import ContextVar
from functools import wraps
from inspect import getattr_static, isfunction


class AdapterIdentity:
    """Stable adapter identity and session-only scratch data, never serialized."""

    def naked(self):
        return self._naked

    @property
    def _naked(self):
        return self

    def _get_tempLib(self):
        from fontParts.base import BaseFont, BaseLayer
        from fontParts.fontshell import RLib

        if "_scratch_lib" not in self.__dict__:
            self._scratch_lib = RLib()
        if isinstance(self, (BaseFont, BaseLayer)):
            self._scratch_lib.font = self
        return self._scratch_lib

    @property
    def tempLib(self):
        return self._get_tempLib()


class OwnedAccess(AdapterIdentity):
    def raiseNotImplementedError(self):
        import sys

        from .errors import UnsupportedCapability

        method = sys._getframe(1).f_code.co_name
        raise UnsupportedCapability(
            f"{type(self).__name__}.{method}",
            "This adapter does not implement the requested FontParts operation",
        )

    def __getattribute__(self, name):
        def check():
            owner = object.__getattribute__(self, "__dict__").get("_owner")
            if owner is not None:
                owner._check()

        return public_access(self, name, super().__getattribute__, check)


# A synchronous public call owns this cache; it never survives an event-loop turn.
_active_checks = ContextVar("fontport_entry_checks", default=None)


def once_per_entry(method):
    @wraps(method)
    def checked(self, *args, **kwargs):
        active = _active_checks.get()
        key = (id(self), method)
        if active is not None and key in active:
            return None
        result = method(self, *args, **kwargs)
        if active is not None:
            active.add(key)
        return result

    return checked


def public_access(obj, name, getter, check):
    """Scope nested reads to one check; a retained method checks when called."""
    if name.startswith("_"):
        return getter(name)
    raw = getattr_static(type(obj), name, None)

    def invoke(operation):
        token = None
        if _active_checks.get() is None:
            token = _active_checks.set(set())
        try:
            check()
            return operation()
        finally:
            if token is not None:
                _active_checks.reset(token)

    if isfunction(raw):

        @wraps(raw)
        def call(*args, **kwargs):
            return invoke(lambda: getter(name)(*args, **kwargs))

        return call
    return invoke(lambda: getter(name))
