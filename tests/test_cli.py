"""Tests for the ProxyManX CLI orchestration layer."""

import pytest

from proxymanx.cli import ProxyManX

PROXY_ENV_VARS = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'NO_PROXY', 'no_proxy',
]


@pytest.fixture
def clean_env(monkeypatch):
    for var in PROXY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture
def manager(tmp_path, clean_env):
    """A ProxyManX whose profiles live in tmp_path, never the real home dir."""
    return ProxyManX(config_dir=tmp_path)


@pytest.fixture
def sample_config():
    return {
        'http_host': 'proxy.corp',
        'http_port': 8080,
        'https_host': 'proxy.corp',
        'https_port': 8080,
        'ftp_host': 'proxy.corp',
        'ftp_port': 8080,
        'use_auth': False,
        'username': '',
        'password': '',
        'no_proxy': 'localhost',
        'use_same': True,
    }


class TestReadLiveConfig:
    def test_returns_none_when_nothing_is_set(self, manager):
        assert manager._read_live_config() is None

    def test_builds_config_from_environment(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')
        clean_env.setenv('HTTPS_PROXY', 'http://proxy.corp:8080')
        clean_env.setenv('NO_PROXY', 'localhost,127.0.0.1')

        config = manager._read_live_config()

        assert config['http_host'] == 'proxy.corp'
        assert config['http_port'] == 8080
        assert config['https_host'] == 'proxy.corp'
        assert config['no_proxy'] == 'localhost,127.0.0.1'
        assert config['use_same'] is True
        assert config['use_auth'] is False

    def test_captures_username_but_never_the_password(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://alice:s3cret@proxy.corp:8080')

        config = manager._read_live_config()

        assert config['use_auth'] is True
        assert config['username'] == 'alice'
        assert config['password'] == ''

    def test_differing_https_marks_use_same_false(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')
        clean_env.setenv('HTTPS_PROXY', 'http://secure.corp:8443')

        config = manager._read_live_config()

        assert config['https_host'] == 'secure.corp'
        assert config['https_port'] == 8443
        assert config['use_same'] is False

    def test_https_defaults_to_http_when_absent(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')

        config = manager._read_live_config()

        assert config['https_host'] == 'proxy.corp'
        assert config['https_port'] == 8080

    def test_lowercase_env_vars_are_honoured(self, manager, clean_env):
        clean_env.setenv('http_proxy', 'http://lower.corp:3128')

        config = manager._read_live_config()

        assert config['http_host'] == 'lower.corp'
        assert config['http_port'] == 3128


class TestSaveCurrentConfig:
    def test_writes_a_real_profile(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')

        manager.save_current_config('fromlive')

        assert 'fromlive' in manager.config_manager.list_configs()
        assert manager.config_manager.load_config('fromlive')['http_host'] == 'proxy.corp'

    def test_marks_the_saved_profile_active(self, manager, clean_env):
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')

        manager.save_current_config('fromlive')

        assert manager.config_manager.get_active_profile() == 'fromlive'

    def test_password_does_not_reach_disk(self, manager, clean_env, tmp_path):
        clean_env.setenv('HTTP_PROXY', 'http://alice:s3cret@proxy.corp:8080')

        manager.save_current_config('fromlive')

        assert 's3cret' not in (tmp_path / 'fromlive.ini').read_text()

    def test_exits_nonzero_when_no_proxy_is_active(self, manager):
        with pytest.raises(SystemExit) as excinfo:
            manager.save_current_config('fromlive')

        assert excinfo.value.code == 1
        assert manager.config_manager.list_configs() == []


class TestDetectActiveProfile:
    def test_prefers_the_tracked_profile(self, manager, sample_config):
        manager.config_manager.save_config('office', sample_config)
        manager.config_manager.set_active_profile('office')

        assert manager._detect_active_profile() == 'office'

    def test_falls_back_to_matching_the_environment(self, manager, clean_env, sample_config):
        manager.config_manager.save_config('office', sample_config)
        # No tracked profile, but the environment matches the saved one
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')

        assert manager._detect_active_profile() == 'office'

    def test_fallback_records_what_it_found(self, manager, clean_env, sample_config):
        manager.config_manager.save_config('office', sample_config)
        clean_env.setenv('HTTP_PROXY', 'http://proxy.corp:8080')

        manager._detect_active_profile()

        assert manager.config_manager.get_active_profile() == 'office'

    def test_no_match_returns_none(self, manager, clean_env, sample_config):
        manager.config_manager.save_config('office', sample_config)
        clean_env.setenv('HTTP_PROXY', 'http://somewhere.else:9999')

        assert manager._detect_active_profile() is None

    def test_nothing_set_returns_none(self, manager):
        assert manager._detect_active_profile() is None
