"""Tests for proxy target handlers.

The registry is faked (see conftest.py). Real Windows behaviour is covered by
the "Windows end to end" CI job.
"""

import platform

import pytest

from proxymanx import targets
from proxymanx.targets import (
    PROXY_TARGETS,
    EnvironmentProxyTarget,
    NPMProxyTarget,
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

    def test_persistent_write_failure_is_tolerated(self, clean_env, sample_config, fake_windows):
        # set_proxy must still report overall success for the session vars.
        fake_windows.fail = True
        target = EnvironmentProxyTarget()
        assert target._set_persistent_env_vars({'HTTP_PROXY': 'http://x:1'}) is False
        assert target.set_proxy(sample_config) is True

    def test_set_broadcasts_after_writing(self, clean_env, sample_config, fake_windows):
        # Regression: the broadcast used to go out before the variables were
        # written, so new terminals did not see the proxy until sign-out.
        EnvironmentProxyTarget().set_proxy(sample_config)

        kind, registry_at_broadcast = fake_windows.events[-1]
        assert kind == 'broadcast'
        assert registry_at_broadcast['HTTP_PROXY'] == 'http://proxy.corp:8080'

    def test_unset_broadcasts_after_deleting(self, clean_env, sample_config, fake_windows, monkeypatch):
        target = EnvironmentProxyTarget()
        target.set_proxy(sample_config)
        monkeypatch.setattr(targets.platform, 'system', lambda: 'Windows')
        target.unset_proxy()

        assert fake_windows.events[-1] == ('broadcast', {})

    def test_no_proxy_is_translated(self, clean_env, sample_config, fake_windows):
        sample_config['no_proxy'] = 'localhost,*.local,10.*'
        EnvironmentProxyTarget().set_proxy(sample_config)

        assert fake_windows.registry['NO_PROXY'] == 'localhost,.local,10.0.0.0/8'


class TestSystemProxyTarget:
    def test_bypass_list_is_translated(self, sample_config, fake_windows, monkeypatch):
        monkeypatch.setattr(targets.platform, 'system', lambda: 'Windows')
        monkeypatch.setattr(SystemProxyTarget, '_refresh_system_settings', lambda self: None)
        sample_config['no_proxy'] = 'localhost,*.local,10.*'

        assert SystemProxyTarget().set_proxy(sample_config)
        assert fake_windows.registry['ProxyOverride'] == 'localhost;*.local;10.*'


class TestNPMProxyTarget:
    @pytest.fixture
    def npm(self, monkeypatch):
        """Record npm commands instead of running them."""
        calls, replies = [], {}

        def fake_run(cmd, *args, **kwargs):
            calls.append(cmd)
            return True, replies.get(cmd, ''), ''

        monkeypatch.setattr(targets, 'run_command', fake_run)
        return calls, replies

    def test_set_leaves_certificate_checking_alone(self, npm, sample_config):
        calls, _ = npm
        assert NPMProxyTarget().set_proxy(sample_config)
        assert not [c for c in calls if 'strict-ssl' in c and 'get' not in c.split()]

    def test_set_warns_when_certificate_checking_is_off(self, npm, sample_config, capsys):
        _, replies = npm
        replies['npm config get strict-ssl'] = 'false\n'
        NPMProxyTarget().set_proxy(sample_config)
        assert 'certificate checking is off' in capsys.readouterr().out

    def test_unset_restores_certificate_checking(self, npm):
        calls, _ = npm
        NPMProxyTarget().unset_proxy()
        assert 'npm config delete strict-ssl' in calls

    def test_strict_ssl_alone_is_not_an_active_proxy(self, npm):
        _, replies = npm
        replies.update({'npm config get proxy': 'null\n', 'npm config get https-proxy': 'null\n',
                        'npm config get strict-ssl': 'true\n'})
        assert NPMProxyTarget().list_proxy() is None


LEGACY_BLOCK = """
# ProxyManX Windows - Proxy Settings
$env:HTTP_PROXY = "http://proxy.corp:8080"
$env:HTTPS_PROXY = "http://proxy.corp:8080"
$env:NO_PROXY = "localhost"

# Set system proxy for PowerShell web requests
[System.Net.WebRequest]::DefaultWebProxy = New-Object System.Net.WebProxy("http://proxy.corp:8080")
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
"""

USER_BEFORE = "Set-Alias ll Get-ChildItem\n"
# Every one of these lines was deleted by the old cleanup
USER_AFTER = "# my own comment\n$env:EDITOR = 'code'\n\n[System.Net.WebRequest]::DefaultWebProxy\nSet-Alias g git\n"


class TestPowerShellProfile:
    @pytest.fixture
    def target(self, tmp_path, monkeypatch):
        monkeypatch.setattr(PowerShellProxyTarget, '_get_profile_path',
                            lambda self: tmp_path / 'WindowsPowerShell' / 'profile.ps1')
        target = PowerShellProxyTarget()
        target.profile_path.parent.mkdir()
        return target

    def write(self, target, text):
        target.profile_path.write_bytes(text.encode('utf-8'))

    def read(self, target):
        return target.profile_path.read_bytes().decode('utf-8').replace('\r\n', '\n')

    def test_unset_keeps_user_lines(self, target, sample_config):
        self.write(target, USER_BEFORE)
        assert target.set_proxy(sample_config)
        self.write(target, self.read(target) + USER_AFTER)

        assert target.unset_proxy()
        assert self.read(target) == USER_BEFORE + USER_AFTER

    def test_unset_keeps_user_lines_after_a_legacy_block(self, target):
        self.write(target, USER_BEFORE + LEGACY_BLOCK + USER_AFTER)
        assert target.unset_proxy()
        assert self.read(target) == USER_BEFORE + "\n" + USER_AFTER

    def test_unset_removes_legacy_and_current_blocks(self, target, sample_config):
        target.set_proxy(sample_config)
        self.write(target, LEGACY_BLOCK + USER_BEFORE + self.read(target))
        assert target.unset_proxy()
        assert self.read(target) == "\n" + USER_BEFORE

    def test_crlf_profiles(self, target):
        crlf = (USER_BEFORE + LEGACY_BLOCK + USER_AFTER).replace('\n', '\r\n')
        self.write(target, crlf)
        assert target.unset_proxy()
        assert target.profile_path.read_bytes().decode() == (USER_BEFORE + "\n" + USER_AFTER).replace('\n', '\r\n')

    def test_set_twice_leaves_one_block(self, target, sample_config):
        target.set_proxy(sample_config)
        once = self.read(target)
        target.set_proxy(sample_config)
        assert self.read(target) == once

    def test_profile_without_trailing_newline(self, target, sample_config):
        self.write(target, "Set-Alias g git")
        target.set_proxy(sample_config)
        assert self.read(target).startswith("Set-Alias g git\n# ProxyManX")
        target.unset_proxy()
        assert self.read(target) == "Set-Alias g git\n"

    def test_edited_block_is_left_alone(self, target, sample_config):
        edited = "# ProxyManX Windows - Proxy Settings\nWrite-Host 'mine'\n"
        self.write(target, edited)
        assert not target.unset_proxy()
        assert not target.set_proxy(sample_config)
        assert self.read(target) == edited

    def test_unreadable_profile_is_not_touched(self, target, sample_config):
        utf16 = "Set-Alias g git\n".encode('utf-16')
        target.profile_path.write_bytes(utf16)
        assert not target.set_proxy(sample_config)
        assert target.profile_path.read_bytes() == utf16

    def test_unset_without_a_profile(self, target):
        assert target.unset_proxy()
        assert not target.profile_path.exists()
