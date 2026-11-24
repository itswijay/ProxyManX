"""Tests for the platform-independent helpers in proxymanx.utils."""

import pytest

from proxymanx.utils import (
    DEFAULT_PROXY_PORT,
    format_proxy_url,
    get_default_no_proxy,
    parse_proxy_url,
    validate_proxy_config,
)


class TestFormatProxyUrl:
    def test_without_auth(self):
        assert format_proxy_url("proxy.corp", 8080) == "http://proxy.corp:8080"

    def test_with_auth(self):
        url = format_proxy_url("proxy.corp", 8080, "alice", "s3cret")
        assert url == "http://alice:s3cret@proxy.corp:8080"

    def test_username_without_password_is_ignored(self):
        # Both are required to produce a credentialed URL
        assert format_proxy_url("proxy.corp", 8080, "alice", "") == "http://proxy.corp:8080"

    def test_custom_protocol(self):
        url = format_proxy_url("proxy.corp", 3128, protocol="https")
        assert url == "https://proxy.corp:3128"


class TestParseProxyUrl:
    def test_with_scheme(self):
        parsed = parse_proxy_url("http://proxy.corp:8080")
        assert parsed == {
            "host": "proxy.corp",
            "port": 8080,
            "username": "",
            "password": "",
        }

    def test_without_scheme(self):
        # This is the form the Windows registry ProxyServer value takes
        parsed = parse_proxy_url("proxy.corp:3128")
        assert parsed["host"] == "proxy.corp"
        assert parsed["port"] == 3128

    def test_with_credentials(self):
        parsed = parse_proxy_url("http://alice:s3cret@proxy.corp:8080")
        assert parsed["username"] == "alice"
        assert parsed["password"] == "s3cret"
        assert parsed["host"] == "proxy.corp"
        assert parsed["port"] == 8080

    def test_password_containing_at_sign(self):
        # rsplit on '@' means the last one separates credentials from the host
        parsed = parse_proxy_url("http://alice:p@ss@proxy.corp:8080")
        assert parsed["username"] == "alice"
        assert parsed["password"] == "p@ss"
        assert parsed["host"] == "proxy.corp"

    def test_missing_port_uses_default(self):
        assert parse_proxy_url("http://proxy.corp")["port"] == DEFAULT_PROXY_PORT

    def test_trailing_slash_stripped(self):
        assert parse_proxy_url("http://proxy.corp:8080/")["host"] == "proxy.corp"

    @pytest.mark.parametrize("value", ["", "   ", None, "http://", "http://proxy.corp:notaport"])
    def test_unparseable_returns_none(self, value):
        assert parse_proxy_url(value) is None

    @pytest.mark.parametrize(
        "host,port,username,password",
        [
            ("proxy.corp", 8080, None, None),
            ("proxy.corp", 3128, "alice", "s3cret"),
            ("10.0.0.1", 80, None, None),
        ],
    )
    def test_roundtrip_against_format(self, host, port, username, password):
        parsed = parse_proxy_url(format_proxy_url(host, port, username, password))
        assert parsed["host"] == host
        assert parsed["port"] == port
        assert parsed["username"] == (username or "")
        assert parsed["password"] == (password or "")


class TestValidateProxyConfig:
    def test_minimal_valid_config(self):
        assert validate_proxy_config({"http_host": "proxy.corp", "http_port": 8080})

    @pytest.mark.parametrize("missing", ["http_host", "http_port"])
    def test_missing_required_field(self, missing):
        config = {"http_host": "proxy.corp", "http_port": 8080}
        del config[missing]
        assert not validate_proxy_config(config)

    def test_string_port_is_coerced_in_place(self):
        config = {"http_host": "proxy.corp", "http_port": "8080"}
        assert validate_proxy_config(config)
        assert config["http_port"] == 8080

    def test_non_numeric_port_rejected(self):
        assert not validate_proxy_config({"http_host": "proxy.corp", "http_port": "abc"})

    @pytest.mark.parametrize("port", [0, -1, 65536, 99999])
    def test_out_of_range_port_rejected(self, port):
        assert not validate_proxy_config({"http_host": "proxy.corp", "http_port": port})


def test_default_no_proxy_covers_loopback():
    no_proxy = get_default_no_proxy()
    assert "localhost" in no_proxy
    assert "127.0.0.1" in no_proxy
