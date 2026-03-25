"""Merged table of per-stem registry GIF recorders.

Add a new specialized capture by defining ``REGISTRY_RECORDERS`` in your
``registry_*_gif.py`` module (stem → ``record_*_registry_gif``), then register
that module in ``_build_tables`` below. Avoid importing this module from
``registry_gif_lib`` at load time (circular imports); it is imported lazily from
``record_registry_gif`` / ``registry_gif_dispatch_bucket`` after the lib is ready.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

RegistryGifFn = Callable[..., tuple[Any, list]]

_MERGED: dict[str, RegistryGifFn] | None = None
_DISPATCH: dict[str, str] | None = None


def _extend(
    target: dict[str, RegistryGifFn],
    dispatch: dict[str, str],
    chunk: dict[str, RegistryGifFn],
    *,
    bucket: str | None,
) -> None:
    for stem, fn in chunk.items():
        if stem in target:
            raise ValueError(f"registry GIF duplicate stem {stem!r}")
        target[stem] = fn
        dispatch[stem] = bucket if bucket is not None else stem


def _build_tables() -> None:
    global _MERGED, _DISPATCH
    if _MERGED is not None:
        return

    merged: dict[str, RegistryGifFn] = {}
    dispatch: dict[str, str] = {}

    from registry_dl01_gif import DL01_REGISTRY_RECORDERS as dl01
    from registry_cs_pd_gif import REGISTRY_RECORDERS as cs_pd
    from registry_ex_gp_lo_gif import REGISTRY_RECORDERS as ex_gp_lo
    from registry_fw01_gif import REGISTRY_RECORDERS as fw01_reg
    from registry_kn01_gif import REGISTRY_RECORDERS as kn01_reg
    from registry_lw_rp_ml_sf_gif import REGISTRY_RECORDERS as lw_rp_ml_sf
    from registry_mc01_gif import REGISTRY_RECORDERS as mc01_reg
    from registry_mm_fe_gif import REGISTRY_RECORDERS as mm_fe
    from registry_mo_zq_hm_gif import REGISTRY_RECORDERS as mo_zq_hm
    from registry_ng01_gif import REGISTRY_RECORDERS as ng01_reg
    from registry_ph_bn_bi_gif import REGISTRY_RECORDERS as ph_bn_bi
    from registry_pk_ec_gif import REGISTRY_RECORDERS as pk_ec
    from registry_rk_jw_gif import REGISTRY_RECORDERS as rk_jw
    from registry_218_gif import REGISTRY_RECORDERS as batch218
    from registry_sg_cw_gif import REGISTRY_RECORDERS as sg_cw
    from registry_tk_sr_gif import REGISTRY_RECORDERS as tk_sr
    from registry_tw_rv_gif import REGISTRY_RECORDERS as tw_rv
    from registry_wl_ll_gif import REGISTRY_RECORDERS as wl_ll

    _extend(merged, dispatch, dl01, bucket="dl01")
    _extend(merged, dispatch, kn01_reg, bucket="kn01")
    _extend(merged, dispatch, mo_zq_hm, bucket=None)
    _extend(merged, dispatch, ng01_reg, bucket=None)
    _extend(merged, dispatch, ex_gp_lo, bucket=None)
    _extend(merged, dispatch, fw01_reg, bucket="fw01")
    _extend(merged, dispatch, lw_rp_ml_sf, bucket=None)
    _extend(merged, dispatch, mc01_reg, bucket="mc01")
    _extend(merged, dispatch, mm_fe, bucket=None)
    _extend(merged, dispatch, ph_bn_bi, bucket=None)
    _extend(merged, dispatch, cs_pd, bucket=None)
    _extend(merged, dispatch, tw_rv, bucket=None)
    _extend(merged, dispatch, tk_sr, bucket=None)
    _extend(merged, dispatch, batch218, bucket="batch218")
    _extend(merged, dispatch, sg_cw, bucket="sg_cw")
    _extend(merged, dispatch, rk_jw, bucket="rk_jw")
    _extend(merged, dispatch, pk_ec, bucket="pk_ec")
    _extend(merged, dispatch, wl_ll, bucket="wl_ll")

    _MERGED = merged
    _DISPATCH = dispatch


def lookup_external_recorder(game_id: str) -> RegistryGifFn | None:
    _build_tables()
    assert _MERGED is not None
    return _MERGED.get(game_id)


def external_dispatch_bucket(game_id: str) -> str | None:
    """Return audit bucket for stems handled by merged recorders, else ``None``."""
    _build_tables()
    assert _DISPATCH is not None
    return _DISPATCH.get(game_id)
