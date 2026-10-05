"""SSRF protections and strict URL validation.

Rules:
* only http/https
* no userinfo (user:pass@host) in fetchable URLs
* only ports 80/443
* literal-IP hosts (including decimal/hex/octal forms accepted by inet_aton) are checked
* every resolved address must be globally routable (blocks loopback, private, link-local,
  CGNAT, multicast, reserved, cloud metadata 169.254.169.254, IPv4-mapped IPv6 of those)
* redirects are never followed automatically; each hop is re-validated
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import SplitResult, urlsplit

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
}
BLOCKED_SUFFIXES = (".local", ".localhost", ".internal", ".intranet", ".lan", ".home", ".corp", ".private")


class UnsafeURL(ValueError):
    """Raised when a URL must not be fetched."""


def ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if isinstance(ip, ipaddress.IPv6Address) and ip.sixtofour is not None:
        if ip_is_blocked(ip.sixtofour):
            return True
    return (
        not ip.is_global
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def literal_ip(host: str):
    """Return an ip object if `host` is any IP literal form, else None."""
    h = host.strip("[]")
    try:
        return ipaddress.ip_address(h)
    except ValueError:
        pass
    try:  # decimal / hex / octal / short forms such as 2130706433, 0x7f.1, 127.1
        return ipaddress.IPv4Address(socket.inet_aton(h))
    except (OSError, ValueError):
        return None


def validate_url_syntax(raw: str) -> SplitResult:
    if not isinstance(raw, str) or not raw.strip():
        raise UnsafeURL("empty url")
    raw = raw.strip()
    if len(raw) > 2048:
        raise UnsafeURL("url too long")
    if any(ord(c) < 33 or ord(c) == 127 for c in raw):
        raise UnsafeURL("control characters or whitespace in url")
    parts = urlsplit(raw)
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURL(f"scheme not allowed: {parts.scheme or '(none)'}")
    if not parts.hostname:
        raise UnsafeURL("missing host")
    if parts.username or parts.password:
        raise UnsafeURL("credentials in url are not allowed")
    try:
        port = parts.port
    except ValueError as e:
        raise UnsafeURL("invalid port") from e
    if port not in ALLOWED_PORTS:
        raise UnsafeURL(f"port not allowed: {port}")
    host = parts.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES or host.endswith(BLOCKED_SUFFIXES):
        raise UnsafeURL("hostname is blocked")
    ip = literal_ip(host)
    if ip is not None and ip_is_blocked(ip):
        raise UnsafeURL("ip address is not publicly routable")
    return parts


def resolve_public_addresses(host: str, port: int = 443) -> list[str]:
    """Resolve host and ensure EVERY address is public. Raises UnsafeURL otherwise."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise UnsafeURL("host did not resolve") from e
    addrs = sorted({i[4][0] for i in infos})
    if not addrs:
        raise UnsafeURL("host did not resolve")
    for a in addrs:
        if ip_is_blocked(ipaddress.ip_address(a)):
            raise UnsafeURL("host resolves to a non-public address")
    return addrs


def assert_safe_to_fetch(raw: str, resolve: bool = True) -> SplitResult:
    parts = validate_url_syntax(raw)
    if resolve:
        resolve_public_addresses(parts.hostname.lower(), parts.port or (80 if parts.scheme == "http" else 443))
    return parts
