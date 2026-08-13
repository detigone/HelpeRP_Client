"""Защита локальных секретов (Windows DPAPI)."""

from __future__ import annotations

import base64
import sys

_PREFIX = "dpapi:"


def _win_protect(data: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    blob_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out),
    ):
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _win_unprotect(data: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    blob_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out),
    ):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def protect_secret(plaintext: str) -> str:
    if not plaintext or sys.platform != "win32":
        return plaintext
    try:
        enc = _win_protect(plaintext.encode("utf-8"))
        return _PREFIX + base64.b64encode(enc).decode("ascii")
    except Exception:
        return plaintext


def unprotect_secret(stored: str) -> str:
    if not stored:
        return ""
    if not stored.startswith(_PREFIX):
        return stored
    if sys.platform != "win32":
        return ""
    try:
        raw = base64.b64decode(stored[len(_PREFIX):])
        return _win_unprotect(raw).decode("utf-8")
    except Exception:
        return ""
