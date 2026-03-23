"""Per-stem bytes appended to engine BFS dedup keys when the frame omits critical state."""

from __future__ import annotations

from collections.abc import Callable


def extra_state_key_for_stem(stem: str) -> Callable[[object], bytes] | None:
    """Return a function ``env -> bytes`` or None if the default frame key suffices."""

    if stem == "dl01":

        def _dl01(env: object) -> bytes:
            q = getattr(getattr(env, "_game", None), "_q", None)
            if q is None:
                return b""
            return repr(list(q)).encode()

        return _dl01

    if stem == "hd01":

        def _hd01(env: object) -> bytes:
            g = getattr(env, "_game", None)
            if g is None:
                return b""
            return repr(
                (
                    getattr(g, "_immune", 0),
                    getattr(g, "_heat_row", -1),
                    getattr(g, "_steps", 0),
                )
            ).encode()

        return _hd01

    if stem == "bt01":

        def _bt01(env: object) -> bytes:
            g = getattr(env, "_game", None)
            if g is None:
                return b""
            return repr((getattr(g, "_charge", 0),)).encode()

        return _bt01

    if stem == "rh01":

        def _rh01(env: object) -> bytes:
            g = getattr(env, "_game", None)
            if g is None:
                return b""
            return repr(
                (
                    getattr(g, "_danger_y", 0),
                    getattr(g, "_ticks", 0),
                )
            ).encode()

        return _rh01

    return None
