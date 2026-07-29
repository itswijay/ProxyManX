"""Tests for ConfigManager profile storage.

Every test points ConfigManager at a tmp_path so the real ~/.proxymanx is
never touched.
"""

import json

import pytest

from proxymanx.config import ConfigManager


@pytest.fixture
def manager(tmp_path):
    return ConfigManager(config_dir=tmp_path)


@pytest.fixture
def sample_config():
    return {
        'http_host': 'proxy.corp',
        'http_port': 8080,
        'https_host': 'proxy.corp',
        'https_port': 8080,
        'ftp_host': 'proxy.corp',
        'ftp_port': 8080,
        'use_auth': True,
        'username': 'alice',
        'password': 'sup3rs3cret',
        'no_proxy': 'localhost,127.0.0.1',
        'use_same': True,
    }


class TestSaveLoad:
    def test_roundtrip(self, manager, sample_config):
        assert manager.save_config('office', sample_config)

        loaded = manager.load_config('office')
        assert loaded['http_host'] == 'proxy.corp'
        assert loaded['username'] == 'alice'
        assert loaded['use_auth'] is True
        assert loaded['no_proxy'] == 'localhost,127.0.0.1'

    def test_ports_come_back_as_ints(self, manager, sample_config):
        manager.save_config('office', sample_config)
        loaded = manager.load_config('office')

        for key in ('http_port', 'https_port', 'ftp_port'):
            assert isinstance(loaded[key], int), key
            assert loaded[key] == 8080

    def test_password_is_never_written_to_disk(self, manager, sample_config, tmp_path):
        manager.save_config('office', sample_config)

        on_disk = (tmp_path / 'office.ini').read_text()
        assert 'sup3rs3cret' not in on_disk
        assert 'password' not in on_disk
        # ...but the rest of the profile is still there
        assert 'alice' in on_disk

    def test_loaded_password_is_empty(self, manager, sample_config):
        manager.save_config('office', sample_config)
        assert manager.load_config('office')['password'] == ''

    def test_legacy_profile_with_password_still_loads(self, manager, tmp_path):
        # Profiles written before 2.1.0 carry a password key
        (tmp_path / 'legacy.ini').write_text(
            "[proxy]\n"
            "http_host = proxy.corp\n"
            "http_port = 8080\n"
            "https_host = proxy.corp\n"
            "https_port = 8080\n"
            "ftp_host = proxy.corp\n"
            "ftp_port = 8080\n"
            "use_auth = True\n"
            "username = alice\n"
            "password = oldsecret\n"
            "no_proxy = localhost\n"
            "use_same = True\n"
        )

        loaded = manager.load_config('legacy')
        assert loaded['password'] == 'oldsecret'

    def test_load_missing_profile_returns_none(self, manager):
        assert manager.load_config('nope') is None

    def test_json_profile_is_read(self, manager, tmp_path):
        (tmp_path / 'fromjson.json').write_text(json.dumps({'http_host': 'j.corp', 'http_port': 1234}))
        assert manager.load_config('fromjson')['http_host'] == 'j.corp'


class TestListConfigs:
    def test_empty(self, manager):
        assert manager.list_configs() == []

    def test_lists_both_formats_sorted_and_deduped(self, manager, tmp_path, sample_config):
        manager.save_config('bbb', sample_config)
        manager.save_config('aaa', sample_config)
        (tmp_path / 'ccc.json').write_text('{}')
        # Same stem in both formats must appear once
        (tmp_path / 'aaa.json').write_text('{}')

        assert manager.list_configs() == ['aaa', 'bbb', 'ccc']

    def test_active_profile_state_file_is_not_a_profile(self, manager, sample_config):
        manager.save_config('office', sample_config)
        manager.set_active_profile('office')
        assert manager.list_configs() == ['office']


class TestDeleteConfig:
    def test_delete_ini(self, manager, sample_config):
        manager.save_config('office', sample_config)
        assert manager.delete_config('office')
        assert manager.list_configs() == []

    def test_delete_json(self, manager, tmp_path):
        # Regression: delete used to only unlink .ini, so json profiles were
        # listed but could never be removed.
        (tmp_path / 'fromjson.json').write_text('{}')
        assert manager.delete_config('fromjson')
        assert manager.list_configs() == []

    def test_delete_removes_both_formats(self, manager, tmp_path, sample_config):
        manager.save_config('office', sample_config)
        (tmp_path / 'office.json').write_text('{}')

        assert manager.delete_config('office')
        assert not (tmp_path / 'office.ini').exists()
        assert not (tmp_path / 'office.json').exists()

    def test_delete_missing_returns_false(self, manager):
        assert not manager.delete_config('nope')

    def test_delete_clears_active_profile(self, manager, sample_config):
        manager.save_config('office', sample_config)
        manager.set_active_profile('office')

        manager.delete_config('office')
        assert manager._read_active_profile() is None


class TestActiveProfile:
    def test_set_and_get(self, manager, sample_config):
        manager.save_config('office', sample_config)
        manager.set_active_profile('office')
        assert manager.get_active_profile() == 'office'

    def test_none_when_unset(self, manager):
        assert manager.get_active_profile() is None

    def test_clear(self, manager, sample_config):
        manager.save_config('office', sample_config)
        manager.set_active_profile('office')
        manager.clear_active_profile()
        assert manager.get_active_profile() is None

    def test_clear_is_idempotent(self, manager):
        manager.clear_active_profile()
        manager.clear_active_profile()

    def test_stale_pointer_self_heals(self, manager, tmp_path, sample_config):
        manager.save_config('office', sample_config)
        manager.set_active_profile('office')

        # Remove the profile behind ConfigManager's back
        (tmp_path / 'office.ini').unlink()

        assert manager.get_active_profile() is None
        assert not (tmp_path / '.active_profile').exists()


def test_config_dir_is_created(tmp_path):
    target = tmp_path / 'nested' / 'proxymanx'
    ConfigManager(config_dir=target)
    assert target.is_dir()
