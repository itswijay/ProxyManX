"""Tests for proxy target handlers.

Only the platform-independent targets are exercised. The system, PowerShell
and persistent-registry paths are Windows-only and are covered by the manual
Windows checklist instead.
"""

import platform

import pytest

from proxymanx.targets import (
    PROXY_TARGETS,
    EnvironmentProxyTarget,
    PowerShellProxyTarget,
    SystemProxyTarget,
    get_available_targets,
    get_target_descriptions,
)

ON_WINDOWS = platform.system() == "Windows"

PROXY_ENV_VARS = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'NO_PROXY', 'no_proxy',
]


@pytest.fixture
def clean_env(monkeypatch):
    """Isolate os.environ so tests never leak proxy vars into each other."""
    for var in PROXY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture
def sample_config():
    return {
        'http_host': 'proxy.corp',
        'http_port': 8080,
        'https_host': 'proxy.corp',
        'https_port': 8080,
        'use_auth': False,
        'username': '',
        'password': '',
        'no_proxy': 'localhost,127.0.0.1',
    }


class TestTargetRegistry:
    def test_descriptions_cover_every_target(self):
        assert set(get_target_descriptions()) == set(PROXY_TARGETS)

    def test_available_targets_are_a_subset_of_the_registry(self):
        assert set(get_available_targets()).issubset(set(PROXY_TARGETS))

    def test_available_targets_are_instances_not_classes(self):
        for name, target in get_available_targets().items():
            assert not isinstance(target, type), name


class TestWindowsOnlyAvailability:
    def test_system_target_gated_on_windows(self):
        assert SystemProxyTarget().is_available() is ON_WINDOWS

    def test_powershell_target_gated_on_windows(self):
        # Regression: is_available() used to return True unconditionally, so on
        # Linux the target went live and wrote into ~/Documents/WindowsPowerShell.
        assert PowerShellProxyTarget().is_available() is ON_WINDOWS

    @pytest.mark.skipif(ON_WINDOWS, reason="checks non-Windows exclusion")
    def test_windows_targets_absent_off_windows(self):
        available = get_available_targets()
        assert 'system' not in available
        assert 'powershell' not in available


class TestEnvironmentProxyTarget:
    def test_always_available(self):
        assert EnvironmentProxyTarget().is_available()

    def test_set_populates_both_cases(self, clean_env, sample_config):
        import os

        assert EnvironmentProxyTarget().set_proxy(sample_config)

        assert os.environ['HTTP_PROXY'] == 'http://proxy.corp:8080'
        assert os.environ['http_proxy'] == 'http://proxy.corp:8080'
        assert os.environ['HTTPS_PROXY'] == 'http://proxy.corp:8080'
        assert os.environ['NO_PROXY'] == 'localhost,127.0.0.1'

    def test_set_with_auth_embeds_credentials(self, clean_env, sample_config):
        import os

        sample_config.update(use_auth=True, username='alice', password='s3cret')
        EnvironmentProxyTarget().set_proxy(sample_config)

        assert os.environ['HTTP_PROXY'] == 'http://alice:s3cret@proxy.corp:8080'

    def test_list_reports_what_was_set(self, clean_env, sample_config):
        target = EnvironmentProxyTarget()
        target.set_proxy(sample_config)

        listed = target.list_proxy()
        assert listed['HTTP_PROXY'] == 'http://proxy.corp:8080'

    def test_list_returns_none_when_clean(self, clean_env):
        assert EnvironmentProxyTarget().list_proxy() is None

    def test_unset_clears_everything(self, clean_env, sample_config):
        import os

        target = EnvironmentProxyTarget()
        target.set_proxy(sample_config)
        assert target.unset_proxy()

        for var in PROXY_ENV_VARS:
            assert var not in os.environ
        assert target.list_proxy() is None

    def test_unset_on_clean_env_is_a_no_op(self, clean_env):
        assert EnvironmentProxyTarget().unset_proxy()

    @pytest.mark.skipif(ON_WINDOWS, reason="winreg is real on Windows")
    def test_persistent_write_fails_gracefully_off_windows(self, clean_env, sample_config):
        # _set_persistent_env_vars hits the MockWinreg stub and returns False;
        # set_proxy must still report overall success for the session vars.
        target = EnvironmentProxyTarget()
        assert target._set_persistent_env_vars({'HTTP_PROXY': 'http://x:1'}) is False
        assert target.set_proxy(sample_config) is True
