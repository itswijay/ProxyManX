"""Shared fixtures."""

import types

import pytest

from proxymanx import targets


@pytest.fixture(autouse=True)
def fake_windows(monkeypatch):
    """Replace the registry and the settings broadcast in every test.

    Without this, running the tests on Windows would overwrite the user's own
    proxy variables. It also lets registry logic be tested on Linux.
    """
    state = types.SimpleNamespace(registry={}, events=[], fail=False)

    def open_key(*args, **kwargs):
        if state.fail:
            raise OSError("registry not available")
        return object()

    def set_value(key, name, reserved, kind, value):
        state.registry[name] = value
        state.events.append(('write', name))

    def delete_value(key, name):
        if name not in state.registry:
            raise FileNotFoundError(name)
        del state.registry[name]
        state.events.append(('delete', name))

    monkeypatch.setattr(targets, 'winreg', types.SimpleNamespace(
        HKEY_CURRENT_USER=None, KEY_SET_VALUE=None, KEY_READ=None,
        REG_DWORD=None, REG_SZ=None,
        OpenKey=open_key, SetValueEx=set_value, DeleteValue=delete_value,
        CloseKey=lambda key: None,
    ))
    monkeypatch.setattr(targets, 'broadcast_environment_change',
                        lambda: state.events.append(('broadcast', state.registry.copy())))
    return state
